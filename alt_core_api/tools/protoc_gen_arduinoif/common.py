# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import importlib.util
import os
import types
from functools import lru_cache
from pathlib import Path
from typing import List, NamedTuple

from google.protobuf.descriptor_pb2 import EnumDescriptorProto

__all__ = [
    "full_service_name",
    "get_arduino_opts_pb2",
    "MethodSpec",
    "PlannedMethod",
    "ServiceModel",
]


def full_service_name(package_name: str, service_name: str) -> str:
    if package_name:
        return f".{package_name}.{service_name}"
    return f".{service_name}"


class MethodSpec(NamedTuple):
    decl: str
    call_name: str
    arg_names: List[str]
    returns_void: bool
    source_virtual: bool
    emit_api: bool
    emit_service: bool
    visibility: str


class PlannedMethod(NamedTuple):
    spec: MethodSpec
    in_ifc: bool
    in_api: bool
    in_service: bool
    in_service_impl: bool


class ServiceModel(NamedTuple):
    include_list: List[str]
    api_includes: List[str]
    service_includes: List[str]
    service_impl_includes: List[str]
    namespace_name: str
    proto_enums: List[EnumDescriptorProto]
    ifc_name: str
    api_name: str
    service_name: str
    service_impl_name: str
    api_member_name: str
    service_base_ifc_class_names: List[str]
    ifc_header: str
    api_header: str
    service_header: str
    service_impl_header: str
    methods: List[PlannedMethod]
    generate_api: bool
    generate_service: bool
    generate_service_impl: bool


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

    return _load_module_from_path(source_path, "_protoc_gen_arduinoif_arduino_opts_pb2")
