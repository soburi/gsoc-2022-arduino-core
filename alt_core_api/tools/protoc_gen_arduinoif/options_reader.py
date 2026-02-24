# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import importlib.util
import os
import types
from typing import List

def _load_arduino_opts_pb2() -> types.ModuleType:
    pb2_path = os.environ.get("PROTOC_GEN_ARDUINOIF_PB2")
    if pb2_path:
        module_name = "_protoc_gen_arduinoif_arduino_opts_pb2"
        spec = importlib.util.spec_from_file_location(module_name, pb2_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"failed to load arduino_opts_pb2 from '{pb2_path}'")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    from .generated import arduino_opts_pb2 as bundled_pb2

    return bundled_pb2


arduino_opts_pb2 = _load_arduino_opts_pb2()

__all__ = [
    "field_cpp_name",
    "field_cpp_type",
    "method_cpp_arg_types",
    "method_cpp_name",
    "method_cpp_return",
    "method_emit_api",
    "method_emit_service",
    "method_source_virtual",
    "method_visibility",
    "service_api_class_name",
    "service_api_member_name",
    "service_base_services",
    "service_extra_includes",
    "service_generate_api_class",
    "service_generate_service_class",
    "service_generate_service_impl_class",
    "service_ifc_class_name",
    "service_ifc_header_name",
    "service_service_class_name",
    "service_service_impl_class_name",
]


def _has_extension(options, extension) -> bool:
    try:
        return options.HasExtension(extension)
    except (AttributeError, KeyError):
        return False


def _get_string(options, extension) -> str:
    if not _has_extension(options, extension):
        return ""
    value = options.Extensions[extension]
    return str(value)


def _get_string_list(options, extension) -> List[str]:
    values: List[str] = []
    for value in options.Extensions[extension]:
        text = str(value).strip()
        if text:
            values.append(text)
    return values


def _get_bool(options, extension, default: bool) -> bool:
    if not _has_extension(options, extension):
        return default
    return bool(options.Extensions[extension])


def field_cpp_type(field) -> str:
    return _get_string(field.options, arduino_opts_pb2.cpp_type)


def field_cpp_name(field) -> str:
    return _get_string(field.options, arduino_opts_pb2.field_cpp_name)


def method_cpp_name(method) -> str:
    return _get_string(method.options, arduino_opts_pb2.cpp_name)


def method_cpp_return(method) -> str:
    return _get_string(method.options, arduino_opts_pb2.cpp_return)


def method_cpp_arg_types(method) -> List[str]:
    return _get_string_list(method.options, arduino_opts_pb2.cpp_arg_types)


def method_source_virtual(method, default: bool = True) -> bool:
    return _get_bool(method.options, arduino_opts_pb2.source_virtual, default)


def method_emit_api(method, default: bool = True) -> bool:
    return _get_bool(method.options, arduino_opts_pb2.emit_api, default)


def method_emit_service(method, default: bool = True) -> bool:
    return _get_bool(method.options, arduino_opts_pb2.emit_service, default)


def method_visibility(method) -> str:
    return _get_string(method.options, arduino_opts_pb2.method_visibility)


def service_generate_api_class(service, default: bool = False) -> bool:
    return _get_bool(service.options, arduino_opts_pb2.generate_api_class, default)


def service_generate_service_class(service, default: bool = False) -> bool:
    return _get_bool(service.options, arduino_opts_pb2.generate_service_class, default)


def service_generate_service_impl_class(service, default: bool = False) -> bool:
    return _get_bool(
        service.options,
        arduino_opts_pb2.generate_service_impl_class,
        default,
    )


def service_ifc_class_name(service) -> str:
    return _get_string(service.options, arduino_opts_pb2.ifc_class_name)


def service_api_class_name(service) -> str:
    return _get_string(service.options, arduino_opts_pb2.api_class_name)


def service_service_class_name(service) -> str:
    return _get_string(service.options, arduino_opts_pb2.service_class_name)


def service_service_impl_class_name(service) -> str:
    return _get_string(service.options, arduino_opts_pb2.service_impl_class_name)


def service_api_member_name(service) -> str:
    return _get_string(service.options, arduino_opts_pb2.api_member_name)


def service_base_services(service) -> List[str]:
    return _get_string_list(service.options, arduino_opts_pb2.base_services)


def service_ifc_header_name(service) -> str:
    return _get_string(service.options, arduino_opts_pb2.ifc_header_name)


def service_extra_includes(service) -> List[str]:
    return _get_string_list(service.options, arduino_opts_pb2.extra_includes)
