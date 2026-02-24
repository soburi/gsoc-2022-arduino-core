# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Dict, Iterator, List, NamedTuple, Optional, Tuple

from google.protobuf.descriptor_pb2 import (
    DescriptorProto,
    EnumDescriptorProto,
    FieldDescriptorProto,
)

from . import (
    FIELD_CPP_NAME_TAG,
    FIELD_CPP_TYPE_TAG,
    METHOD_CPP_ARG_TYPES_TAG,
    METHOD_CPP_NAME_TAG,
    METHOD_CPP_RETURN_TAG,
    METHOD_EMIT_API_TAG,
    METHOD_EMIT_SERVICE_TAG,
    METHOD_SOURCE_VIRTUAL_TAG,
    METHOD_VISIBILITY_TAG,
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
from .request_context import RequestContext, full_service_name
from .service_plan import MethodSpec, PlannedMethod, ServicePlan

__all__ = [
    "build_service_plan",
    "collect_lineage_methods",
    "render_service_headers",
]

ParsedFields = Dict[int, List[Tuple[int, object]]]
_OPTIONS_PARSE_CACHE: Dict[int, Tuple[bytes, ParsedFields]] = {}
_OPTIONS_PARSE_CACHE_LIMIT = 1024


def _dedupe_ordered(items: List[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _read_varint(data: bytes, index: int) -> Tuple[int, int]:
    value = 0
    shift = 0
    while True:
        if index >= len(data):
            raise ValueError("unexpected end of varint")
        byte = data[index]
        index += 1
        value |= (byte & 0x7F) << shift
        if not (byte & 0x80):
            return value, index
        shift += 7
        if shift > 63:
            raise ValueError("varint is too large")


def _parse_wire_fields(data: bytes) -> ParsedFields:
    parsed: ParsedFields = {}
    index = 0

    while index < len(data):
        key, index = _read_varint(data, index)
        field_number = key >> 3
        wire_type = key & 0x7

        if wire_type == 0:
            value, index = _read_varint(data, index)
        elif wire_type == 1:
            if index + 8 > len(data):
                raise ValueError("invalid fixed64 field")
            value = data[index : index + 8]
            index += 8
        elif wire_type == 2:
            length, index = _read_varint(data, index)
            if index + length > len(data):
                raise ValueError("invalid length-delimited field")
            value = data[index : index + length]
            index += length
        elif wire_type == 5:
            if index + 4 > len(data):
                raise ValueError("invalid fixed32 field")
            value = data[index : index + 4]
            index += 4
        else:
            raise ValueError(f"unsupported wire type {wire_type}")

        parsed.setdefault(field_number, []).append((wire_type, value))

    return parsed


def _parsed_fields_from_options(options) -> ParsedFields:
    raw = options.SerializeToString()
    if not raw:
        return {}

    cache_key = id(options)
    cached = _OPTIONS_PARSE_CACHE.get(cache_key)
    if cached is not None and cached[0] == raw:
        return cached[1]

    try:
        fields = _parse_wire_fields(raw)
    except ValueError:
        return {}

    if len(_OPTIONS_PARSE_CACHE) > _OPTIONS_PARSE_CACHE_LIMIT:
        _OPTIONS_PARSE_CACHE.clear()
    _OPTIONS_PARSE_CACHE[cache_key] = (raw, fields)
    return fields


def get_string_option(options, field_number: int) -> str:
    fields = _parsed_fields_from_options(options)
    if not fields:
        return ""

    for wire_type, value in fields.get(field_number, []):
        if wire_type == 2:
            try:
                return bytes(value).decode("utf-8")
            except UnicodeDecodeError:
                return ""
    return ""


def get_bool_option(options, field_number: int, default: bool = False) -> bool:
    fields = _parsed_fields_from_options(options)
    if not fields:
        return default

    for wire_type, value in fields.get(field_number, []):
        if wire_type == 0:
            return bool(value)
    return default


def get_string_list_option(options, field_number: int) -> List[str]:
    fields = _parsed_fields_from_options(options)
    if not fields:
        return []

    values: List[str] = []
    for wire_type, value in fields.get(field_number, []):
        if wire_type != 2:
            continue
        try:
            text = bytes(value).decode("utf-8").strip()
        except UnicodeDecodeError:
            continue
        if text:
            values.append(text)
    return values


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


def _field_type(field: FieldDescriptorProto) -> str:
    default_types = {
        FieldDescriptorProto.TYPE_BOOL: "bool",
        FieldDescriptorProto.TYPE_INT32: "int32_t",
        FieldDescriptorProto.TYPE_INT64: "int64_t",
        FieldDescriptorProto.TYPE_UINT32: "uint32_t",
        FieldDescriptorProto.TYPE_UINT64: "uint64_t",
        FieldDescriptorProto.TYPE_SINT32: "int32_t",
        FieldDescriptorProto.TYPE_SINT64: "int64_t",
        FieldDescriptorProto.TYPE_FIXED32: "uint32_t",
        FieldDescriptorProto.TYPE_FIXED64: "uint64_t",
        FieldDescriptorProto.TYPE_SFIXED32: "int32_t",
        FieldDescriptorProto.TYPE_SFIXED64: "int64_t",
        FieldDescriptorProto.TYPE_FLOAT: "float",
        FieldDescriptorProto.TYPE_DOUBLE: "double",
        FieldDescriptorProto.TYPE_STRING: "const char *",
        FieldDescriptorProto.TYPE_BYTES: "const uint8_t *",
        FieldDescriptorProto.TYPE_ENUM: "int32_t",
    }
    return default_types.get(field.type, "int32_t")


def _resolved_field_type(field: FieldDescriptorProto) -> str:
    param_type = get_string_option(field.options, FIELD_CPP_TYPE_TAG).strip()
    if param_type:
        return param_type
    return _field_type(field)


def _resolved_field_name(field: FieldDescriptorProto) -> str:
    param_name = get_string_option(field.options, FIELD_CPP_NAME_TAG).strip()
    if param_name:
        return param_name
    return field.name


def _build_input_params(
    input_message: DescriptorProto | None,
) -> Tuple[List[str], List[str]]:
    arg_names: List[str] = []
    param_decls: List[str] = []
    if input_message is None:
        return param_decls, arg_names

    ordered_fields = sorted(input_message.field, key=lambda field: field.number)
    for field in ordered_fields:
        param_type = _resolved_field_type(field)
        param_name = _resolved_field_name(field)
        param_decls.append(f"{param_type} {param_name}")
        arg_names.append(param_name)
    return param_decls, arg_names


def _build_option_params(arg_types: List[str]) -> Tuple[List[str], List[str]]:
    arg_names = [f"arg{index}" for index in range(len(arg_types))]
    param_decls = [
        f"{arg_type} {arg_name}" for arg_type, arg_name in zip(arg_types, arg_names)
    ]
    return param_decls, arg_names


def _resolved_return_type(method, message_map: Dict[str, DescriptorProto]) -> str:
    return_type = get_string_option(method.options, METHOD_CPP_RETURN_TAG).strip()
    if return_type:
        return return_type

    output_message = message_map.get(method.output_type)
    if output_message is None:
        return "void"

    ordered_fields = sorted(output_message.field, key=lambda field: field.number)
    if len(ordered_fields) == 0:
        return "void"
    if len(ordered_fields) == 1:
        return _resolved_field_type(ordered_fields[0])
    return "void"


def _resolved_method_name(method) -> str:
    method_name = get_string_option(method.options, METHOD_CPP_NAME_TAG).strip()
    if method_name:
        return method_name
    return method.name


def _build_decl(return_type: str, method_name: str, param_decls: List[str]) -> str:
    params_blob = ", ".join(param_decls)
    if method_name.startswith("operator "):
        return f"{method_name}({params_blob})"
    return f"{return_type} {method_name}({params_blob})"


def _method_spec_from_descriptor(
    method, message_map: Dict[str, DescriptorProto]
) -> MethodSpec:
    source_virtual = get_bool_option(method.options, METHOD_SOURCE_VIRTUAL_TAG, True)
    emit_api = get_bool_option(method.options, METHOD_EMIT_API_TAG, True)
    emit_service = get_bool_option(method.options, METHOD_EMIT_SERVICE_TAG, True)
    visibility = (
        get_string_option(method.options, METHOD_VISIBILITY_TAG).strip().lower()
        or "public"
    )
    if visibility not in {"public", "protected", "private"}:
        raise ValueError(
            f"{method.name}: unsupported method_visibility '{visibility}' "
            "(expected: public, protected, private)"
        )

    method_name = _resolved_method_name(method)
    return_type = _resolved_return_type(method, message_map)

    arg_types = get_string_list_option(method.options, METHOD_CPP_ARG_TYPES_TAG)
    if arg_types:
        param_decls, arg_names = _build_option_params(arg_types)
    else:
        input_message = message_map.get(method.input_type)
        param_decls, arg_names = _build_input_params(input_message)

    decl = _build_decl(return_type, method_name, param_decls)
    return MethodSpec(
        decl,
        method_name,
        arg_names,
        "",
        return_type == "void",
        source_virtual,
        emit_api,
        emit_service,
        visibility,
    )


def collect_lineage_methods(
    lineage: List[str],
    service_index: ServiceIndex,
    message_map: Dict[str, DescriptorProto],
) -> List[MethodSpec]:
    by_decl: Dict[str, MethodSpec] = {}

    for service_full_name in lineage:
        service, _ = service_index[service_full_name]
        for method in service.method:
            spec = _method_spec_from_descriptor(method, message_map)
            by_decl.pop(spec.decl, None)
            by_decl[spec.decl] = spec

    return list(by_decl.values())


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
