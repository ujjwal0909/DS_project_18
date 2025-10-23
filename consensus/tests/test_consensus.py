from __future__ import annotations

import time
from typing import Dict, List

import pytest

from consensus.node import ConsensusNode, NodeConfig
from consensus.rpc import RPCClient, parse_target


_PORT_COUNTER = 5600


def next_base_port(step: int = 20) -> int:
    global _PORT_COUNTER
    base = _PORT_COUNTER
    _PORT_COUNTER += step
    return base


class Cluster:
    def __init__(self, node_ids: List[str], base_port: int = 5600) -> None:
        self.node_ids = node_ids
        self.base_port = base_port
        self.nodes: Dict[str, ConsensusNode] = {}
        self.addresses: Dict[str, str] = {}

    def start(self, abort_nodes: List[str] | None = None) -> None:
        abort_nodes = abort_nodes or []
        self.addresses = {}
        for index, node_id in enumerate(self.node_ids):
            port = self.base_port + index
            address = f"127.0.0.1:{port}"
            self.addresses[node_id] = address
        for index, node_id in enumerate(self.node_ids):
            peers = {
                other_id: self.addresses[other_id]
                for other_id in self.node_ids
                if other_id != node_id
            }
            config = NodeConfig(
                node_id=node_id,
                host="127.0.0.1",
                port=self.base_port + index,
                peers=peers,
                vote_commit=node_id not in abort_nodes,
            )
            node = ConsensusNode(config)
            node.start()
            self.nodes[node_id] = node
        time.sleep(0.5)

    def stop(self) -> None:
        for node in self.nodes.values():
            node.stop()
            node.wait()
        self.nodes.clear()
        self.addresses.clear()
        time.sleep(0.2)

    def run_transaction(self, coordinator: str, payload: str, participants: List[str]) -> bool:
        return self.nodes[coordinator].run_transaction(payload, participants)

    def client(self, node_id: str) -> RPCClient:
        address = self.addresses[node_id]
        host, port = parse_target(address)
        return RPCClient(host, port)

    def send_command(self, node_id: str, command: str) -> Dict[str, str]:
        client = self.client(node_id)
        last_response: Dict[str, str] = {"success": False}
        for _ in range(5):
            try:
                response = client.call(
                    "RaftService",
                    "ClientCommand",
                    {
                        "source_id": "test-client",
                        "command": command,
                        "client_id": "pytest",
                        "request_id": command,
                    },
                )
            except Exception:
                time.sleep(0.3)
                continue
            last_response = response
            if response.get("success"):
                return response
            if "no_leader" in response.get("message", ""):
                time.sleep(0.3)
                continue
            if response.get("message", "").startswith("forward_failed"):
                time.sleep(0.3)
                continue
            break
        return last_response

    def get_status(self, node_id: str) -> Dict[str, str]:
        client = self.client(node_id)
        return client.call(
            "RaftService",
            "GetStatus",
            {"requester_id": "pytest"},
        )

    def await_leader(self, timeout: float = 6.0) -> str:
        deadline = time.time() + timeout
        while time.time() < deadline:
            for node_id in self.node_ids:
                if node_id not in self.nodes:
                    continue
                try:
                    status = self.get_status(node_id)
                except Exception:
                    continue
                if status["role"] == "leader":
                    return node_id
            time.sleep(0.2)
        raise AssertionError("No leader elected")


@pytest.fixture
def cluster() -> Cluster:
    cluster = Cluster(["n1", "n2", "n3", "n4", "n5"], base_port=next_base_port())
    cluster.start()
    yield cluster
    cluster.stop()


def test_leader_election(cluster: Cluster) -> None:
    leader = cluster.await_leader()
    assert leader in cluster.node_ids


def test_command_replication(cluster: Cluster) -> None:
    leader = cluster.await_leader()
    follower = next(node for node in cluster.node_ids if node != leader)
    response = cluster.send_command(follower, "set temperature 42")
    assert response["success"]
    time.sleep(0.5)
    for node_id in cluster.node_ids:
        status = cluster.get_status(node_id)
        assert "set temperature 42" in status["applied_commands"]


def test_leader_failover(cluster: Cluster) -> None:
    leader = cluster.await_leader()
    cluster.send_command(leader, "set failover 1")
    cluster.nodes[leader].stop()
    cluster.nodes[leader].wait()
    del cluster.nodes[leader]
    cluster.node_ids.remove(leader)
    new_leader = cluster.await_leader()
    response = cluster.send_command(new_leader, "set recovered 2")
    assert response["success"]


def test_new_node_join() -> None:
    cluster = Cluster(["n1", "n2", "n3"], base_port=next_base_port())
    cluster.start()
    leader = cluster.await_leader()
    cluster.send_command(leader, "set baseline 1")
    new_id = "n4"
    new_port = cluster.base_port + len(cluster.node_ids)
    new_address = f"127.0.0.1:{new_port}"
    for node in cluster.nodes.values():
        node.config.peers[new_id] = new_address
    peers = {
        node_id: address for node_id, address in cluster.addresses.items()
    }
    config = NodeConfig(
        node_id=new_id,
        host="127.0.0.1",
        port=new_port,
        peers=peers,
    )
    new_node = ConsensusNode(config)
    new_node.start()
    cluster.nodes[new_id] = new_node
    cluster.node_ids.append(new_id)
    cluster.addresses[new_id] = new_address
    time.sleep(1.5)
    status = cluster.get_status(new_id)
    assert "set baseline 1" in status["applied_commands"]
    cluster.stop()


def test_two_phase_commit_abort() -> None:
    cluster = Cluster(["c1", "p1", "p2"], base_port=next_base_port())
    cluster.start(abort_nodes=["p2"])
    decision = cluster.run_transaction("c1", "update", ["c1", "p1", "p2"])
    assert decision is False
    cluster.stop()


def test_forwarding_to_leader(cluster: Cluster) -> None:
    leader = cluster.await_leader()
    follower = next(node for node in cluster.node_ids if node != leader)
    response = cluster.send_command(follower, "increment counter")
    assert response["success"]
