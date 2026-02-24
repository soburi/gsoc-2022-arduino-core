# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import sys
from typing import Iterator, Tuple

from google.protobuf.compiler import plugin_pb2

from .enum_renderer import EnumRenderer
from .options_runtime import get_arduino_opts_pb2
from .service_renderer import ServiceRenderer
from .service_model_builder import ServiceModelBuilder
from .request_context import RequestContext

__all__ = [
    "main",
]


def _iter_generated_files(
    request: plugin_pb2.CodeGeneratorRequest,
) -> Iterator[Tuple[str, str]]:
    context = RequestContext.build(request)

    for proto_file in request.proto_file:
        if not context.is_requested_proto(proto_file.name):
            continue

        if proto_file.enum_type and not proto_file.service:
            yield from EnumRenderer(
                proto_file.name,
                list(proto_file.enum_type),
            ).iter_headers()

        for service in proto_file.service:
            service_model = ServiceModelBuilder.build(
                service,
                proto_file.package,
                list(proto_file.enum_type),
                context,
            )
            yield from ServiceRenderer(service_model).iter_headers()


def main() -> int:
    get_arduino_opts_pb2()
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
