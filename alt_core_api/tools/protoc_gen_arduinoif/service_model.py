# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import List, NamedTuple

from google.protobuf.descriptor_pb2 import EnumDescriptorProto

__all__ = [
    "MethodSpec",
    "PlannedMethod",
    "ServiceModel",
]


class MethodSpec(NamedTuple):
    decl: str
    call_name: str
    arg_names: List[str]
    suffix: str
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
