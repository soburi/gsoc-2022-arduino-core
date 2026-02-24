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
    field_cpp_name,
    field_cpp_type,
    method_cpp_arg_types,
    method_cpp_name,
    method_cpp_return,
    method_emit_api,
    method_emit_service,
    method_source_virtual,
    method_visibility,
    service_api_class_name,
    service_base_services,
    service_generate_api_class,
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

    assert service_generate_api_class(service) is True
    assert service_base_services(service) == ["Stream"]
    assert service_api_class_name(service) == "arduino::HardwareSerial"

    assert method_cpp_name(begin_baud) == "begin"
    assert method_cpp_return(begin_baud) == ""
    assert method_cpp_arg_types(begin_baud) == ["unsigned long"]
    assert method_visibility(begin_baud) == ""
    assert method_source_virtual(begin_baud, True) is True
    assert method_emit_api(begin_baud, True) is True
    assert method_emit_service(begin_baud, True) is True


def test_field_option_accessors() -> None:
    message = DescriptorProto(name="Sample")
    field = message.field.add()
    field.name = "value"
    field.number = 1
    field.type = FieldDescriptorProto.TYPE_UINT32

    assert field_cpp_type(field) == ""
    assert field_cpp_name(field) == ""

    field.options.Extensions[arduino_opts_pb2.cpp_type] = "uint8_t"
    field.options.Extensions[arduino_opts_pb2.field_cpp_name] = "input_value"

    assert field_cpp_type(field) == "uint8_t"
    assert field_cpp_name(field) == "input_value"
