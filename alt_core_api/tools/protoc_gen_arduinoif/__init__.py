# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Dict, List, NamedTuple, Tuple

from google.protobuf.descriptor_pb2 import EnumDescriptorProto

FIELD_CPP_TYPE_TAG = 50001
FIELD_CPP_NAME_TAG = 50002
METHOD_CPP_NAME_TAG = 50101
METHOD_CPP_RETURN_TAG = 50102
METHOD_CPP_ARG_TYPES_TAG = 50104
METHOD_SOURCE_VIRTUAL_TAG = 50111
METHOD_EMIT_API_TAG = 50112
METHOD_EMIT_SERVICE_TAG = 50113
METHOD_VISIBILITY_TAG = 50114
SERVICE_GENERATE_API_CLASS_TAG = 50201
SERVICE_GENERATE_SERVICE_CLASS_TAG = 50202
SERVICE_GENERATE_SERVICE_IMPL_CLASS_TAG = 50203
SERVICE_IFC_CLASS_NAME_TAG = 50211
SERVICE_API_CLASS_NAME_TAG = 50212
SERVICE_SERVICE_CLASS_NAME_TAG = 50213
SERVICE_SERVICE_IMPL_CLASS_NAME_TAG = 50214
SERVICE_API_MEMBER_NAME_TAG = 50215
SERVICE_BASE_SERVICES_TAG = 50216
SERVICE_IFC_HEADER_NAME_TAG = 50217
SERVICE_EXTRA_INCLUDES_TAG = 50218

ServiceDescriptor = Tuple[object, str]
ServiceIndex = Dict[str, ServiceDescriptor]


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


class ServicePlan(NamedTuple):
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

    @classmethod
    def build(
        cls,
        service,
        package_name: str,
        proto_enums: List[EnumDescriptorProto],
        context,
    ) -> "ServicePlan":
        from .service_codegen import build_service_plan

        return build_service_plan(service, package_name, proto_enums, context)


from .core import main
from .request_context import RequestContext, build_request_context, full_service_name
from .service_codegen import build_service_plan, render_service_headers

__all__ = [
    "FIELD_CPP_TYPE_TAG",
    "FIELD_CPP_NAME_TAG",
    "METHOD_CPP_NAME_TAG",
    "METHOD_CPP_RETURN_TAG",
    "METHOD_CPP_ARG_TYPES_TAG",
    "METHOD_SOURCE_VIRTUAL_TAG",
    "METHOD_EMIT_API_TAG",
    "METHOD_EMIT_SERVICE_TAG",
    "METHOD_VISIBILITY_TAG",
    "SERVICE_GENERATE_API_CLASS_TAG",
    "SERVICE_GENERATE_SERVICE_CLASS_TAG",
    "SERVICE_GENERATE_SERVICE_IMPL_CLASS_TAG",
    "SERVICE_IFC_CLASS_NAME_TAG",
    "SERVICE_API_CLASS_NAME_TAG",
    "SERVICE_SERVICE_CLASS_NAME_TAG",
    "SERVICE_SERVICE_IMPL_CLASS_NAME_TAG",
    "SERVICE_API_MEMBER_NAME_TAG",
    "SERVICE_BASE_SERVICES_TAG",
    "SERVICE_IFC_HEADER_NAME_TAG",
    "SERVICE_EXTRA_INCLUDES_TAG",
    "ServiceDescriptor",
    "ServiceIndex",
    "main",
    "MethodSpec",
    "PlannedMethod",
    "ServicePlan",
    "RequestContext",
    "build_request_context",
    "full_service_name",
    "build_service_plan",
    "render_service_headers",
]
