# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import sys
from pathlib import PurePosixPath

from google.protobuf.compiler import plugin_pb2

from .descriptors import (
    collect_message_types,
    collect_service_descriptors,
    full_service_name,
    types_header_name_for_proto,
)
from .header_render import render_enum_header
from .service_codegen import build_service_plan, iter_rendered_service_headers


def main() -> int:
    request = plugin_pb2.CodeGeneratorRequest()
    request.ParseFromString(sys.stdin.buffer.read())

    response = plugin_pb2.CodeGeneratorResponse()
    message_map = collect_message_types(request)
    service_index = collect_service_descriptors(request)
    lineage_cache: dict[str, list[str]] = {}
    requested_files = set(request.file_to_generate)
    requested_basenames = {PurePosixPath(name).name for name in requested_files}

    try:
        for proto_file in request.proto_file:
            proto_basename = PurePosixPath(proto_file.name).name
            if (
                proto_file.name not in requested_files
                and proto_basename not in requested_basenames
            ):
                continue

            if proto_file.enum_type and not proto_file.service:
                output = response.file.add()
                output.name = types_header_name_for_proto(proto_file.name)
                output.content = render_enum_header(list(proto_file.enum_type))

            for service in proto_file.service:
                service_full_name = full_service_name(proto_file.package, service.name)
                service_plan = build_service_plan(
                    service,
                    service_full_name,
                    service_index,
                    lineage_cache,
                    message_map,
                    proto_file.package,
                    list(proto_file.enum_type),
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
