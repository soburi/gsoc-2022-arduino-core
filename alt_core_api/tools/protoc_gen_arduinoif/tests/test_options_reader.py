# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from google.protobuf.compiler import plugin_pb2
from google.protobuf.descriptor_pb2 import (
    DescriptorProto,
    FieldDescriptorProto,
    FileDescriptorSet,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from protoc_gen_arduinoif.plan_builder import (  # noqa: E402
    arduino_opts_pb2,
    ServicePlanBuilder,
)


def _build_request(tmp_path: Path) -> plugin_pb2.CodeGeneratorRequest:
    descriptor_path = tmp_path / "input.desc"
    proto_dir = REPO_ROOT / "idl/proto"
    google_dir = proto_dir / "google/protobuf"
    proto_files = [
        "print.proto",
        "stream.proto",
        "hardware_serial.proto",
        "common.proto",
    ]

    command = [
        "protoc",
        f"--descriptor_set_out={descriptor_path}",
        "--include_imports",
        f"--proto_path={proto_dir}",
        f"--proto_path={google_dir}",
        *proto_files,
    ]
    subprocess.run(command, cwd=REPO_ROOT, check=True)

    descriptor_set = FileDescriptorSet()
    descriptor_set.ParseFromString(descriptor_path.read_bytes())

    request = plugin_pb2.CodeGeneratorRequest()
    request.file_to_generate.extend(proto_files)
    request.proto_file.extend(descriptor_set.file)
    return request


def test_method_and_service_options_from_extensions(tmp_path: Path) -> None:
    request = _build_request(tmp_path)
    hardware_serial_file = next(
        proto_file
        for proto_file in request.proto_file
        if proto_file.name == "hardware_serial.proto"
    )
    service = next(
        descriptor
        for descriptor in hardware_serial_file.service
        if descriptor.name == "HardwareSerial"
    )
    begin_baud = next(method for method in service.method if method.name == "BeginBaud")

    service_opts = ServicePlanBuilder._OptionsView(service.options)
    method_opts = ServicePlanBuilder._OptionsView(begin_baud.options)

    assert service_opts.bool("generate_api_class", False) is True
    assert service_opts.string_list("base_services") == ["Stream"]
    assert service_opts.string("api_class_name") == "arduino::HardwareSerial"

    assert method_opts.string("cpp_name") == "begin"
    assert method_opts.string("cpp_return") == ""
    assert method_opts.string_list("cpp_arg_types") == ["unsigned long"]
    assert method_opts.string("method_visibility") == ""
    assert method_opts.bool("source_virtual", True) is True
    assert method_opts.bool("emit_api", True) is True
    assert method_opts.bool("emit_service", True) is True


def test_field_option_accessors() -> None:
    message = DescriptorProto(name="Sample")
    field = message.field.add()
    field.name = "value"
    field.number = 1
    field.type = FieldDescriptorProto.TYPE_UINT32

    field_opts = ServicePlanBuilder._OptionsView(field.options)
    assert field_opts.string("cpp_type") == ""
    assert field_opts.string("field_cpp_name") == ""

    field.options.Extensions[arduino_opts_pb2.cpp_type] = "uint8_t"
    field.options.Extensions[arduino_opts_pb2.field_cpp_name] = "input_value"

    assert field_opts.string("cpp_type") == "uint8_t"
    assert field_opts.string("field_cpp_name") == "input_value"
