# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
PROTO_DIR = REPO_ROOT / "idl/proto"
PROTO_FILE = PROTO_DIR / "arduino_opts.proto"
PB2_OUTPUT_DIR = Path(tempfile.gettempdir()) / "protoc_gen_arduinoif_pytest"
PB2_FILE = PB2_OUTPUT_DIR / "arduino_opts_pb2.py"


def _ensure_pb2() -> Path:
    PB2_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if PB2_FILE.exists() and PB2_FILE.stat().st_mtime >= PROTO_FILE.stat().st_mtime:
        return PB2_FILE

    subprocess.run(
        [
            "protoc",
            f"--python_out={PB2_OUTPUT_DIR}",
            f"--proto_path={PROTO_DIR}",
            str(PROTO_FILE),
        ],
        cwd=REPO_ROOT,
        check=True,
    )
    return PB2_FILE


TEST_PB2_PATH = _ensure_pb2()
os.environ["PROTOC_GEN_ARDUINOIF_PB2"] = str(TEST_PB2_PATH)


@pytest.fixture(scope="session")
def test_pb2_path() -> Path:
    return TEST_PB2_PATH
