#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "${ROOT_DIR}"

VENV_PYTHON="/home/crs/zephyrproject/.venv/bin/python"
PROTO_DIR="alt_core_api/idl/proto"
OUT_DIR="${PROTOC_GEN_ARDUINOIF_PB2_OUT_DIR:-alt_core_api/tools/protoc_gen_arduinoif/generated}"
GRPC_PROTO_DIR="/home/crs/zephyrproject/.venv/lib/python3.12/site-packages/grpc_tools/_proto"
PB2_PATH="${OUT_DIR}/arduino_opts_pb2.py"

mkdir -p "${OUT_DIR}"

"${VENV_PYTHON}" -m grpc_tools.protoc \
  -I"${PROTO_DIR}" \
  -I"${GRPC_PROTO_DIR}" \
  --python_out="${OUT_DIR}" \
  "${PROTO_DIR}/arduino_opts.proto"

PROTOC_GEN_ARDUINOIF_PB2_PATCH_TARGET="${PB2_PATH}" "${VENV_PYTHON}" - <<'PY'
import re
from pathlib import Path
import os

pb2_path = Path(os.environ["PROTOC_GEN_ARDUINOIF_PB2_PATCH_TARGET"])
text = pb2_path.read_text(encoding="utf-8")

import_line = "from google.protobuf import runtime_version as _runtime_version\n"
import_guard = (
    "try:\n"
    "  from google.protobuf import runtime_version as _runtime_version\n"
    "except ImportError:\n"
    "  _runtime_version = None\n"
)
if import_line in text and import_guard not in text:
    text = text.replace(import_line, import_guard)

pattern = re.compile(
    r"_runtime_version\.ValidateProtobufRuntimeVersion\(\n"
    r"(?P<body>(?:\s+.*\n)+?)"
    r"\)\n"
)
match = pattern.search(text)
if match and "if _runtime_version is not None:" not in text:
    body = "".join(f"  {line}" for line in match.group("body").splitlines(True))
    wrapped = (
        "if _runtime_version is not None:\n"
        "  _runtime_version.ValidateProtobufRuntimeVersion(\n"
        f"{body}"
        "  )\n"
    )
    text = text[: match.start()] + wrapped + text[match.end() :]

pb2_path.write_text(text, encoding="utf-8")
PY
