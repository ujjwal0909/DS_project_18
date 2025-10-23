"""Implementation of 2PC and Raft nodes using the lightweight RPC layer."""
from __future__ import annotations

import random
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .rpc import RPCClient, RPCError, RPCServer, parse_target


TWOPC_VOTING_SERVICE = "VotingPhase"
TWOPC_DECISION_SERVICE = "DecisionPhase"
RAFT_SERVICE = "RaftService"


@dataclass
class LogEntry:
    index: int
    term: int
    command: str


@dataclass
class TransactionRecord:
    transaction_id: str
    payload: str
    decision: Optional[bool] = None


@dataclass
class NodeConfig:
    node_id: str
    host: str
    port: int
    peers: Dict[str, str]
    vote_commit: bool = True
    election_timeout_range: Tuple[float, float] = (1.5, 3.0)
    heartbeat_interval: float = 1.0

    @property
    def address(self) -> str:
        return f"{self.host}:{self.port}"


class ConsensusNode:
    def __init__(self, config: NodeConfig) -> None:
        self.config = config
        self._server = RPCServer(config.host, config.port)
        self._server.register(TWOPC_VOTING_SERVICE, "RequestVote", self._handle_vote_request)
        self._server.register(TWOPC_DECISION_SERVICE, "DeliverDecision", self._handle_decision)
        self._server.register(RAFT_SERVICE, "RequestVote", self._handle_raft_request_vote)
        self._server.register(RAFT_SERVICE, "AppendEntries", self._handle_append_entries)
        self._server.register(RAFT_SERVICE, "ClientCommand", self._handle_client_command)
        self._server.register(RAFT_SERVICE, "GetStatus", self._handle_get_status)
        self._server.register(RAFT_SERVICE, "Shutdown", self._handle_shutdown)

        self._twopc_transactions: Dict[str, TransactionRecord] = {}
        self._twopc_lock = threading.Lock()

        self._state_lock = threading.Lock()
        self._role: str = "follower"
        self._current_term: int = 0
        self._voted_for: Optional[str] = None
        self._log: List[LogEntry] = []
        self._commit_index: int = -1
        self._last_applied: int = -1
        self._applied_commands: List[str] = []
        self._kv_store: Dict[str, str] = {}
        self._leader_id: Optional[str] = None
        self._last_heartbeat: float = time.time()
        self._running = threading.Event()
        self._running.clear()

        self._bg_threads: List[threading.Thread] = []

    # ------------------------------------------------------------------
    # Lifecycle management
    # ------------------------------------------------------------------
    def start(self) -> None:
        self._server.start()
        self._running.set()
        election_thread = threading.Thread(target=self._run_election_timer, daemon=True)
        heartbeat_thread = threading.Thread(target=self._run_heartbeat_loop, daemon=True)
        self._bg_threads.extend([election_thread, heartbeat_thread])
        for thread in self._bg_threads:
            thread.start()

    def stop(self) -> None:
        self._running.clear()
        self._server.stop()

    def wait(self) -> None:
        for thread in self._bg_threads:
            if thread.is_alive():
                thread.join(timeout=0.5)

    # ------------------------------------------------------------------
    # 2PC coordinator utilities
    # ------------------------------------------------------------------
    def run_transaction(self, payload: str, participants: List[str]) -> bool:
        transaction_id = uuid.uuid4().hex
        votes: Dict[str, bool] = {}
        for participant_id in participants:
            target = self.config.peers.get(participant_id)
            if target is None and participant_id != self.config.node_id:
                raise ValueError(f"Unknown participant {participant_id}")
            if participant_id == self.config.node_id:
                target = self.config.address
            self._print_phase_client(
                "Voting", self.config.node_id, "RequestVote", participant_id, target
            )
            client = self._build_client(target)
            try:
                response = client.call(
                    TWOPC_VOTING_SERVICE,
                    "RequestVote",
                    {
                        "coordinator_id": self.config.node_id,
                        "participant_id": participant_id,
                        "transaction_id": transaction_id,
                        "payload": payload,
                    },
                )
            except Exception:
                votes[participant_id] = False
            else:
                votes[participant_id] = bool(response.get("commit", False))
        decision = all(votes.values())
        for participant_id in participants:
            target = self.config.peers.get(participant_id)
            if target is None and participant_id != self.config.node_id:
                continue
            if participant_id == self.config.node_id:
                target = self.config.address
            self._print_phase_client(
                "Decision", self.config.node_id, "DeliverDecision", participant_id, target
            )
            client = self._build_client(target)
            try:
                client.call(
                    TWOPC_DECISION_SERVICE,
                    "DeliverDecision",
                    {
                        "coordinator_id": self.config.node_id,
                        "participant_id": participant_id,
                        "transaction_id": transaction_id,
                        "commit": decision,
                        "payload": payload,
                    },
                )
            except Exception:
                continue
        return decision

    def _handle_vote_request(self, payload: Dict[str, str]) -> Dict[str, str]:
        participant_id = payload["participant_id"]
        self._print_phase_server("Voting", participant_id, "RequestVote", payload["coordinator_id"])
        vote = self.config.vote_commit
        record = TransactionRecord(
            transaction_id=payload["transaction_id"],
            payload=payload["payload"],
        )
        with self._twopc_lock:
            self._twopc_transactions[record.transaction_id] = record
        return {
            "participant_id": participant_id,
            "transaction_id": record.transaction_id,
            "commit": vote,
        }

    def _handle_decision(self, payload: Dict[str, str]) -> Dict[str, str]:
        participant_id = payload["participant_id"]
        self._print_phase_server("Decision", participant_id, "DeliverDecision", payload["coordinator_id"])
        with self._twopc_lock:
            record = self._twopc_transactions.get(payload["transaction_id"])
            if record:
                record.decision = payload["commit"]
        message = "committed" if payload["commit"] else "aborted"
        return {
            "participant_id": participant_id,
            "transaction_id": payload["transaction_id"],
            "committed": payload["commit"],
            "message": message,
        }

    def _print_phase_client(
        self, phase: str, source_id: str, rpc_name: str, target_id: str, target_address: str
    ) -> None:
        print(
            f"Phase {phase} of Node {source_id} sends RPC {rpc_name} to Phase {phase} "
            f"of Node {target_id} ({target_address})"
        )

    def _print_phase_server(self, phase: str, node_id: str, rpc_name: str, caller_id: str) -> None:
        print(
            f"Phase {phase} of Node {node_id} sends RPC {rpc_name} to Phase {phase} "
            f"of Node {caller_id}"
        )

    # ------------------------------------------------------------------
    # Raft handlers
    # ------------------------------------------------------------------
    def _handle_raft_request_vote(self, payload: Dict[str, str]) -> Dict[str, str]:
        candidate_id = payload["candidate_id"]
        term = int(payload["term"])
        self._print_node_server("RequestVote", candidate_id)
        with self._state_lock:
            if term < self._current_term:
                return {"vote_granted": False, "term": self._current_term}
            if term > self._current_term:
                self._current_term = term
                self._voted_for = None
                self._role = "follower"
            if self._voted_for in (None, candidate_id):
                self._voted_for = candidate_id
                self._last_heartbeat = time.time()
                return {"vote_granted": True, "term": self._current_term}
            return {"vote_granted": False, "term": self._current_term}

    def _handle_append_entries(self, payload: Dict[str, str]) -> Dict[str, str]:
        leader_id = payload["leader_id"]
        term = int(payload["term"])
        entries = payload.get("entries", [])
        commit_index = int(payload.get("commit_index", -1))
        self._print_node_server("AppendEntries", leader_id)
        with self._state_lock:
            if term < self._current_term:
                return {"success": False, "term": self._current_term}
            self._leader_id = leader_id
            self._role = "follower"
            self._current_term = term
            self._last_heartbeat = time.time()
            new_log: List[LogEntry] = []
            for entry in entries:
                new_log.append(
                    LogEntry(index=int(entry["index"]), term=int(entry["term"]), command=entry["command"])
                )
            if new_log:
                self._log = new_log
            self._commit_index = commit_index
        self._apply_entries()
        return {"success": True, "term": self._current_term}

    def _handle_client_command(self, payload: Dict[str, str]) -> Dict[str, str]:
        source_id = payload.get("source_id", "client")
        command = payload["command"]
        self._print_node_server("ClientCommand", source_id)
        with self._state_lock:
            if self._role != "leader":
                leader_id = self._leader_id
            else:
                leader_id = self.config.node_id
            if self._role == "leader":
                entry = LogEntry(index=len(self._log), term=self._current_term, command=command)
                self._log.append(entry)
        if leader_id != self.config.node_id:
            if not leader_id:
                return {"success": False, "leader_id": "", "message": "no_leader"}
            target_address = self.config.peers.get(leader_id)
            if leader_id == self.config.node_id or target_address is None:
                target_address = self.config.address
            self._print_node_client("ClientCommand", leader_id, target_address)
            client = self._build_client(target_address)
            try:
                response = client.call(
                    RAFT_SERVICE,
                    "ClientCommand",
                    {
                        "source_id": self.config.node_id,
                        "command": command,
                        "client_id": payload.get("client_id", "client"),
                        "request_id": payload.get("request_id", uuid.uuid4().hex),
                    },
                )
            except Exception as exc:
                return {
                    "success": False,
                    "leader_id": leader_id,
                    "message": f"forward_failed:{exc}",
                }
            return response
        committed = self._replicate_log()
        if committed:
            result = self._apply_entries()
            return {"success": True, "leader_id": self.config.node_id, "result": result, "message": "committed"}
        return {"success": False, "leader_id": self.config.node_id, "message": "failed_to_commit"}

    def _handle_get_status(self, payload: Dict[str, str]) -> Dict[str, str]:
        requester_id = payload.get("requester_id", "client")
        self._print_node_server("GetStatus", requester_id)
        with self._state_lock:
            return {
                "node_id": self.config.node_id,
                "role": self._role,
                "term": self._current_term,
                "commit_index": self._commit_index,
                "applied_commands": list(self._applied_commands),
                "leader_id": self._leader_id or "",
            }

    def _handle_shutdown(self, payload: Dict[str, str]) -> Dict[str, str]:
        requester_id = payload.get("requester_id", "client")
        self._print_node_server("Shutdown", requester_id)
        self.stop()
        return {"stopping": True}

    def _print_node_client(self, rpc_name: str, target_id: str, target_address: str) -> None:
        print(
            f"Node {self.config.node_id} sends RPC {rpc_name} to Node {target_id} "
            f"({target_address})"
        )

    def _print_node_server(self, rpc_name: str, caller_id: str) -> None:
        print(f"Node {self.config.node_id} runs RPC {rpc_name} called by Node {caller_id}")

    # ------------------------------------------------------------------
    # Raft background tasks
    # ------------------------------------------------------------------
    def _run_election_timer(self) -> None:
        while not self._running.is_set():
            time.sleep(0.1)
        while self._running.is_set():
            timeout = random.uniform(*self.config.election_timeout_range)
            triggered = False
            while self._running.is_set():
                time.sleep(0.05)
                with self._state_lock:
                    elapsed = time.time() - self._last_heartbeat
                if elapsed >= timeout:
                    triggered = True
                    break
            if not triggered:
                continue
            with self._state_lock:
                if time.time() - self._last_heartbeat < timeout:
                    continue
                self._role = "candidate"
                self._current_term += 1
                self._voted_for = self.config.node_id
                self._last_heartbeat = time.time()
                term = self._current_term
            votes = 1
            for peer_id, target in self.config.peers.items():
                if peer_id == self.config.node_id:
                    continue
                self._print_node_client("RequestVote", peer_id, target)
                client = self._build_client(target)
                try:
                    response = client.call(
                        RAFT_SERVICE,
                        "RequestVote",
                        {
                            "candidate_id": self.config.node_id,
                            "term": term,
                            "last_log_index": len(self._log) - 1,
                            "last_log_term": self._log[-1].term if self._log else 0,
                        },
                    )
                except Exception:
                    continue
                if response.get("vote_granted"):
                    votes += 1
            if votes >= self._majority():
                with self._state_lock:
                    self._role = "leader"
                    self._leader_id = self.config.node_id
                    self._last_heartbeat = time.time()
            else:
                with self._state_lock:
                    self._role = "follower"

    def _run_heartbeat_loop(self) -> None:
        while not self._running.is_set():
            time.sleep(0.1)
        while self._running.is_set():
            time.sleep(self.config.heartbeat_interval)
            with self._state_lock:
                if self._role != "leader":
                    continue
                term = self._current_term
                entries = [entry.__dict__ for entry in self._log]
                commit_index = self._commit_index
            for peer_id, target in self.config.peers.items():
                if peer_id == self.config.node_id:
                    continue
                self._print_node_client("AppendEntries", peer_id, target)
                client = self._build_client(target)
                try:
                    client.call(
                        RAFT_SERVICE,
                        "AppendEntries",
                        {
                            "leader_id": self.config.node_id,
                            "term": term,
                            "entries": entries,
                            "commit_index": commit_index,
                        },
                    )
                except Exception:
                    continue

    def _replicate_log(self) -> bool:
        with self._state_lock:
            term = self._current_term
            entries = [entry.__dict__ for entry in self._log]
        success_count = 1
        for peer_id, target in self.config.peers.items():
            if peer_id == self.config.node_id:
                continue
            self._print_node_client("AppendEntries", peer_id, target)
            client = self._build_client(target)
            try:
                response = client.call(
                    RAFT_SERVICE,
                    "AppendEntries",
                    {
                        "leader_id": self.config.node_id,
                        "term": term,
                        "entries": entries,
                        "commit_index": len(entries) - 1,
                    },
                )
            except Exception:
                continue
            if response.get("success"):
                success_count += 1
        if success_count >= self._majority():
            with self._state_lock:
                self._commit_index = len(entries) - 1
            return True
        return False

    def _apply_entries(self) -> str:
        applied_result = ""
        while True:
            with self._state_lock:
                if self._commit_index <= self._last_applied:
                    break
                self._last_applied += 1
                entry = self._log[self._last_applied]
            result = self._execute_command(entry.command)
            applied_result = result or applied_result
        return applied_result

    def _execute_command(self, command: str) -> str:
        parts = command.strip().split()
        if not parts:
            return ""
        op = parts[0].lower()
        if op == "set" and len(parts) == 3:
            key, value = parts[1:]
            self._kv_store[key] = value
            self._applied_commands.append(command)
            return value
        if op == "increment" and len(parts) == 2:
            key = parts[1]
            current = int(self._kv_store.get(key, "0"))
            current += 1
            self._kv_store[key] = str(current)
            self._applied_commands.append(command)
            return str(current)
        if op == "get" and len(parts) == 2:
            key = parts[1]
            value = self._kv_store.get(key, "")
            self._applied_commands.append(command)
            return value
        self._applied_commands.append(command)
        return ""

    def _build_client(self, target: str) -> RPCClient:
        host, port = parse_target(target)
        return RPCClient(host, port)

    def _majority(self) -> int:
        total = len(self.config.peers) + 1  # include self
        return total // 2 + 1


def create_node(node_id: str, address: str, peers: Dict[str, str], vote_commit: bool = True) -> ConsensusNode:
    host, port = parse_target(address)
    config = NodeConfig(
        node_id=node_id,
        host=host,
        port=port,
        peers=peers,
        vote_commit=vote_commit,
    )
    return ConsensusNode(config)
