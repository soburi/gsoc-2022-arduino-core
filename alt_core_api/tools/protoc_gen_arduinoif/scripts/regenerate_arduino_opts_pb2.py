#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path


def _patch_runtime_guard(pb2_path: Path) -> None:
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


def main() -> int:
    root_dir = Path(__file__).resolve().parents[4]
    proto_dir = root_dir / "alt_core_api" / "idl" / "proto"
    out_dir = Path(
        os.environ.get(
            "PROTOC_GEN_ARDUINOIF_PB2_OUT_DIR",
            str(
                root_dir
                / "alt_core_api"
                / "tools"
                / "protoc_gen_arduinoif"
                / "generated"
            ),
        )
    )
    grpc_proto_dir = (
        Path("/home/crs/zephyrproject/.venv/lib/python3.12/site-packages/grpc_tools/_proto")
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    pb2_path = out_dir / "arduino_opts_pb2.py"

    cmd = [
        "/home/crs/zephyrproject/.venv/bin/python",
        "-m",
        "grpc_tools.protoc",
        f"-I{proto_dir}",
        f"-I{grpc_proto_dir}",
        f"--python_out={out_dir}",
        str(proto_dir / "arduino_opts.proto"),
    ]
    subprocess.run(cmd, check=True, cwd=root_dir)
    _patch_runtime_guard(pb2_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
