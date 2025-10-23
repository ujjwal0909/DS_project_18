"""A lightweight RPC framework used to simulate gRPC interactions.

The implementation intentionally mirrors the client/server flow of gRPC but is
implemented with the Python standard library to avoid external dependencies in
this execution environment. Messages are encoded as JSON objects and delimited
by newlines. The protocol is synchronous and request/response based.
"""
from __future__ import annotations

import json
import socket
import threading
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Tuple


Payload = Dict[str, Any]


class RPCError(Exception):
    """Raised when the RPC layer encounters an unrecoverable error."""


@dataclass
class RPCRequest:
    service: str
    method: str
    payload: Payload

    def to_bytes(self) -> bytes:
        return json.dumps(
            {"service": self.service, "method": self.method, "payload": self.payload}
        ).encode("utf-8") + b"\n"


@dataclass
class RPCResponse:
    payload: Payload

    @classmethod
    def from_bytes(cls, data: bytes) -> "RPCResponse":
        try:
            parsed = json.loads(data.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise RPCError("Invalid RPC response payload") from exc
        if not isinstance(parsed, dict) or "payload" not in parsed:
            raise RPCError("Malformed RPC response structure")
        return cls(payload=parsed["payload"])

    def to_bytes(self) -> bytes:
        return json.dumps({"payload": self.payload}).encode("utf-8") + b"\n"


class RPCServer:
    """Simple TCP based RPC server."""

    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port
        self._handlers: Dict[Tuple[str, str], Callable[[Payload], Payload]] = {}
        self._server_socket: Optional[socket.socket] = None
        self._serve_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    @property
    def address(self) -> Tuple[str, int]:
        return self._host, self._port

    def register(self, service: str, method: str, handler: Callable[[Payload], Payload]) -> None:
        self._handlers[(service, method)] = handler

    def start(self) -> None:
        if self._server_socket is not None:
            raise RuntimeError("Server already running")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self._host, self._port))
        sock.listen()
        self._server_socket = sock
        self._serve_thread = threading.Thread(target=self._serve_forever, daemon=True)
        self._serve_thread.start()

    def _serve_forever(self) -> None:
        assert self._server_socket is not None
        while not self._stop_event.is_set():
            try:
                self._server_socket.settimeout(0.5)
                client, _ = self._server_socket.accept()
            except socket.timeout:
                continue
            threading.Thread(target=self._handle_client, args=(client,), daemon=True).start()

    def _handle_client(self, client: socket.socket) -> None:
        with client:
            buffer = b""
            while not self._stop_event.is_set():
                try:
                    chunk = client.recv(4096)
                except OSError:
                    return
                if not chunk:
                    return
                buffer += chunk
                while b"\n" in buffer:
                    raw, buffer = buffer.split(b"\n", 1)
                    if not raw:
                        continue
                    try:
                        request_dict = json.loads(raw.decode("utf-8"))
                        service = request_dict["service"]
                        method = request_dict["method"]
                        payload = request_dict["payload"]
                    except (json.JSONDecodeError, KeyError) as exc:
                        response = RPCResponse(payload={"error": str(exc)}).to_bytes()
                        client.sendall(response)
                        continue
                    handler = self._handlers.get((service, method))
                    if handler is None:
                        response = RPCResponse(payload={"error": "method_not_found"}).to_bytes()
                        client.sendall(response)
                        continue
                    try:
                        result = handler(payload)
                    except Exception as exc:  # pragma: no cover - defensive
                        response = RPCResponse(payload={"error": str(exc)}).to_bytes()
                        client.sendall(response)
                        continue
                    response = RPCResponse(payload=result).to_bytes()
                    try:
                        client.sendall(response)
                    except OSError:
                        return

    def stop(self) -> None:
        self._stop_event.set()
        if self._server_socket:
            try:
                self._server_socket.close()
            except OSError:
                pass
        if self._serve_thread and self._serve_thread.is_alive():
            self._serve_thread.join(timeout=1.0)


class RPCClient:
    """Synchronous RPC client."""

    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port

    def call(self, service: str, method: str, payload: Payload, timeout: float = 5.0) -> Payload:
        request = RPCRequest(service=service, method=method, payload=payload)
        try:
            with socket.create_connection((self._host, self._port), timeout=timeout) as sock:
                sock.settimeout(timeout)
                sock.sendall(request.to_bytes())
                data = b""
                while not data.endswith(b"\n"):
                    chunk = sock.recv(4096)
                    if not chunk:
                        raise RPCError("Connection closed before response")
                    data += chunk
        except (OSError, TimeoutError) as exc:
            raise RPCError(str(exc)) from exc
        response = RPCResponse.from_bytes(data.strip())
        if "error" in response.payload:
            raise RPCError(response.payload["error"])
        return response.payload


def parse_target(target: str) -> Tuple[str, int]:
    host, port_str = target.split(":", 1)
    return host, int(port_str)
