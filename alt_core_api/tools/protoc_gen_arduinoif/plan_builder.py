# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import importlib.util
import os
import re
import subprocess
import tempfile
import types
from pathlib import PurePosixPath
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple

from google.protobuf.descriptor_pb2 import (
    DescriptorProto,
    EnumDescriptorProto,
    FieldDescriptorProto,
)

from . import MethodSpec, PlannedMethod, ServiceIndex
from .request_context import RequestContext
from .service_plan import ServicePlan

__all__ = [
    "ServicePlanBuilder",
]


def _patch_runtime_guard(pb2_path: Path) -> None:
    text = pb2_path.read_text(encoding="utf-8")
    import_line = "from google.protobuf import runtime_version as _runtime_version\n"
    import_guard = (
        "try:\n"
        "  from google.protobuf import runtime_version as _runtime_version\n"
        "except ImportError:\n"
        "  _runtime_version = None\n"
    )
    if import_line in text and import_guard not in text:
        text = text.replace(import_line, import_guard)

    pattern = re.compile(
        r"_runtime_version\.ValidateProtobufRuntimeVersion\(\n"
        r"(?P<body>(?:\s+.*\n)+?)"
        r"\)\n"
    )
    match = pattern.search(text)
    if match and "if _runtime_version is not None:" not in text:
        body = "".join(f"  {line}" for line in match.group("body").splitlines(True))
        wrapped = (
            "if _runtime_version is not None:\n"
            "  _runtime_version.ValidateProtobufRuntimeVersion(\n"
            f"{body}"
            "  )\n"
        )
        text = text[: match.start()] + wrapped + text[match.end() :]

    pb2_path.write_text(text, encoding="utf-8")


def _generate_pb2_to_temp() -> Path:
    proto_dir = Path(__file__).resolve().parents[2] / "idl" / "proto"
    proto_file = proto_dir / "arduino_opts.proto"
    cache_dir = Path(tempfile.gettempdir()) / "protoc_gen_arduinoif_pb2"
    cache_dir.mkdir(parents=True, exist_ok=True)
    pb2_path = cache_dir / "arduino_opts_pb2.py"

    should_generate = True
    if pb2_path.exists():
        should_generate = pb2_path.stat().st_mtime < proto_file.stat().st_mtime

    if should_generate:
        subprocess.run(
            [
                "protoc",
                f"--proto_path={proto_dir}",
                f"--python_out={cache_dir}",
                str(proto_file),
            ],
            check=True,
        )
        _patch_runtime_guard(pb2_path)

    return pb2_path


def _load_arduino_opts_pb2() -> types.ModuleType:
    pb2_path = os.environ.get("PROTOC_GEN_ARDUINOIF_PB2")
    if pb2_path and Path(pb2_path).exists():
        module_name = "_protoc_gen_arduinoif_arduino_opts_pb2"
        spec = importlib.util.spec_from_file_location(module_name, pb2_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"failed to load arduino_opts_pb2 from '{pb2_path}'")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    generated_path = _generate_pb2_to_temp()
    module_name = "_protoc_gen_arduinoif_arduino_opts_pb2_generated"
    spec = importlib.util.spec_from_file_location(module_name, generated_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"failed to load generated arduino_opts_pb2 '{generated_path}'"
        )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


arduino_opts_pb2 = _load_arduino_opts_pb2()


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


class _ResolvedServiceOptions(NamedTuple):
    ifc_name: str
    api_name: str
    service_name: str
    service_impl_name: str
    api_member_name: str
    generate_api: bool
    generate_service: bool
    generate_service_impl: bool


class ServicePlanBuilder:
    _default_types = {
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
        self._service_full_name = RequestContext.full_service_name(
            package_name, service.name
        )

    @classmethod
    def build(
        cls,
        service,
        package_name: str,
        proto_enums: List[EnumDescriptorProto],
        context: RequestContext,
    ) -> ServicePlan:
        return cls(
            service,
            package_name,
            proto_enums,
            context,
        )._build()

    def _build(self) -> ServicePlan:
        options = self._resolve_options()
        self._validate_generation_flags(options)

        own_method_specs = self._collect_lineage_methods(
            [self._service_full_name],
            self._context.service_index,
            self._context.message_map,
        )
        lineage = self._collect_service_lineage(self._service_full_name)
        ancestor_services = lineage[:-1]
        lineage_method_specs = self._collect_lineage_methods(
            lineage,
            self._context.service_index,
            self._context.message_map,
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

        include_list = self._dedupe_ordered(self._collect_lineage_includes(lineage))
        service_base_ifc_class_names: List[str] = []
        service_base_ifc_header_names: List[str] = []
        for ancestor_full_name in ancestor_services:
            ancestor_service, _ = self._context.service_index[ancestor_full_name]
            service_base_ifc_class_names.append(self._ifc_class_name(ancestor_service))
            service_base_ifc_header_names.append(
                self._service_header_name(ancestor_service)
            )
        service_base_ifc_class_names = self._dedupe_ordered(
            service_base_ifc_class_names
        )
        service_base_ifc_header_names = self._dedupe_ordered(
            service_base_ifc_header_names
        )

        stem = self._service_header_stem(self._service)
        ifc_header = self._service_header_name(self._service)
        api_header = f"{stem}_api.hpp"
        service_header = f"{stem}_service.hpp"
        service_impl_header = f"{stem}_service_impl.hpp"

        api_includes = [ifc_header, *include_list]

        service_includes: List[str] = []
        if options.generate_service:
            service_includes = self._dedupe_ordered(
                [*service_base_ifc_header_names, *include_list]
            )
            if self._proto_enums:
                service_includes = self._dedupe_ordered(
                    [ifc_header, *service_includes]
                )

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
            namespace_name=self._cpp_namespace_from_package(self._package_name),
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

    @classmethod
    def _collect_lineage_methods(
        cls,
        lineage: List[str],
        service_index: ServiceIndex,
        message_map: Dict[str, DescriptorProto],
    ) -> List[MethodSpec]:
        by_decl: Dict[str, MethodSpec] = {}

        for service_full_name in lineage:
            service, _ = service_index[service_full_name]
            for method in service.method:
                spec = cls._method_spec_from_descriptor(method, message_map)
                by_decl.pop(spec.decl, None)
                by_decl[spec.decl] = spec

        return list(by_decl.values())

    @classmethod
    def _method_spec_from_descriptor(
        cls, method, message_map: Dict[str, DescriptorProto]
    ) -> MethodSpec:
        source_virtual = method_source_virtual(method, True)
        emit_api = method_emit_api(method, True)
        emit_service = method_emit_service(method, True)
        visibility = method_visibility(method).strip().lower() or "public"
        if visibility not in {"public", "protected", "private"}:
            raise ValueError(
                f"{method.name}: unsupported method_visibility '{visibility}' "
                "(expected: public, protected, private)"
            )

        method_name = cls._resolved_method_name(method)
        return_type = cls._resolved_return_type(method, message_map)

        arg_types = method_cpp_arg_types(method)
        if arg_types:
            param_decls, arg_names = cls._build_option_params(arg_types)
        else:
            input_message = message_map.get(method.input_type)
            param_decls, arg_names = cls._build_input_params(input_message)

        decl = cls._build_decl(return_type, method_name, param_decls)
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

    @classmethod
    def _resolved_return_type(
        cls, method, message_map: Dict[str, DescriptorProto]
    ) -> str:
        return_type = method_cpp_return(method).strip()
        if return_type:
            return return_type

        output_message = message_map.get(method.output_type)
        if output_message is None:
            return "void"

        ordered_fields = sorted(output_message.field, key=lambda field: field.number)
        if len(ordered_fields) == 0:
            return "void"
        if len(ordered_fields) == 1:
            return cls._resolved_field_type(ordered_fields[0])
        return "void"

    @staticmethod
    def _resolved_method_name(method) -> str:
        method_name = method_cpp_name(method).strip()
        if method_name:
            return method_name
        return method.name

    @staticmethod
    def _build_decl(
        return_type: str, method_name: str, param_decls: List[str]
    ) -> str:
        params_blob = ", ".join(param_decls)
        if method_name.startswith("operator "):
            return f"{method_name}({params_blob})"
        return f"{return_type} {method_name}({params_blob})"

    @classmethod
    def _build_input_params(
        cls,
        input_message: DescriptorProto | None,
    ) -> Tuple[List[str], List[str]]:
        arg_names: List[str] = []
        param_decls: List[str] = []
        if input_message is None:
            return param_decls, arg_names

        ordered_fields = sorted(input_message.field, key=lambda field: field.number)
        for field in ordered_fields:
            param_type = cls._resolved_field_type(field)
            param_name = cls._resolved_field_name(field)
            param_decls.append(f"{param_type} {param_name}")
            arg_names.append(param_name)
        return param_decls, arg_names

    @staticmethod
    def _build_option_params(arg_types: List[str]) -> Tuple[List[str], List[str]]:
        arg_names = [f"arg{index}" for index in range(len(arg_types))]
        param_decls = [
            f"{arg_type} {arg_name}"
            for arg_type, arg_name in zip(arg_types, arg_names)
        ]
        return param_decls, arg_names

    @classmethod
    def _resolved_field_type(cls, field: FieldDescriptorProto) -> str:
        param_type = field_cpp_type(field).strip()
        if param_type:
            return param_type
        return cls._field_type(field)

    @staticmethod
    def _resolved_field_name(field: FieldDescriptorProto) -> str:
        param_name = field_cpp_name(field).strip()
        if param_name:
            return param_name
        return field.name

    @classmethod
    def _field_type(cls, field: FieldDescriptorProto) -> str:
        return cls._default_types.get(field.type, "int32_t")

    def _resolve_options(self) -> _ResolvedServiceOptions:
        ifc_name = service_ifc_class_name(self._service).strip() or f"{self._service.name}Interface"
        api_name = service_api_class_name(self._service).strip() or f"{self._service.name}Api"
        service_impl_name = (
            service_service_impl_class_name(self._service).strip()
            or f"{self._service.name}ServiceImpl"
        )
        api_member_name = service_api_member_name(self._service).strip() or "api_"

        return _ResolvedServiceOptions(
            ifc_name=ifc_name,
            api_name=api_name,
            service_name=self._service_class_name(self._service),
            service_impl_name=service_impl_name,
            api_member_name=api_member_name,
            generate_api=service_generate_api_class(self._service, False),
            generate_service=service_generate_service_class(self._service, False),
            generate_service_impl=service_generate_service_impl_class(
                self._service,
                False,
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

    def _collect_service_lineage(
        self,
        service_full_name: str,
        visiting: Optional[List[str]] = None,
    ) -> List[str]:
        if service_full_name in self._context.lineage_cache:
            return self._context.lineage_cache[service_full_name]
        if visiting is None:
            visiting = []
        if service_full_name in visiting:
            cycle = " -> ".join([*visiting, service_full_name])
            raise ValueError(f"cyclic service inheritance detected: {cycle}")

        entry = self._context.service_index.get(service_full_name)
        if entry is None:
            raise ValueError(f"service '{service_full_name}' not found")
        service, package_name = entry
        base_refs = service_base_services(service)

        inherited: List[str] = []
        for base_ref in base_refs:
            base_full_name = self._resolve_service_reference(base_ref, package_name)
            inherited.extend(
                self._collect_service_lineage(
                    base_full_name,
                    [*visiting, service_full_name],
                )
            )
        inherited.append(service_full_name)
        lineage = self._dedupe_ordered(inherited)
        self._context.lineage_cache[service_full_name] = lineage
        return lineage

    def _resolve_service_reference(
        self,
        reference: str,
        current_package: str,
    ) -> str:
        if reference.startswith("."):
            candidate = reference
        elif "." in reference:
            candidate = f".{reference}"
        elif current_package:
            candidate = f".{current_package}.{reference}"
        else:
            candidate = f".{reference}"

        if candidate in self._context.service_index:
            return candidate

        raise ValueError(
            f"service '{candidate}' not found for base_services entry '{reference}'"
        )

    def _collect_lineage_includes(self, lineage: List[str]) -> List[str]:
        includes: List[str] = []
        for service_full_name in lineage:
            service, _ = self._context.service_index[service_full_name]
            includes.extend(service_extra_includes(service))
        return self._dedupe_ordered(includes)

    @staticmethod
    def _service_class_name(service) -> str:
        return service_service_class_name(service).strip() or f"{service.name}Service"

    @staticmethod
    def _ifc_class_name(service) -> str:
        return service_ifc_class_name(service).strip() or f"{service.name}Interface"

    @classmethod
    def _service_header_name(cls, service) -> str:
        header_name = service_ifc_header_name(service).strip()
        if header_name:
            return header_name
        return f"{cls._snake_case(service.name)}_interface.hpp"

    @classmethod
    def _service_header_stem(cls, service) -> str:
        ifc_header = cls._service_header_name(service)
        suffix = "_interface.hpp"
        if ifc_header.endswith(suffix):
            return ifc_header[: -len(suffix)]
        return PurePosixPath(ifc_header).stem

    @staticmethod
    def _cpp_namespace_from_package(package_name: str) -> str:
        return "::".join(part for part in package_name.split(".") if part)

    @staticmethod
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

    @staticmethod
    def _dedupe_ordered(items: List[str]) -> List[str]:
        seen = set()
        result: List[str] = []
        for item in items:
            if item in seen:
                continue
            seen.add(item)
            result.append(item)
        return result

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
                    in_service_impl=in_service
                    and spec.call_name in service_impl_callable,
                )
            )
        return methods
