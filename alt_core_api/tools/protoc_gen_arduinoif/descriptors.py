# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Dict, List, Optional

from .constants import (
    SERVICE_BASE_SERVICES_TAG,
    SERVICE_EXTRA_INCLUDES_TAG,
    SERVICE_IFC_CLASS_NAME_TAG,
    SERVICE_IFC_HEADER_NAME_TAG,
    SERVICE_SERVICE_CLASS_NAME_TAG,
    ServiceIndex,
)
from .wire_options import get_string_list_option, get_string_option

__all__ = [
    "snake_case",
    "dedupe_ordered",
    "collect_service_lineage",
    "collect_lineage_includes",
    "service_class_name",
    "ifc_class_name",
    "class_decl",
    "service_header_name",
    "service_header_stem",
    "cpp_namespace_from_package",
    "types_header_name_for_proto",
]


def snake_case(name: str) -> str:
    first_pass = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    second_pass = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", first_pass)
    return second_pass.lower()


def dedupe_ordered(items: List[str]) -> List[str]:
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


def collect_service_lineage(
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
            collect_service_lineage(
                base_full_name,
                service_index,
                lineage_cache,
                [*visiting, service_full_name],
            )
        )
    inherited.append(service_full_name)
    lineage = dedupe_ordered(inherited)
    lineage_cache[service_full_name] = lineage
    return lineage


def collect_lineage_includes(
    lineage: List[str],
    service_index: ServiceIndex,
) -> List[str]:
    includes: List[str] = []
    for service_full_name in lineage:
        service, _ = service_index[service_full_name]
        includes.extend(
            get_string_list_option(service.options, SERVICE_EXTRA_INCLUDES_TAG)
        )
    return dedupe_ordered(includes)


def service_class_name(service) -> str:
    return (
        get_string_option(service.options, SERVICE_SERVICE_CLASS_NAME_TAG).strip()
        or f"{service.name}Service"
    )


def ifc_class_name(service) -> str:
    return (
        get_string_option(service.options, SERVICE_IFC_CLASS_NAME_TAG).strip()
        or f"{service.name}Interface"
    )


def class_decl(class_name: str, base_classes: List[str]) -> str:
    if not base_classes:
        return f"class {class_name} {{"
    bases = ", ".join(f"public {base_class}" for base_class in base_classes)
    return f"class {class_name} : {bases} {{"


def service_header_name(service) -> str:
    header_name = get_string_option(
        service.options, SERVICE_IFC_HEADER_NAME_TAG
    ).strip()
    if header_name:
        return header_name
    return f"{snake_case(service.name)}_interface.hpp"


def service_header_stem(service) -> str:
    ifc_header = service_header_name(service)
    suffix = "_interface.hpp"
    if ifc_header.endswith(suffix):
        return ifc_header[: -len(suffix)]
    return PurePosixPath(ifc_header).stem


def cpp_namespace_from_package(package_name: str) -> str:
    return "::".join(part for part in package_name.split(".") if part)


def types_header_name_for_proto(proto_file_name: str) -> str:
    return f"{PurePosixPath(proto_file_name).stem}_types.h"
