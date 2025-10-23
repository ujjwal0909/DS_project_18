"""Command line entry point to start a consensus node."""
from __future__ import annotations

import argparse
import json
import signal
import sys
import threading
from typing import Dict

from consensus.node import ConsensusNode, NodeConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a consensus node")
    parser.add_argument("node_id", help="Identifier of the node")
    parser.add_argument("host", help="Host interface to bind to")
    parser.add_argument("port", type=int, help="Port to bind to")
    parser.add_argument(
        "--peers",
        type=str,
        default="{}",
        help="JSON mapping of peer_id -> address",
    )
    parser.add_argument(
        "--vote-abort",
        action="store_true",
        help="Force the node to vote abort during 2PC",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        peers: Dict[str, str] = json.loads(args.peers)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid peers JSON: {exc}")
    config = NodeConfig(
        node_id=args.node_id,
        host=args.host,
        port=args.port,
        peers=peers,
        vote_commit=not args.vote_abort,
    )
    node = ConsensusNode(config)
    node.start()

    stop_event = threading.Event()

    def handle_signal(signum, frame):  # type: ignore[unused-ignore]
        stop_event.set()
        node.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, handle_signal)

    try:
        while not stop_event.is_set():
            stop_event.wait(0.5)
    finally:
        node.stop()
        node.wait()


if __name__ == "__main__":
    main()
