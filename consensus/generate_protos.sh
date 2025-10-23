#!/usr/bin/env bash
set -euo pipefail
OUTPUT_DIR="$(dirname "$0")/generated"
PROTO_DIR="$(dirname "$0")/proto"
python3 -m grpc_tools.protoc \
  --proto_path="$PROTO_DIR" \
  --python_out="$OUTPUT_DIR" \
  --grpc_python_out="$OUTPUT_DIR" \
  "$PROTO_DIR"/twopc.proto \
  "$PROTO_DIR"/raft.proto
