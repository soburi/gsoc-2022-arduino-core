# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import List, NamedTuple


class MethodSpec(NamedTuple):
    decl: str
    call_name: str
    arg_names: List[str]
    suffix: str
    returns_void: bool
    source_virtual: bool
    emit_api: bool
    emit_service: bool
    visibility: str


class PlannedMethod(NamedTuple):
    spec: MethodSpec
    in_ifc: bool
    in_api: bool
    in_service: bool
    in_service_impl: bool

__all__ = [
    "MethodSpec",
    "PlannedMethod",
]
