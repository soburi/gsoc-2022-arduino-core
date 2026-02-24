# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Dict, List, Tuple

from google.protobuf.descriptor_pb2 import DescriptorProto, FieldDescriptorProto

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
    MethodSpec,
    ServiceIndex,
)
from .wire_options import get_bool_option, get_string_list_option, get_string_option

__all__ = [
    "collect_lineage_methods",
]


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
