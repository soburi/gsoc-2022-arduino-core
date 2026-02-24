# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Dict, Iterator, List, NamedTuple, Optional, Tuple

from google.protobuf.descriptor_pb2 import EnumDescriptorProto

from .constants import (
    SERVICE_BASE_SERVICES_TAG,
    SERVICE_API_CLASS_NAME_TAG,
    SERVICE_API_MEMBER_NAME_TAG,
    SERVICE_EXTRA_INCLUDES_TAG,
    SERVICE_GENERATE_API_CLASS_TAG,
    SERVICE_GENERATE_SERVICE_CLASS_TAG,
    SERVICE_GENERATE_SERVICE_IMPL_CLASS_TAG,
    SERVICE_IFC_HEADER_NAME_TAG,
    SERVICE_IFC_CLASS_NAME_TAG,
    SERVICE_SERVICE_CLASS_NAME_TAG,
    SERVICE_SERVICE_IMPL_CLASS_NAME_TAG,
    ServiceIndex,
)
from .header_render import (
    render_api_header_content,
    render_ifc_header_content,
    render_service_header_content,
    render_service_impl_header_content,
)
from .method_specs import collect_lineage_methods
from .model import PlannedMethod, ServicePlan
from .request_context import RequestContext, full_service_name
from .wire_options import get_bool_option, get_string_list_option, get_string_option

__all__ = [
    "build_service_plan",
    "render_service_headers",
]


def _dedupe_ordered(items: List[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _resolve_service_reference(
    reference: str,
    current_package: str,
    service_index: ServiceIndex,
) -> str:
    if reference.startswith("."):
        candidate = reference
    elif "." in reference:
        candidate = f".{reference}"
    elif current_package:
        candidate = f".{current_package}.{reference}"
    else:
        candidate = f".{reference}"

    if candidate in service_index:
        return candidate

    raise ValueError(
        f"service '{candidate}' not found for base_services entry '{reference}'"
    )


def _collect_service_lineage(
    service_full_name: str,
    service_index: ServiceIndex,
    lineage_cache: Dict[str, List[str]],
    visiting: Optional[List[str]] = None,
) -> List[str]:
    if service_full_name in lineage_cache:
        return lineage_cache[service_full_name]
    if visiting is None:
        visiting = []
    if service_full_name in visiting:
        cycle = " -> ".join([*visiting, service_full_name])
        raise ValueError(f"cyclic service inheritance detected: {cycle}")

    entry = service_index.get(service_full_name)
    if entry is None:
        raise ValueError(f"service '{service_full_name}' not found")
    service, package_name = entry
    base_refs = get_string_list_option(service.options, SERVICE_BASE_SERVICES_TAG)

    inherited: List[str] = []
    for base_ref in base_refs:
        base_full_name = _resolve_service_reference(
            base_ref, package_name, service_index
        )
        inherited.extend(
            _collect_service_lineage(
                base_full_name,
                service_index,
                lineage_cache,
                [*visiting, service_full_name],
            )
        )
    inherited.append(service_full_name)
    lineage = _dedupe_ordered(inherited)
    lineage_cache[service_full_name] = lineage
    return lineage


def _collect_lineage_includes(
    lineage: List[str],
    service_index: ServiceIndex,
) -> List[str]:
    includes: List[str] = []
    for service_full_name in lineage:
        service, _ = service_index[service_full_name]
        includes.extend(
            get_string_list_option(service.options, SERVICE_EXTRA_INCLUDES_TAG)
        )
    return _dedupe_ordered(includes)


def _service_class_name(service) -> str:
    return (
        get_string_option(service.options, SERVICE_SERVICE_CLASS_NAME_TAG).strip()
        or f"{service.name}Service"
    )


def _ifc_class_name(service) -> str:
    return (
        get_string_option(service.options, SERVICE_IFC_CLASS_NAME_TAG).strip()
        or f"{service.name}Interface"
    )


def _service_header_name(service) -> str:
    header_name = get_string_option(
        service.options, SERVICE_IFC_HEADER_NAME_TAG
    ).strip()
    if header_name:
        return header_name
    return f"{_snake_case(service.name)}_interface.hpp"


def _service_header_stem(service) -> str:
    ifc_header = _service_header_name(service)
    suffix = "_interface.hpp"
    if ifc_header.endswith(suffix):
        return ifc_header[: -len(suffix)]
    return PurePosixPath(ifc_header).stem


def _cpp_namespace_from_package(package_name: str) -> str:
    return "::".join(part for part in package_name.split(".") if part)


def _snake_case(name: str) -> str:
    chars: List[str] = []
    for index, char in enumerate(name):
        if char.isupper() and index > 0 and (
            not name[index - 1].isupper()
            or (index + 1 < len(name) and name[index + 1].islower())
        ):
            chars.append("_")
        chars.append(char.lower())
    return "".join(chars)


class _ResolvedServiceOptions(NamedTuple):
    ifc_name: str
    api_name: str
    service_name: str
    service_impl_name: str
    api_member_name: str
    generate_api: bool
    generate_service: bool
    generate_service_impl: bool


class _ServicePlanBuilder:
    def __init__(
        self,
        service,
        package_name: str,
        proto_enums: List[EnumDescriptorProto],
        context: RequestContext,
    ) -> None:
        self._service = service
        self._package_name = package_name
        self._proto_enums = proto_enums
        self._context = context
        self._service_full_name = full_service_name(package_name, service.name)

    def build(self) -> ServicePlan:
        options = self._resolve_options()
        self._validate_generation_flags(options)

        own_method_specs = collect_lineage_methods(
            [self._service_full_name],
            self._context.service_index,
            self._context.message_map,
        )
        lineage = _collect_service_lineage(
            self._service_full_name,
            self._context.service_index,
            self._context.lineage_cache,
        )
        ancestor_services = lineage[:-1]
        lineage_method_specs = collect_lineage_methods(
            lineage, self._context.service_index, self._context.message_map
        )
        own_virtual_decls = {
            spec.decl for spec in own_method_specs if spec.source_virtual
        }
        api_callable = {
            spec.call_name
            for spec in lineage_method_specs
            if spec.emit_api and spec.source_virtual
        }
        service_callable = {
            spec.call_name for spec in lineage_method_specs if spec.emit_service
        }

        self._validate_api_methods(options, lineage_method_specs)
        self._validate_service_impl_api_delegate(
            options, lineage_method_specs, api_callable
        )

        service_impl_callable = (
            api_callable
            if (options.generate_service_impl and options.generate_api)
            else service_callable
        )

        methods = self._build_planned_methods(
            lineage_method_specs,
            own_virtual_decls,
            service_impl_callable,
        )

        include_list = _dedupe_ordered(
            _collect_lineage_includes(lineage, self._context.service_index)
        )
        service_base_ifc_class_names: List[str] = []
        service_base_ifc_header_names: List[str] = []
        for ancestor_full_name in ancestor_services:
            ancestor_service, _ = self._context.service_index[ancestor_full_name]
            service_base_ifc_class_names.append(_ifc_class_name(ancestor_service))
            service_base_ifc_header_names.append(_service_header_name(ancestor_service))
        service_base_ifc_class_names = _dedupe_ordered(service_base_ifc_class_names)
        service_base_ifc_header_names = _dedupe_ordered(service_base_ifc_header_names)

        stem = _service_header_stem(self._service)
        ifc_header = _service_header_name(self._service)
        api_header = f"{stem}_api.hpp"
        service_header = f"{stem}_service.hpp"
        service_impl_header = f"{stem}_service_impl.hpp"

        api_includes = [ifc_header, *include_list]

        service_includes: List[str] = []
        if options.generate_service:
            service_includes = _dedupe_ordered(
                [*service_base_ifc_header_names, *include_list]
            )
            if self._proto_enums:
                service_includes = _dedupe_ordered([ifc_header, *service_includes])

        service_impl_includes: List[str] = []
        if options.generate_service_impl:
            service_impl_includes = [service_header, *include_list]
            if options.generate_api:
                service_impl_includes.insert(1, api_header)

        return ServicePlan(
            include_list=include_list,
            api_includes=api_includes,
            service_includes=service_includes,
            service_impl_includes=service_impl_includes,
            namespace_name=_cpp_namespace_from_package(self._package_name),
            proto_enums=self._proto_enums,
            ifc_name=options.ifc_name,
            api_name=options.api_name,
            service_name=options.service_name,
            service_impl_name=options.service_impl_name,
            api_member_name=options.api_member_name,
            service_base_ifc_class_names=service_base_ifc_class_names,
            ifc_header=ifc_header,
            api_header=api_header,
            service_header=service_header,
            service_impl_header=service_impl_header,
            methods=methods,
            generate_api=options.generate_api,
            generate_service=options.generate_service,
            generate_service_impl=options.generate_service_impl,
        )

    def _resolve_options(self) -> _ResolvedServiceOptions:
        ifc_name = (
            get_string_option(self._service.options, SERVICE_IFC_CLASS_NAME_TAG).strip()
            or f"{self._service.name}Interface"
        )
        api_name = (
            get_string_option(self._service.options, SERVICE_API_CLASS_NAME_TAG).strip()
            or f"{self._service.name}Api"
        )
        service_impl_name = (
            get_string_option(
                self._service.options, SERVICE_SERVICE_IMPL_CLASS_NAME_TAG
            ).strip()
            or f"{self._service.name}ServiceImpl"
        )
        api_member_name = (
            get_string_option(self._service.options, SERVICE_API_MEMBER_NAME_TAG).strip()
            or "api_"
        )

        return _ResolvedServiceOptions(
            ifc_name=ifc_name,
            api_name=api_name,
            service_name=_service_class_name(self._service),
            service_impl_name=service_impl_name,
            api_member_name=api_member_name,
            generate_api=get_bool_option(
                self._service.options, SERVICE_GENERATE_API_CLASS_TAG, False
            ),
            generate_service=get_bool_option(
                self._service.options, SERVICE_GENERATE_SERVICE_CLASS_TAG, False
            ),
            generate_service_impl=get_bool_option(
                self._service.options, SERVICE_GENERATE_SERVICE_IMPL_CLASS_TAG, False
            ),
        )

    def _validate_generation_flags(self, options: _ResolvedServiceOptions) -> None:
        if options.generate_service_impl and not options.generate_service:
            raise ValueError(
                f"{self._service.name}: generate_service_impl_class=true requires generate_service_class=true"
            )

    def _validate_api_methods(
        self, options: _ResolvedServiceOptions, lineage_method_specs
    ) -> None:
        if not options.generate_api:
            return
        invalid_api_methods = [
            spec.decl
            for spec in lineage_method_specs
            if spec.emit_api and not spec.source_virtual
        ]
        if invalid_api_methods:
            joined = ", ".join(invalid_api_methods)
            raise ValueError(
                f"{self._service.name}: generate_api_class=true cannot emit non-virtual-source methods in API ({joined})"
            )

    def _validate_service_impl_api_delegate(
        self,
        options: _ResolvedServiceOptions,
        lineage_method_specs,
        api_callable,
    ) -> None:
        if not (options.generate_service_impl and options.generate_api):
            return
        missing_api = [
            spec.decl
            for spec in lineage_method_specs
            if spec.emit_service and spec.call_name not in api_callable
        ]
        if missing_api:
            joined = ", ".join(missing_api)
            raise ValueError(
                f"{self._service.name}: service impl delegates API, but API does not expose ({joined})"
            )

    @staticmethod
    def _build_planned_methods(
        lineage_method_specs,
        own_virtual_decls,
        service_impl_callable,
    ) -> List[PlannedMethod]:
        methods: List[PlannedMethod] = []
        for spec in lineage_method_specs:
            in_ifc = spec.decl in own_virtual_decls
            in_service = spec.emit_service
            methods.append(
                PlannedMethod(
                    spec=spec,
                    in_ifc=in_ifc,
                    in_api=spec.emit_api and spec.source_virtual,
                    in_service=in_service,
                    in_service_impl=in_service and spec.call_name in service_impl_callable,
                )
            )
        return methods


def build_service_plan(
    service,
    package_name: str,
    proto_enums: List[EnumDescriptorProto],
    context: RequestContext,
) -> ServicePlan:
    return _ServicePlanBuilder(
        service,
        package_name,
        proto_enums,
        context,
    ).build()


def render_service_headers(plan: ServicePlan) -> Iterator[Tuple[str, str]]:
    yield (
        plan.ifc_header,
        render_ifc_header_content(plan),
    )

    if plan.generate_api:
        yield (
            plan.api_header,
            render_api_header_content(plan),
        )

    if plan.generate_service:
        yield (
            plan.service_header,
            render_service_header_content(plan),
        )

    if plan.generate_service_impl:
        yield (
            plan.service_impl_header,
            render_service_impl_header_content(plan),
        )
