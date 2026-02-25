# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import sys
from pathlib import Path
from typing import NamedTuple

from google.protobuf.descriptor_pb2 import EnumDescriptorProto

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from protoc_gen_arduinoif.common import (  # noqa: E402
    MethodSpec,
    ServiceModel,
)
from protoc_gen_arduinoif.service_renderer import ServiceRenderer  # noqa: E402


class _PlannedMethod(NamedTuple):
    spec: MethodSpec
    in_ifc: bool
    in_api: bool
    in_service: bool
    in_service_impl: bool


def _sample_model() -> ServiceModel:
    enum_desc = EnumDescriptorProto(name="Mode")
    enum_desc.value.add(name="MODE_A", number=0)

    foo_spec = MethodSpec(
        decl="int foo(uint8_t arg0)",
        call_name="foo",
        arg_names=["arg0"],
        returns_void=False,
        source_virtual=True,
        emit_api=True,
        emit_service=True,
        visibility="public",
    )
    bar_spec = MethodSpec(
        decl="void bar()",
        call_name="bar",
        arg_names=[],
        returns_void=True,
        source_virtual=True,
        emit_api=True,
        emit_service=True,
        visibility="protected",
    )
    baz_spec = MethodSpec(
        decl="void baz()",
        call_name="baz",
        arg_names=[],
        returns_void=True,
        source_virtual=True,
        emit_api=True,
        emit_service=True,
        visibility="private",
    )

    methods = [
        _PlannedMethod(foo_spec, True, True, True, True),
        _PlannedMethod(bar_spec, True, True, True, True),
        _PlannedMethod(baz_spec, True, True, True, True),
    ]

    return ServiceModel(
        include_list=["ifc_dep.hpp"],
        api_includes=["api_dep.hpp"],
        service_includes=["service_dep.hpp"],
        service_impl_includes=["impl_dep.hpp"],
        namespace_name="arduino",
        proto_enums=[enum_desc],
        ifc_name="ExampleInterface",
        api_name="ExampleApi",
        service_name="ExampleService",
        service_impl_name="ExampleServiceImpl",
        api_member_name="api_",
        service_base_ifc_class_names=["BaseIfc"],
        ifc_header="example_interface.hpp",
        api_header="example_api.hpp",
        service_header="example_service.hpp",
        service_impl_header="example_service_impl.hpp",
        methods=methods,
        generate_api=True,
        generate_service=True,
        generate_service_impl=True,
    )


def test_renderer_templates_emit_expected_fragments() -> None:
    model = _sample_model()
    renderer = ServiceRenderer(model)
    rendered = dict(renderer)

    ifc_content = rendered["example_interface.hpp"]
    assert "class ExampleInterface" in ifc_content
    assert "virtual int foo(uint8_t arg0) = 0;" in ifc_content
    assert "typedef enum Mode" in ifc_content
    assert "namespace arduino" in ifc_content

    api_content = rendered["example_api.hpp"]
    assert "class ExampleApi : public ExampleInterface" in api_content
    assert "return impl_.foo(arg0);" in api_content
    assert "impl_.bar();" in api_content

    service_content = rendered["example_service.hpp"]
    assert "class ExampleService : public BaseIfc" in service_content
    assert "virtual void baz() = 0;" in service_content

    impl_content = rendered["example_service_impl.hpp"]
    assert "class ExampleServiceImpl : public ExampleService" in impl_content
    assert "return api_.foo(arg0);" in impl_content
    assert "api_.baz();" in impl_content
    assert "override" in impl_content


def test_renderer_template_iter_order_is_stable() -> None:
    model = _sample_model()
    renderer = ServiceRenderer(model)

    names = [name for name, _ in renderer]
    assert names == [
        "example_interface.hpp",
        "example_api.hpp",
        "example_service.hpp",
        "example_service_impl.hpp",
    ]
