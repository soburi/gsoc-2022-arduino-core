# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Dict, List, Set, Tuple

from google.protobuf.compiler import plugin_pb2
from google.protobuf.descriptor_pb2 import DescriptorProto

__all__ = [
    "RequestContext",
]


@dataclass
class RequestContext:
    message_map: Dict[str, DescriptorProto]
    service_index: Dict[str, Tuple[object, str]]
    lineage_cache: Dict[str, List[str]]
    requested_files: Set[str]
    requested_basenames: Set[str]

    @classmethod
    def build(cls, request: plugin_pb2.CodeGeneratorRequest) -> "RequestContext":
        message_map: Dict[str, DescriptorProto] = {}
        service_index: Dict[str, Tuple[object, str]] = {}

        for proto_file in request.proto_file:
            prefix = f".{proto_file.package}" if proto_file.package else ""
            for message in proto_file.message_type:
                cls._add_message(message_map, prefix, "", message)
            for service in proto_file.service:
                full_name = cls.full_service_name(proto_file.package, service.name)
                service_index[full_name] = (service, proto_file.package)

        requested_files = set(request.file_to_generate)
        requested_basenames = {PurePosixPath(name).name for name in requested_files}
        return cls(
            message_map=message_map,
            service_index=service_index,
            lineage_cache={},
            requested_files=requested_files,
            requested_basenames=requested_basenames,
        )

    @staticmethod
    def full_service_name(package_name: str, service_name: str) -> str:
        if package_name:
            return f".{package_name}.{service_name}"
        return f".{service_name}"

    def is_requested_proto(self, proto_name: str) -> bool:
        proto_basename = PurePosixPath(proto_name).name
        return (
            proto_name in self.requested_files
            or proto_basename in self.requested_basenames
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
            RequestContext._add_message(
                message_map, package_prefix, child_parent, nested
            )
