# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from google.protobuf.compiler import plugin_pb2
from google.protobuf.descriptor_pb2 import (
    DescriptorProto,
    FileDescriptorSet,
    MethodDescriptorProto,
    ServiceDescriptorProto,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from protoc_gen_arduinoif import (  # noqa: E402
    RequestContext,
    ServiceModelBuilder,
)
from protoc_gen_arduinoif.core import _load_arduino_opts_pb2  # noqa: E402
from protoc_gen_arduinoif.service_renderer import ServiceRenderer  # noqa: E402

arduino_opts_pb2 = _load_arduino_opts_pb2()
ServiceModelBuilder.configure_options_module(arduino_opts_pb2)


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


def _hardware_serial_model(tmp_path: Path):
    request = _build_request(tmp_path)
    context = RequestContext.build(request)

    target_file = next(
        proto_file
        for proto_file in request.proto_file
        if proto_file.name == "hardware_serial.proto"
    )
    target_service = next(
        service for service in target_file.service if service.name == "HardwareSerial"
    )
    return ServiceModelBuilder.build(
        target_service,
        target_file.package,
        list(target_file.enum_type),
        context,
    )


def test_build_service_model_has_expected_headers_and_groups(tmp_path: Path) -> None:
    model = _hardware_serial_model(tmp_path)

    assert model.ifc_header == "hardware_serial_interface.hpp"
    assert model.api_header == "hardware_serial_api.hpp"
    assert model.service_header == "hardware_serial_service.hpp"
    assert model.service_impl_header == "hardware_serial_service_impl.hpp"
    assert model.generate_api is True
    assert model.generate_service is True
    assert model.generate_service_impl is True

    ifc_methods = [planned.spec for planned in model.methods if planned.in_ifc]
    ifc_call_names = [spec.call_name for spec in ifc_methods]
    assert ifc_call_names == ["begin", "begin", "end", "operator bool"]
    assert all(spec.visibility == "public" for spec in ifc_methods)


def test_render_service_headers_uses_stable_order(tmp_path: Path) -> None:
    model = _hardware_serial_model(tmp_path)
    rendered_names = [name for name, _ in ServiceRenderer(model).iter_headers()]
    assert rendered_names == [
        "hardware_serial_interface.hpp",
        "hardware_serial_api.hpp",
        "hardware_serial_service.hpp",
        "hardware_serial_service_impl.hpp",
    ]


def test_build_service_model_prefers_latest_duplicate_decl() -> None:
    empty_message = DescriptorProto(name="Empty")
    message_map = {".test.Empty": empty_message}

    base_method = MethodDescriptorProto(
        name="Ping",
        input_type=".test.Empty",
        output_type=".test.Empty",
    )
    child_method = MethodDescriptorProto(
        name="Ping",
        input_type=".test.Empty",
        output_type=".test.Empty",
    )
    child_method.options.Extensions[arduino_opts_pb2.method_visibility] = "protected"

    base_service = ServiceDescriptorProto(name="Base")
    base_service.method.extend([base_method])
    child_service = ServiceDescriptorProto(name="Child")
    child_service.options.Extensions[arduino_opts_pb2.base_services].append("Base")
    child_service.method.extend([child_method])

    service_index = {
        ".test.Base": (base_service, "test"),
        ".test.Child": (child_service, "test"),
    }
    context = RequestContext(
        message_map=message_map,
        service_index=service_index,
        lineage_cache={},
        requested_files=set(),
        requested_basenames=set(),
    )
    model = ServiceModelBuilder.build(
        child_service,
        "test",
        [],
        context,
    )
    specs = [planned.spec for planned in model.methods]
    assert len(specs) == 1
    assert specs[0].visibility == "protected"
