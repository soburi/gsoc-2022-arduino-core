# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
from typing import Iterator, List, Tuple

from jinja2 import Environment, FileSystemLoader

from . import MethodSpec
from .service_plan import ServicePlan

__all__ = [
    "ServicePlanRenderer",
]

_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
_ENV = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=True,
)

_SURFACES = {
    "ifc": ("ifc_header.hpp.j2", "include_list", "in_ifc"),
    "api": ("api_header.hpp.j2", "api_includes", "in_api"),
    "service": ("service_header.hpp.j2", "service_includes", "in_service"),
    "service_impl": (
        "service_impl_header.hpp.j2",
        "service_impl_includes",
        "in_service_impl",
    ),
}

_HEADER_ORDER = [
    ("ifc_header", "ifc", None),
    ("api_header", "api", "generate_api"),
    ("service_header", "service", "generate_service"),
    ("service_impl_header", "service_impl", "generate_service_impl"),
]


class ServicePlanRenderer:
    def __init__(self, plan: ServicePlan) -> None:
        self._plan = plan

    def render_ifc_header_content(self) -> str:
        return self._render_surface("ifc")

    def render_api_header_content(self) -> str:
        return self._render_surface("api")

    def render_service_header_content(self) -> str:
        return self._render_surface("service")

    def render_service_impl_header_content(self) -> str:
        return self._render_surface("service_impl")

    def iter_headers(self) -> Iterator[Tuple[str, str]]:
        for header_attr, surface, gate_attr in _HEADER_ORDER:
            if gate_attr and not getattr(self._plan, gate_attr):
                continue
            yield getattr(self._plan, header_attr), self._render_surface(surface)

    def _render_surface(self, surface: str) -> str:
        template, include_attr, method_attr = _SURFACES[surface]
        public_methods, protected_methods, private_methods = self._group_surface_methods(
            method_attr
        )

        return self._render_template(
            template,
            includes=getattr(self._plan, include_attr),
            namespace_name=self._plan.namespace_name,
            public_methods=public_methods,
            protected_methods=protected_methods,
            private_methods=private_methods,
            **self._surface_context(surface),
        )

    def _surface_context(self, surface: str) -> dict:
        if surface == "ifc":
            return {
                "proto_enums": self._plan.proto_enums,
                "ifc_name": self._plan.ifc_name,
            }
        if surface == "api":
            return {
                "ifc_name": self._plan.ifc_name,
                "api_name": self._plan.api_name,
            }
        if surface == "service":
            return {
                "service_name": self._plan.service_name,
                "service_base_ifc_class_names": self._plan.service_base_ifc_class_names,
            }
        return {
            "generate_api": self._plan.generate_api,
            "api_name": self._plan.api_name,
            "service_name": self._plan.service_name,
            "service_impl_name": self._plan.service_impl_name,
            "api_member_name": self._plan.api_member_name,
        }

    @staticmethod
    def _render_template(template_name: str, **context) -> str:
        rendered = _ENV.get_template(template_name).render(**context)
        return rendered if rendered.endswith("\n") else f"{rendered}\n"

    def _group_surface_methods(
        self,
        method_attr: str,
    ) -> Tuple[List[MethodSpec], List[MethodSpec], List[MethodSpec]]:
        public_methods: List[MethodSpec] = []
        protected_methods: List[MethodSpec] = []
        private_methods: List[MethodSpec] = []

        for planned in self._plan.methods:
            if not getattr(planned, method_attr):
                continue
            spec = planned.spec
            if spec.visibility == "protected":
                protected_methods.append(spec)
            elif spec.visibility == "private":
                private_methods.append(spec)
            else:
                public_methods.append(spec)

        return public_methods, protected_methods, private_methods
