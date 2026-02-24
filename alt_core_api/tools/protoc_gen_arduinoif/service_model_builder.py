# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Dict, List, NamedTuple, Optional, Tuple

from google.protobuf.descriptor_pb2 import (
    DescriptorProto,
    EnumDescriptorProto,
    FieldDescriptorProto,
)

from .request_context import RequestContext
from .service_model import MethodSpec, PlannedMethod, ServiceModel

__all__ = [
    "ServiceModelBuilder",
]


class ServiceModelBuilder:
    class _ResolvedServiceOptions(NamedTuple):
        ifc_name: str
        api_name: str
        service_name: str
        service_impl_name: str
        api_member_name: str
        generate_api: bool
        generate_service: bool
        generate_service_impl: bool

    _arduino_opts_pb2 = None

    class _OptionsView:
        def __init__(self, options, arduino_opts_pb2) -> None:
            self._options = options
            self._arduino_opts_pb2 = arduino_opts_pb2

        def _ext(self, extension_name: str):
            return getattr(self._arduino_opts_pb2, extension_name)

        def _has_extension(self, extension) -> bool:
            try:
                return self._options.HasExtension(extension)
            except (AttributeError, KeyError):
                return False

        def string(self, extension_name: str) -> str:
            extension = self._ext(extension_name)
            if not self._has_extension(extension):
                return ""
            return str(self._options.Extensions[extension])

        def string_list(self, extension_name: str) -> List[str]:
            extension = self._ext(extension_name)
            return [
                text
                for text in (str(value).strip() for value in self._options.Extensions[extension])
                if text
            ]

        def bool(self, extension_name: str, default: bool = False) -> bool:
            extension = self._ext(extension_name)
            if not self._has_extension(extension):
                return default
            return bool(self._options.Extensions[extension])

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
        self._service_full_name = RequestContext.full_service_name(package_name, service.name)

    @classmethod
    def configure_options_module(cls, arduino_opts_pb2_module) -> None:
        cls._arduino_opts_pb2 = arduino_opts_pb2_module

    @classmethod
    def _options_view(cls, options):
        if cls._arduino_opts_pb2 is None:
            raise RuntimeError("ServiceModelBuilder options module is not configured")
        return cls._OptionsView(options, cls._arduino_opts_pb2)

    @classmethod
    def build(
        cls,
        service,
        package_name: str,
        proto_enums: List[EnumDescriptorProto],
        context: RequestContext,
    ) -> ServiceModel:
        return cls(service, package_name, proto_enums, context)._build()

    def _build(self) -> ServiceModel:
        service_opts = self._options_view(self._service.options)

        ifc_header = service_opts.string("ifc_header_name").strip() or f"{self._snake_case(self._service.name)}_interface.hpp"
        if ifc_header.endswith("_interface.hpp"):
            stem = ifc_header[: -len("_interface.hpp")]
        else:
            stem = PurePosixPath(ifc_header).stem

        options = self._ResolvedServiceOptions(
            ifc_name=service_opts.string("ifc_class_name").strip() or f"{self._service.name}Interface",
            api_name=service_opts.string("api_class_name").strip() or f"{self._service.name}Api",
            service_name=service_opts.string("service_class_name").strip() or f"{self._service.name}Service",
            service_impl_name=service_opts.string("service_impl_class_name").strip()
            or f"{self._service.name}ServiceImpl",
            api_member_name=service_opts.string("api_member_name").strip() or "api_",
            generate_api=service_opts.bool("generate_api_class", False),
            generate_service=service_opts.bool("generate_service_class", False),
            generate_service_impl=service_opts.bool("generate_service_impl_class", False),
        )
        self._validate_generation_flags(options)

        lineage = self._collect_service_lineage(self._service_full_name)
        own_specs = self._collect_lineage_methods(
            [self._service_full_name],
            self._context.service_index,
            self._context.message_map,
        )
        lineage_specs = self._collect_lineage_methods(
            lineage,
            self._context.service_index,
            self._context.message_map,
        )

        own_virtual_decls = {spec.decl for spec in own_specs if spec.source_virtual}
        api_callable = {
            spec.call_name
            for spec in lineage_specs
            if spec.emit_api and spec.source_virtual
        }
        service_callable = {
            spec.call_name for spec in lineage_specs if spec.emit_service
        }

        self._validate_api_methods(options, lineage_specs)
        self._validate_service_impl_api_delegate(options, lineage_specs, api_callable)

        service_impl_callable = (
            api_callable
            if (options.generate_service_impl and options.generate_api)
            else service_callable
        )
        methods = self._build_planned_methods(
            lineage_specs,
            own_virtual_decls,
            service_impl_callable,
        )

        include_list = list(dict.fromkeys(self._collect_lineage_includes(lineage)))

        base_ifc_names: List[str] = []
        base_ifc_headers: List[str] = []
        for ancestor_full_name in lineage[:-1]:
            ancestor_service, _ = self._context.service_index[ancestor_full_name]
            ancestor_opts = self._options_view(ancestor_service.options)
            base_ifc_names.append(
                ancestor_opts.string("ifc_class_name").strip()
                or f"{ancestor_service.name}Interface"
            )
            base_ifc_headers.append(
                ancestor_opts.string("ifc_header_name").strip()
                or f"{self._snake_case(ancestor_service.name)}_interface.hpp"
            )
        base_ifc_names = list(dict.fromkeys(base_ifc_names))
        base_ifc_headers = list(dict.fromkeys(base_ifc_headers))

        api_header = f"{stem}_api.hpp"
        service_header = f"{stem}_service.hpp"
        service_impl_header = f"{stem}_service_impl.hpp"

        api_includes = [ifc_header, *include_list]

        service_includes: List[str] = []
        if options.generate_service:
            service_includes = list(dict.fromkeys([*base_ifc_headers, *include_list]))
            if self._proto_enums:
                service_includes = list(dict.fromkeys([ifc_header, *service_includes]))

        service_impl_includes: List[str] = []
        if options.generate_service_impl:
            service_impl_includes = [service_header, *include_list]
            if options.generate_api:
                service_impl_includes.insert(1, api_header)

        namespace_name = "::".join(part for part in self._package_name.split(".") if part)

        return ServiceModel(
            include_list=include_list,
            api_includes=api_includes,
            service_includes=service_includes,
            service_impl_includes=service_impl_includes,
            namespace_name=namespace_name,
            proto_enums=self._proto_enums,
            ifc_name=options.ifc_name,
            api_name=options.api_name,
            service_name=options.service_name,
            service_impl_name=options.service_impl_name,
            api_member_name=options.api_member_name,
            service_base_ifc_class_names=base_ifc_names,
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
        service_index: Dict[str, Tuple[object, str]],
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
        cls,
        method,
        message_map: Dict[str, DescriptorProto],
    ) -> MethodSpec:
        options = cls._options_view(method.options)
        source_virtual = options.bool("source_virtual", True)
        emit_api = options.bool("emit_api", True)
        emit_service = options.bool("emit_service", True)
        visibility = options.string("method_visibility").strip().lower() or "public"
        if visibility not in {"public", "protected", "private"}:
            raise ValueError(
                f"{method.name}: unsupported method_visibility '{visibility}' "
                "(expected: public, protected, private)"
            )

        method_name = options.string("cpp_name").strip() or method.name

        def resolve_field(field: FieldDescriptorProto) -> Tuple[str, str]:
            field_opts = cls._options_view(field.options)
            field_type = (
                field_opts.string("cpp_type").strip()
                or cls._default_types.get(field.type, "int32_t")
            )
            field_name = field_opts.string("field_cpp_name").strip() or field.name
            return field_type, field_name

        return_type = options.string("cpp_return").strip()
        if not return_type:
            output_message = message_map.get(method.output_type)
            if output_message is None:
                return_type = "void"
            else:
                output_fields = sorted(output_message.field, key=lambda f: f.number)
                return_type = (
                    resolve_field(output_fields[0])[0]
                    if len(output_fields) == 1
                    else "void"
                )

        arg_names: List[str] = []
        param_decls: List[str] = []
        arg_types = options.string_list("cpp_arg_types")
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

        return MethodSpec(
            decl=decl,
            call_name=method_name,
            arg_names=arg_names,
            suffix="",
            returns_void=(return_type == "void"),
            source_virtual=source_virtual,
            emit_api=emit_api,
            emit_service=emit_service,
            visibility=visibility,
        )

    def _validate_generation_flags(
        self,
        options: ServiceModelBuilder._ResolvedServiceOptions,
    ) -> None:
        if options.generate_service_impl and not options.generate_service:
            raise ValueError(
                f"{self._service.name}: generate_service_impl_class=true requires generate_service_class=true"
            )

    def _validate_api_methods(
        self,
        options: ServiceModelBuilder._ResolvedServiceOptions,
        lineage_method_specs,
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
        options: ServiceModelBuilder._ResolvedServiceOptions,
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
        inherited: List[str] = []
        for base_ref in self._options_view(service.options).string_list("base_services"):
            base_full_name = self._resolve_service_reference(base_ref, package_name)
            inherited.extend(
                self._collect_service_lineage(
                    base_full_name,
                    [*visiting, service_full_name],
                )
            )

        lineage = list(dict.fromkeys([*inherited, service_full_name]))
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

        if candidate not in self._context.service_index:
            raise ValueError(
                f"service '{candidate}' not found for base_services entry '{reference}'"
            )
        return candidate

    def _collect_lineage_includes(self, lineage: List[str]) -> List[str]:
        includes: List[str] = []
        for service_full_name in lineage:
            service, _ = self._context.service_index[service_full_name]
            includes.extend(self._options_view(service.options).string_list("extra_includes"))
        return includes

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
    def _build_planned_methods(
        lineage_method_specs,
        own_virtual_decls,
        service_impl_callable,
    ) -> List[PlannedMethod]:
        methods: List[PlannedMethod] = []
        for spec in lineage_method_specs:
            in_service = spec.emit_service
            methods.append(
                PlannedMethod(
                    spec=spec,
                    in_ifc=spec.decl in own_virtual_decls,
                    in_api=spec.emit_api and spec.source_virtual,
                    in_service=in_service,
                    in_service_impl=in_service and spec.call_name in service_impl_callable,
                )
            )
        return methods
