# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import importlib.util
import os
import types
from functools import lru_cache
from pathlib import Path

__all__ = [
    "get_arduino_opts_pb2",
]


def _load_module_from_path(source_path: Path, module_name: str) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, source_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load arduino_opts_pb2 from '{source_path}'")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def get_arduino_opts_pb2() -> types.ModuleType:
    pb2_path = os.environ.get("PROTOC_GEN_ARDUINOIF_PB2")
    if not pb2_path:
        raise RuntimeError("PROTOC_GEN_ARDUINOIF_PB2 is not set")

    source_path = Path(pb2_path)
    if not source_path.exists():
        raise RuntimeError(
            f"PROTOC_GEN_ARDUINOIF_PB2 points to missing file: '{source_path}'"
        )

    module_name = "_protoc_gen_arduinoif_arduino_opts_pb2"
    return _load_module_from_path(source_path, module_name)
