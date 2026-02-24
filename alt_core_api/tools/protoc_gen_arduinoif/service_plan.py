# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Dict, Iterator, List, NamedTuple, Tuple

from google.protobuf.descriptor_pb2 import DescriptorProto
from google.protobuf.descriptor_pb2 import EnumDescriptorProto

__all__ = [
    "MethodSpec",
    "PlannedMethod",
    "ServicePlan",
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
        from .service_codegen import _ServicePlanBuilder

        return _ServicePlanBuilder(
            service,
            package_name,
            proto_enums,
            context,
        ).build()

    @classmethod
    def collect_lineage_methods(
        cls,
        lineage: List[str],
        service_index,
        message_map: Dict[str, DescriptorProto],
    ) -> List[MethodSpec]:
        from .service_codegen import _MethodSpecFactory

        return _MethodSpecFactory.collect_lineage_methods(
            lineage,
            service_index,
            message_map,
        )

    def iter_rendered_headers(self) -> Iterator[Tuple[str, str]]:
        from .service_codegen import _RenderedHeaderStream

        yield from _RenderedHeaderStream(self).iter_files()
