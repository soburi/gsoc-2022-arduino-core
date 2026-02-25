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
    MethodDescriptorProto,
    ServiceDescriptorProto,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from protoc_gen_arduinoif.common import get_arduino_opts_pb2  # noqa: E402
from protoc_gen_arduinoif.request_context import RequestContext  # noqa: E402
from protoc_gen_arduinoif.service_model_builder import ServiceModelBuilder  # noqa: E402

arduino_opts_pb2 = get_arduino_opts_pb2()


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

    subprocess.run(
        [
            "protoc",
            f"--descriptor_set_out={descriptor_path}",
            "--include_imports",
            f"--proto_path={proto_dir}",
            f"--proto_path={google_dir}",
            *proto_files,
        ],
        cwd=REPO_ROOT,
        check=True,
    )

    descriptor_set = FileDescriptorSet()
    descriptor_set.ParseFromString(descriptor_path.read_bytes())

    request = plugin_pb2.CodeGeneratorRequest()
    request.file_to_generate.extend(proto_files)
    request.proto_file.extend(descriptor_set.file)
    return request


def test_builder_reads_service_and_method_extensions(tmp_path: Path) -> None:
    request = _build_request(tmp_path)
    context = RequestContext.build(request)

    hardware_serial_file = next(
        proto_file
        for proto_file in request.proto_file
        if proto_file.name == "hardware_serial.proto"
    )
    service = next(s for s in hardware_serial_file.service if s.name == "HardwareSerial")

    model = ServiceModelBuilder.build(
        service,
        hardware_serial_file.package,
        list(hardware_serial_file.enum_type),
        context,
    )

    assert model.generate_api is True
    assert model.api_name == "arduino::HardwareSerial"

    ifc_decls = [planned.spec.decl for planned in model.methods if planned.in_ifc]
    assert "void begin(unsigned long arg0)" in ifc_decls
    assert "void begin(unsigned long arg0, uint16_t arg1)" in ifc_decls


def test_builder_reads_field_extensions_from_input_message() -> None:
    input_message = DescriptorProto(name="Input")
    field = input_message.field.add()
    field.name = "value"
    field.number = 1
    field.type = FieldDescriptorProto.TYPE_UINT32
    field.options.Extensions[arduino_opts_pb2.cpp_type] = "uint8_t"
    field.options.Extensions[arduino_opts_pb2.field_cpp_name] = "input_value"

    empty_message = DescriptorProto(name="Empty")

    method = MethodDescriptorProto(
        name="Foo",
        input_type=".test.Input",
        output_type=".test.Empty",
    )
    service = ServiceDescriptorProto(name="Sample")
    service.method.extend([method])

    context = RequestContext(
        message_map={
            ".test.Input": input_message,
            ".test.Empty": empty_message,
        },
        service_index={
            ".test.Sample": (service, "test"),
        },
        lineage_cache={},
        requested_files=set(),
        requested_basenames=set(),
    )

    model = ServiceModelBuilder.build(service, "test", [], context)
    ifc_specs = [planned.spec for planned in model.methods if planned.in_ifc]
    assert len(ifc_specs) == 1
    assert ifc_specs[0].decl == "void Foo(uint8_t input_value)"
