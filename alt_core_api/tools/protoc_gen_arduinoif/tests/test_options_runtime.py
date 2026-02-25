# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path

import pytest

from protoc_gen_arduinoif.options_runtime import get_arduino_opts_pb2


def test_get_arduino_opts_pb2_requires_env(monkeypatch: pytest.MonkeyPatch) -> None:
    get_arduino_opts_pb2.cache_clear()
    monkeypatch.delenv("PROTOC_GEN_ARDUINOIF_PB2", raising=False)

    with pytest.raises(RuntimeError, match="PROTOC_GEN_ARDUINOIF_PB2 is not set"):
        get_arduino_opts_pb2()


def test_get_arduino_opts_pb2_loads_from_env(
    monkeypatch: pytest.MonkeyPatch,
    test_pb2_path: Path,
) -> None:
    get_arduino_opts_pb2.cache_clear()
    monkeypatch.setenv("PROTOC_GEN_ARDUINOIF_PB2", str(test_pb2_path))

    module = get_arduino_opts_pb2()
    assert hasattr(module, "cpp_name")
