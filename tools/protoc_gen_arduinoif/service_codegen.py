# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Dict, List

from google.protobuf.descriptor_pb2 import DescriptorProto, EnumDescriptorProto

from .constants import (
    SERVICE_API_CLASS_NAME_TAG,
    SERVICE_API_MEMBER_NAME_TAG,
    SERVICE_GENERATE_API_CLASS_TAG,
    SERVICE_GENERATE_SERVICE_CLASS_TAG,
    SERVICE_GENERATE_SERVICE_IMPL_CLASS_TAG,
    SERVICE_IFC_CLASS_NAME_TAG,
    SERVICE_SERVICE_IMPL_CLASS_NAME_TAG,
    ServiceIndex,
)
from .descriptors import (
    collect_lineage_includes,
    collect_service_lineage,
    cpp_namespace_from_package,
    dedupe_ordered,
    ifc_class_name,
    service_class_name,
    service_header_name,
    service_header_stem,
)
from .header_render import (
    render_api_header_content,
    render_ifc_header_content,
    render_service_header_content,
    render_service_impl_header_content,
)
from .method_specs import collect_lineage_methods, method_spec_from_descriptor
from .wire_options import get_bool_option, get_string_option


def generate_service_headers(
    service,
    service_full_name: str,
    service_index: ServiceIndex,
    lineage_cache: Dict[str, List[str]],
    message_map: Dict[str, DescriptorProto],
    package_name: str,
    proto_enums: List[EnumDescriptorProto],
) -> Dict[str, str]:
    ifc_name = (
        get_string_option(service.options, SERVICE_IFC_CLASS_NAME_TAG).strip()
        or f"{service.name}Interface"
    )
    api_name = (
        get_string_option(service.options, SERVICE_API_CLASS_NAME_TAG).strip()
        or f"{service.name}Api"
    )
    service_name = service_class_name(service)
    service_impl_name = (
        get_string_option(service.options, SERVICE_SERVICE_IMPL_CLASS_NAME_TAG).strip()
        or f"{service.name}ServiceImpl"
    )
    api_member_name = (
        get_string_option(service.options, SERVICE_API_MEMBER_NAME_TAG).strip()
        or "api_"
    )
    generate_api = get_bool_option(service.options, SERVICE_GENERATE_API_CLASS_TAG, False)
    generate_service = get_bool_option(
        service.options, SERVICE_GENERATE_SERVICE_CLASS_TAG, False
    )
    generate_service_impl = get_bool_option(
        service.options, SERVICE_GENERATE_SERVICE_IMPL_CLASS_TAG, False
    )

    if generate_service_impl and not generate_service:
        raise ValueError(
            f"{service.name}: generate_service_impl_class=true requires generate_service_class=true"
        )

    namespace_name = cpp_namespace_from_package(package_name)
    own_method_specs = [
        method_spec_from_descriptor(method, message_map) for method in service.method
    ]
    lineage = collect_service_lineage(service_full_name, service_index, lineage_cache)
    ancestor_services = lineage[:-1]
    lineage_method_specs = collect_lineage_methods(lineage, service_index, message_map)
    ifc_methods = [spec for spec in own_method_specs if spec.source_virtual]
    api_methods = [
        spec for spec in lineage_method_specs if spec.emit_api and spec.source_virtual
    ]
    service_methods = [spec for spec in lineage_method_specs if spec.emit_service]
    service_impl_methods = service_methods

    if generate_api:
        invalid_api_methods = [
            spec.decl
            for spec in lineage_method_specs
            if spec.emit_api and not spec.source_virtual
        ]
        if invalid_api_methods:
            joined = ", ".join(invalid_api_methods)
            raise ValueError(
                f"{service.name}: generate_api_class=true cannot emit non-virtual-source methods in API ({joined})"
            )

    if generate_service_impl and generate_api:
        api_callable = {spec.call_name for spec in api_methods}
        missing_api = [
            spec.decl for spec in service_methods if spec.call_name not in api_callable
        ]
        if missing_api:
            joined = ", ".join(missing_api)
            raise ValueError(
                f"{service.name}: service impl delegates API, but API does not expose ({joined})"
            )
        service_impl_methods = [
            spec for spec in service_methods if spec.call_name in api_callable
        ]

    include_list = dedupe_ordered(collect_lineage_includes(lineage, service_index))
    service_base_ifc_class_names: List[str] = []
    service_base_ifc_header_names: List[str] = []
    for ancestor_full_name in ancestor_services:
        ancestor_service, _ = service_index[ancestor_full_name]
        service_base_ifc_class_names.append(ifc_class_name(ancestor_service))
        service_base_ifc_header_names.append(service_header_name(ancestor_service))
    service_base_ifc_class_names = dedupe_ordered(service_base_ifc_class_names)
    service_base_ifc_header_names = dedupe_ordered(service_base_ifc_header_names)

    stem = service_header_stem(service)
    ifc_header = service_header_name(service)
    api_header = f"{stem}_api.hpp"
    service_header = f"{stem}_service.hpp"
    service_impl_header = f"{stem}_service_impl.hpp"

    outputs: Dict[str, str] = {}
    outputs[ifc_header] = render_ifc_header_content(
        include_list,
        namespace_name,
        proto_enums,
        ifc_name,
        ifc_methods,
    )

    if generate_api:
        outputs[api_header] = render_api_header_content(
            [ifc_header, *include_list],
            namespace_name,
            api_name,
            ifc_name,
            api_methods,
        )

    if generate_service:
        service_includes = dedupe_ordered([*service_base_ifc_header_names, *include_list])
        if proto_enums:
            service_includes = dedupe_ordered([ifc_header, *service_includes])
        outputs[service_header] = render_service_header_content(
            service_includes,
            namespace_name,
            service_name,
            service_base_ifc_class_names,
            service_methods,
        )

    if generate_service_impl:
        service_impl_includes = [service_header, *include_list]
        if generate_api:
            service_impl_includes.insert(1, api_header)
        outputs[service_impl_header] = render_service_impl_header_content(
            service_impl_includes,
            namespace_name,
            service_impl_name,
            service_name,
            api_name,
            api_member_name,
            service_impl_methods,
            generate_api,
        )

    return outputs
