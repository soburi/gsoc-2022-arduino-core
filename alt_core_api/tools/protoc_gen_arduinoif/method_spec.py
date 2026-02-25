# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Dict, List, NamedTuple, Optional, Tuple

from google.protobuf.descriptor_pb2 import DescriptorProto, FieldDescriptorProto

__all__ = [
    "MethodSpec",
]

_DEFAULT_FIELD_CPP_TYPES: Dict[int, str] = {
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


def _has_extension(options, extension) -> bool:
    try:
        return options.HasExtension(extension)
    except (AttributeError, KeyError):
        return False


def _option_string(options, extension) -> str:
    if not _has_extension(options, extension):
        return ""
    return str(options.Extensions[extension])


def _option_string_list(options, extension) -> List[str]:
    try:
        values = options.Extensions[extension]
    except (AttributeError, KeyError):
        return []
    return [text for text in (str(value).strip() for value in values) if text]


def _option_bool(options, extension, default: bool = False) -> bool:
    if not _has_extension(options, extension):
        return default
    return bool(options.Extensions[extension])


class MethodSpec(NamedTuple):
    decl: str
    call_name: str
    arg_names: List[str]
    returns_void: bool
    source_virtual: bool
    emit_api: bool
    emit_service: bool
    visibility: str

    @classmethod
    def build(
        cls,
        method,
        *,
        opts_pb2,
        message_map: Dict[str, DescriptorProto],
        default_types: Optional[Dict[int, str]] = None,
    ) -> "MethodSpec":
        default_field_types = default_types or _DEFAULT_FIELD_CPP_TYPES
        method_opts = method.options

        source_virtual = _option_bool(method_opts, opts_pb2.source_virtual, True)
        emit_api = _option_bool(method_opts, opts_pb2.emit_api, True)
        emit_service = _option_bool(method_opts, opts_pb2.emit_service, True)

        visibility = _option_string(method_opts, opts_pb2.method_visibility).strip().lower()
        if not visibility:
            visibility = "public"
        if visibility not in {"public", "protected", "private"}:
            raise ValueError(
                f"{method.name}: unsupported method_visibility '{visibility}' "
                "(expected: public, protected, private)"
            )

        method_name = _option_string(method_opts, opts_pb2.cpp_name).strip() or method.name

        def resolve_field(field: FieldDescriptorProto) -> Tuple[str, str]:
            field_opts = field.options
            field_type = (
                _option_string(field_opts, opts_pb2.cpp_type).strip()
                or default_field_types.get(field.type, "int32_t")
            )
            field_name = _option_string(field_opts, opts_pb2.field_cpp_name).strip() or field.name
            return field_type, field_name

        return_type = _option_string(method_opts, opts_pb2.cpp_return).strip()
        if not return_type:
            output_message = message_map.get(method.output_type)
            if output_message is None:
                return_type = "void"
            elif len(output_message.field) == 1:
                return_type = resolve_field(output_message.field[0])[0]
            else:
                return_type = "void"

        arg_names: List[str] = []
        param_decls: List[str] = []
        arg_types = _option_string_list(method_opts, opts_pb2.cpp_arg_types)
        if arg_types:
            arg_names = [f"arg{index}" for index in range(len(arg_types))]
            param_decls = [
                f"{arg_type} {arg_name}"
                for arg_type, arg_name in zip(arg_types, arg_names)
            ]
        else:
            input_message = message_map.get(method.input_type)
            if input_message is not None:
                for field in sorted(input_message.field, key=lambda f: f.number):
                    field_type, field_name = resolve_field(field)
                    param_decls.append(f"{field_type} {field_name}")
                    arg_names.append(field_name)

        params_blob = ", ".join(param_decls)
        decl = (
            f"{method_name}({params_blob})"
            if method_name.startswith("operator ")
            else f"{return_type} {method_name}({params_blob})"
        )

        return cls(
            decl=decl,
            call_name=method_name,
            arg_names=arg_names,
            returns_void=(return_type == "void"),
            source_virtual=source_virtual,
            emit_api=emit_api,
            emit_service=emit_service,
            visibility=visibility,
        )
