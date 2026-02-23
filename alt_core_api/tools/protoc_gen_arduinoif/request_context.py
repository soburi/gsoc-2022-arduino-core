# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Dict, List, NamedTuple, Set

from google.protobuf.compiler import plugin_pb2
from google.protobuf.descriptor_pb2 import DescriptorProto

from .constants import ServiceIndex

__all__ = [
    "RequestContext",
    "build_request_context",
    "full_service_name",
]


class RequestContext(NamedTuple):
    message_map: Dict[str, DescriptorProto]
    service_index: ServiceIndex
    lineage_cache: Dict[str, List[str]]
    requested_files: Set[str]
    requested_basenames: Set[str]

    def is_requested_proto(self, proto_name: str) -> bool:
        proto_basename = PurePosixPath(proto_name).name
        return (
            proto_name in self.requested_files
            or proto_basename in self.requested_basenames
        )


class _RequestContextBuilder:
    def __init__(self, request: plugin_pb2.CodeGeneratorRequest) -> None:
        self._request = request

    def build(self) -> RequestContext:
        message_map: Dict[str, DescriptorProto] = {}
        service_index: ServiceIndex = {}

        for proto_file in self._request.proto_file:
            prefix = f".{proto_file.package}" if proto_file.package else ""
            for message in proto_file.message_type:
                self._add_message(message_map, prefix, "", message)
            for service in proto_file.service:
                full_name = full_service_name(proto_file.package, service.name)
                service_index[full_name] = (service, proto_file.package)

        requested_files = set(self._request.file_to_generate)
        requested_basenames = {PurePosixPath(name).name for name in requested_files}
        return RequestContext(
            message_map=message_map,
            service_index=service_index,
            lineage_cache={},
            requested_files=requested_files,
            requested_basenames=requested_basenames,
        )

    @staticmethod
    def _add_message(
        message_map: Dict[str, DescriptorProto],
        package_prefix: str,
        parent_name: str,
        message: DescriptorProto,
    ) -> None:
        if parent_name:
            full_name = f"{package_prefix}.{parent_name}.{message.name}"
        else:
            full_name = f"{package_prefix}.{message.name}"
        message_map[full_name] = message

        child_parent = full_name[len(package_prefix) + 1 :]
        for nested in message.nested_type:
            _RequestContextBuilder._add_message(
                message_map, package_prefix, child_parent, nested
            )


def full_service_name(package_name: str, service_name: str) -> str:
    if package_name:
        return f".{package_name}.{service_name}"
    return f".{service_name}"


def build_request_context(
    request: plugin_pb2.CodeGeneratorRequest,
) -> RequestContext:
    return _RequestContextBuilder(request).build()
