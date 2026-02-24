# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import sys
from pathlib import PurePosixPath
from typing import Iterator, Tuple

from google.protobuf.compiler import plugin_pb2

from . import ServicePlan
from .header_render import render_enum_header
from .request_context import build_request_context
from .service_codegen import render_service_headers

__all__ = [
    "main",
]


def _iter_generated_files(
    request: plugin_pb2.CodeGeneratorRequest,
) -> Iterator[Tuple[str, str]]:
    context = build_request_context(request)

    for proto_file in request.proto_file:
        if not context.is_requested_proto(proto_file.name):
            continue

        if proto_file.enum_type and not proto_file.service:
            yield (
                _types_header_name_for_proto(proto_file.name),
                render_enum_header(list(proto_file.enum_type)),
            )

        for service in proto_file.service:
            service_plan = ServicePlan.build(
                service,
                proto_file.package,
                list(proto_file.enum_type),
                context,
            )
            yield from render_service_headers(service_plan)


def _types_header_name_for_proto(proto_file_name: str) -> str:
    return f"{PurePosixPath(proto_file_name).stem}_types.h"


def main() -> int:
    request = plugin_pb2.CodeGeneratorRequest()
    request.ParseFromString(sys.stdin.buffer.read())
    response = plugin_pb2.CodeGeneratorResponse()

    try:
        for name, content in _iter_generated_files(request):
            output = response.file.add()
            output.name = name
            output.content = content
    except Exception as error:
        response.error = str(error)

    if hasattr(plugin_pb2.CodeGeneratorResponse, "FEATURE_PROTO3_OPTIONAL"):
        response.supported_features = (
            plugin_pb2.CodeGeneratorResponse.FEATURE_PROTO3_OPTIONAL
        )

    sys.stdout.buffer.write(response.SerializeToString())
    return 0
