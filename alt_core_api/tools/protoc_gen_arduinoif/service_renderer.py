# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
from typing import Iterator, List, Tuple

from jinja2 import Environment, FileSystemLoader

from .service_model import MethodSpec, ServiceModel

__all__ = [
    "ServiceRenderer",
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


class ServiceRenderer:
    def __init__(self, model: ServiceModel) -> None:
        self._model = model

    def iter_headers(self) -> Iterator[Tuple[str, str]]:
        for header_attr, surface, gate_attr in _HEADER_ORDER:
            if gate_attr and not getattr(self._model, gate_attr):
                continue
            yield getattr(self._model, header_attr), self._render_surface(surface)

    def _render_surface(self, surface: str) -> str:
        template, include_attr, method_attr = _SURFACES[surface]
        public_methods, protected_methods, private_methods = self._group_surface_methods(
            method_attr
        )

        return self._render_template(
            template,
            includes=getattr(self._model, include_attr),
            namespace_name=self._model.namespace_name,
            public_methods=public_methods,
            protected_methods=protected_methods,
            private_methods=private_methods,
            **self._surface_context(surface),
        )

    def _surface_context(self, surface: str) -> dict:
        if surface == "ifc":
            return {
                "proto_enums": self._model.proto_enums,
                "ifc_name": self._model.ifc_name,
            }
        if surface == "api":
            return {
                "ifc_name": self._model.ifc_name,
                "api_name": self._model.api_name,
            }
        if surface == "service":
            return {
                "service_name": self._model.service_name,
                "service_base_ifc_class_names": self._model.service_base_ifc_class_names,
            }
        return {
            "generate_api": self._model.generate_api,
            "api_name": self._model.api_name,
            "service_name": self._model.service_name,
            "service_impl_name": self._model.service_impl_name,
            "api_member_name": self._model.api_member_name,
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

        for planned in self._model.methods:
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
