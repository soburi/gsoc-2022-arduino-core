# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import sys
from pathlib import Path

from google.protobuf.compiler import plugin_pb2
from google.protobuf.descriptor_pb2 import DescriptorProto

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from protoc_gen_arduinoif.naming import full_service_name  # noqa: E402
from protoc_gen_arduinoif.request_context import RequestContext  # noqa: E402


def _build_request() -> plugin_pb2.CodeGeneratorRequest:
    request = plugin_pb2.CodeGeneratorRequest()
    request.file_to_generate.extend(
        [
            "idl/proto/print.proto",
            "common.proto",
        ]
    )

    print_file = request.proto_file.add()
    print_file.name = "idl/proto/print.proto"
    print_file.package = "arduino"
    outer = DescriptorProto(name="Outer")
    outer.nested_type.extend([DescriptorProto(name="Inner")])
    print_file.message_type.extend([outer])
    print_file.service.add().name = "Print"

    common_file = request.proto_file.add()
    common_file.name = "common.proto"
    common_file.message_type.add().name = "Common"
    common_file.service.add().name = "CommonService"

    return request


def test_build_request_context_collects_message_and_service_indexes() -> None:
    context = RequestContext.build(_build_request())

    assert ".arduino.Outer" in context.message_map
    assert ".arduino.Outer.Inner" in context.message_map
    assert ".Common" in context.message_map

    assert ".arduino.Print" in context.service_index
    assert ".CommonService" in context.service_index

    assert context.lineage_cache == {}


def test_full_service_name_handles_package_and_root() -> None:
    assert full_service_name("arduino", "Print") == ".arduino.Print"
    assert full_service_name("", "CommonService") == ".CommonService"


def test_is_requested_proto_matches_path_and_basename() -> None:
    context = RequestContext.build(_build_request())

    assert context.is_requested_proto("idl/proto/print.proto")
    assert context.is_requested_proto("print.proto")
    assert context.is_requested_proto("common.proto")
    assert not context.is_requested_proto("idl/proto/stream.proto")
