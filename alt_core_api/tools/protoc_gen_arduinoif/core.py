# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import sys

from google.protobuf.compiler import plugin_pb2

from .descriptors import types_header_name_for_proto
from .header_render import render_enum_header
from .request_context import build_request_context
from .service_codegen import build_service_plan, iter_rendered_service_headers


def main() -> int:
    request = plugin_pb2.CodeGeneratorRequest()
    request.ParseFromString(sys.stdin.buffer.read())

    response = plugin_pb2.CodeGeneratorResponse()
    context = build_request_context(request)

    try:
        for proto_file in request.proto_file:
            if not context.is_requested_proto(proto_file.name):
                continue

            if proto_file.enum_type and not proto_file.service:
                output = response.file.add()
                output.name = types_header_name_for_proto(proto_file.name)
                output.content = render_enum_header(list(proto_file.enum_type))

            for service in proto_file.service:
                service_plan = build_service_plan(
                    service,
                    proto_file.package,
                    list(proto_file.enum_type),
                    context,
                )
                for name, content in iter_rendered_service_headers(service_plan):
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
