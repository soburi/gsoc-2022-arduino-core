# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import importlib.util
import os
import types
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple

from google.protobuf.descriptor_pb2 import (
    DescriptorProto,
    EnumDescriptorProto,
    FieldDescriptorProto,
    ServiceDescriptorProto,
)

__all__ = [
    "full_service_name",
    "get_arduino_opts_pb2",
    "ServiceDescriptor",
    "OptionsView",
    "MethodSpec",
    "PlannedMethod",
    "ServiceModel",
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


class OptionsView:
    def __init__(self, options) -> None:
        self._options = options

    def has(self, extension) -> bool:
        try:
            return self._options.HasExtension(extension)
        except (AttributeError, KeyError):
            return False

    def string(self, extension) -> str:
        if not self.has(extension):
            return ""
        return str(self._options.Extensions[extension])

    def string_list(self, extension) -> List[str]:
        try:
            values = self._options.Extensions[extension]
        except (AttributeError, KeyError):
            return []
        return [text for text in (str(value).strip() for value in values) if text]

    def bool(self, extension, default: bool = False) -> bool:
        if not self.has(extension):
            return default
        return bool(self._options.Extensions[extension])


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
        method_opts = OptionsView(method.options)

        source_virtual = method_opts.bool(opts_pb2.source_virtual, True)
        emit_api = method_opts.bool(opts_pb2.emit_api, True)
        emit_service = method_opts.bool(opts_pb2.emit_service, True)
        visibility = method_opts.string(opts_pb2.method_visibility).strip().lower()
        if not visibility:
            visibility = "public"
        if visibility not in {"public", "protected", "private"}:
            raise ValueError(
                f"{method.name}: unsupported method_visibility '{visibility}' "
                "(expected: public, protected, private)"
            )

        method_name = method_opts.string(opts_pb2.cpp_name).strip() or method.name

        def resolve_field(field: FieldDescriptorProto) -> Tuple[str, str]:
            field_opts = OptionsView(field.options)
            field_type = (
                field_opts.string(opts_pb2.cpp_type).strip()
                or default_field_types.get(field.type, "int32_t")
            )
            field_name = field_opts.string(opts_pb2.field_cpp_name).strip() or field.name
            return field_type, field_name

        return_type = method_opts.string(opts_pb2.cpp_return).strip()
        if not return_type:
            output_message = message_map.get(method.output_type)
            if output_message is None:
                return_type = "void"
            else:
                return_type = (
                    resolve_field(output_message.field[0])[0]
                    if len(output_message.field) == 1
                    else "void"
                )

        arg_names: List[str] = []
        param_decls: List[str] = []
        arg_types = method_opts.string_list(opts_pb2.cpp_arg_types)
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


ServiceDescriptor = Tuple[ServiceDescriptorProto, str]


def full_service_name(package_name: str, service_name: str) -> str:
    if package_name:
        return f".{package_name}.{service_name}"
    return f".{service_name}"


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

    return _load_module_from_path(
        source_path, "_protoc_gen_arduinoif_arduino_opts_pb2"
    )
