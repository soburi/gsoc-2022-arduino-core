# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import types
from functools import lru_cache
from pathlib import Path

__all__ = [
    "get_arduino_opts_pb2",
]


def _patch_runtime_guard(pb2_path: Path) -> None:
    import re

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


def _generate_pb2_to_temp() -> Path:
    import subprocess
    import tempfile

    proto_dir = Path(__file__).resolve().parents[2] / "idl" / "proto"
    proto_file = proto_dir / "arduino_opts.proto"
    cache_dir = Path(tempfile.gettempdir()) / "protoc_gen_arduinoif_pb2"
    cache_dir.mkdir(parents=True, exist_ok=True)
    pb2_path = cache_dir / "arduino_opts_pb2.py"

    should_generate = True
    if pb2_path.exists():
        should_generate = pb2_path.stat().st_mtime < proto_file.stat().st_mtime

    if should_generate:
        subprocess.run(
            [
                "protoc",
                f"--proto_path={proto_dir}",
                f"--python_out={cache_dir}",
                str(proto_file),
            ],
            check=True,
        )
        _patch_runtime_guard(pb2_path)

    return pb2_path


def _load_module_from_path(source_path: Path, module_name: str) -> types.ModuleType:
    import importlib.util

    spec = importlib.util.spec_from_file_location(module_name, source_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load arduino_opts_pb2 from '{source_path}'")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def get_arduino_opts_pb2() -> types.ModuleType:
    import os

    pb2_path = os.environ.get("PROTOC_GEN_ARDUINOIF_PB2")
    if pb2_path and Path(pb2_path).exists():
        source_path = Path(pb2_path)
        module_name = "_protoc_gen_arduinoif_arduino_opts_pb2"
    else:
        source_path = _generate_pb2_to_temp()
        module_name = "_protoc_gen_arduinoif_arduino_opts_pb2_generated"
    return _load_module_from_path(source_path, module_name)
