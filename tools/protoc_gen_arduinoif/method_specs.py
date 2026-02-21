# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re
from typing import Dict, List

from google.protobuf.descriptor_pb2 import DescriptorProto, FieldDescriptorProto

from .constants import (
    FIELD_CPP_NAME_TAG,
    FIELD_CPP_TYPE_TAG,
    METHOD_CPP_DECL_TAG,
    METHOD_CPP_NAME_TAG,
    METHOD_CPP_RETURN_TAG,
    METHOD_EMIT_API_TAG,
    METHOD_EMIT_SERVICE_TAG,
    METHOD_SOURCE_VIRTUAL_TAG,
    METHOD_VISIBILITY_TAG,
    ServiceIndex,
)
from .model import MethodSpec
from .wire_options import get_bool_option, get_string_option


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
    }
    return default_types.get(field.type, "int32_t")


def _split_top_level_commas(text: str) -> List[str]:
    items: List[str] = []
    start = 0
    paren = 0
    angle = 0
    bracket = 0
    brace = 0

    for index, char in enumerate(text):
        if char == "(":
            paren += 1
        elif char == ")":
            paren = max(paren - 1, 0)
        elif char == "<":
            angle += 1
        elif char == ">":
            angle = max(angle - 1, 0)
        elif char == "[":
            bracket += 1
        elif char == "]":
            bracket = max(bracket - 1, 0)
        elif char == "{":
            brace += 1
        elif char == "}":
            brace = max(brace - 1, 0)
        elif char == "," and paren == 0 and angle == 0 and bracket == 0 and brace == 0:
            item = text[start:index].strip()
            if item:
                items.append(item)
            start = index + 1

    tail = text[start:].strip()
    if tail:
        items.append(tail)
    return items


def _find_matching_paren(text: str, open_index: int) -> int:
    depth = 0
    for index in range(open_index, len(text)):
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
            if depth == 0:
                return index
    raise ValueError(f"unmatched parenthesis in declaration: {text}")


def _extract_param_name(param_decl: str, param_index: int) -> str:
    decl = param_decl.split("=", 1)[0].strip()
    if not decl or decl == "void":
        return ""

    function_ptr = re.search(r"\(\s*[*&]\s*([A-Za-z_]\w*)\s*\)", decl)
    if function_ptr:
        return function_ptr.group(1)

    if decl.endswith("*") or decl.endswith("&"):
        return f"arg{param_index}"

    trailing_name = re.search(r"([A-Za-z_]\w*)\s*(?:\[[^\]]*\])?\s*$", decl)
    if trailing_name is None:
        return f"arg{param_index}"

    candidate = trailing_name.group(1)
    identifiers = re.findall(r"[A-Za-z_]\w*", decl)
    if len(identifiers) <= 1 and " " not in decl:
        return f"arg{param_index}"
    if candidate in {
        "void",
        "const",
        "volatile",
        "signed",
        "unsigned",
        "long",
        "short",
    }:
        return f"arg{param_index}"
    return candidate


def _parse_cpp_decl(method_decl: str) -> MethodSpec:
    signature = method_decl.strip().rstrip(";")
    open_index = signature.find("(")
    if open_index < 0:
        raise ValueError(f"invalid cpp_decl (missing '('): {method_decl}")

    close_index = _find_matching_paren(signature, open_index)
    prefix = signature[:open_index].rstrip()
    suffix = signature[close_index + 1 :].strip()

    method_name = ""
    returns_void = False
    if prefix.startswith("operator "):
        method_name = prefix
    else:
        name_match = re.search(r"([~A-Za-z_][A-Za-z0-9_:~]*)\s*$", prefix)
        if name_match is None:
            raise ValueError(f"invalid cpp_decl (method name): {method_decl}")
        method_name = name_match.group(1).split("::")[-1]
        return_type = prefix[: name_match.start()].strip()
        if not return_type:
            raise ValueError(f"invalid cpp_decl (return type): {method_decl}")
        returns_void = return_type == "void"

    params_blob = signature[open_index + 1 : close_index].strip()
    if not params_blob or params_blob == "void":
        return MethodSpec(
            signature, method_name, [], suffix, returns_void, True, True, True, "public"
        )

    raw_params = _split_top_level_commas(params_blob)
    arg_names: List[str] = []
    for index, raw_param in enumerate(raw_params):
        param_decl = raw_param.strip()
        if not param_decl or param_decl == "void":
            continue

        arg_name = _extract_param_name(param_decl, index)
        if arg_name and not re.search(rf"\b{re.escape(arg_name)}\b", param_decl):
            param_decl = f"{param_decl} {arg_name}"

        arg_names.append(arg_name if arg_name else f"arg{index}")
    return MethodSpec(
        signature,
        method_name,
        arg_names,
        suffix,
        returns_void,
        True,
        True,
        True,
        "public",
    )


def method_spec_from_descriptor(
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

    method_decl = (
        get_string_option(method.options, METHOD_CPP_DECL_TAG).strip().rstrip(";")
    )
    if method_decl:
        parsed = _parse_cpp_decl(method_decl)
        return MethodSpec(
            parsed.decl,
            parsed.call_name,
            parsed.arg_names,
            parsed.suffix,
            parsed.returns_void,
            source_virtual,
            emit_api,
            emit_service,
            visibility,
        )

    method_name = get_string_option(method.options, METHOD_CPP_NAME_TAG).strip()
    if not method_name:
        method_name = method.name

    return_type = get_string_option(method.options, METHOD_CPP_RETURN_TAG).strip()
    if not return_type:
        output_message = message_map.get(method.output_type)
        if output_message is not None and len(output_message.field) == 0:
            return_type = "void"
        else:
            return_type = "void"

    arg_names: List[str] = []
    param_decls: List[str] = []
    input_message = message_map.get(method.input_type)
    if input_message is not None:
        ordered_fields = sorted(input_message.field, key=lambda field: field.number)
        for field in ordered_fields:
            param_type = get_string_option(field.options, FIELD_CPP_TYPE_TAG).strip()
            if not param_type:
                param_type = _field_type(field)

            param_name = get_string_option(field.options, FIELD_CPP_NAME_TAG).strip()
            if not param_name:
                param_name = field.name

            param_decls.append(f"{param_type} {param_name}")
            arg_names.append(param_name)

    decl = f"{return_type} {method_name}({', '.join(param_decls)})"
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
    ordered_decls: List[str] = []
    by_decl: Dict[str, MethodSpec] = {}

    for service_full_name in lineage:
        service, _ = service_index[service_full_name]
        for method in service.method:
            spec = method_spec_from_descriptor(method, message_map)
            if spec.decl in by_decl:
                ordered_decls.remove(spec.decl)
            ordered_decls.append(spec.decl)
            by_decl[spec.decl] = spec

    return [by_decl[decl] for decl in ordered_decls]
