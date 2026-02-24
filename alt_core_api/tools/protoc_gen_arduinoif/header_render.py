# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterator, List, Tuple

from jinja2 import Environment, FileSystemLoader

from . import MethodSpec, PlannedMethod
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


class ServicePlanRenderer:
    def __init__(self, plan: ServicePlan) -> None:
        self._plan = plan

    def render_ifc_header_content(self) -> str:
        public_methods, protected_methods, private_methods = self._group_surface_methods(
            lambda planned: planned.in_ifc
        )
        return self._render_template(
            "ifc_header.hpp.j2",
            includes=self._plan.include_list,
            namespace_name=self._plan.namespace_name,
            proto_enums=self._plan.proto_enums,
            ifc_name=self._plan.ifc_name,
            public_methods=public_methods,
            protected_methods=protected_methods,
            private_methods=private_methods,
        )

    def render_api_header_content(self) -> str:
        public_methods, protected_methods, private_methods = self._group_surface_methods(
            lambda planned: planned.in_api
        )
        return self._render_template(
            "api_header.hpp.j2",
            includes=self._plan.api_includes,
            namespace_name=self._plan.namespace_name,
            ifc_name=self._plan.ifc_name,
            api_name=self._plan.api_name,
            public_methods=public_methods,
            protected_methods=protected_methods,
            private_methods=private_methods,
        )

    def render_service_header_content(self) -> str:
        public_methods, protected_methods, private_methods = self._group_surface_methods(
            lambda planned: planned.in_service
        )
        return self._render_template(
            "service_header.hpp.j2",
            includes=self._plan.service_includes,
            namespace_name=self._plan.namespace_name,
            service_name=self._plan.service_name,
            service_base_ifc_class_names=self._plan.service_base_ifc_class_names,
            public_methods=public_methods,
            protected_methods=protected_methods,
            private_methods=private_methods,
        )

    def render_service_impl_header_content(self) -> str:
        public_methods, protected_methods, private_methods = self._group_surface_methods(
            lambda planned: planned.in_service_impl
        )
        return self._render_template(
            "service_impl_header.hpp.j2",
            includes=self._plan.service_impl_includes,
            namespace_name=self._plan.namespace_name,
            generate_api=self._plan.generate_api,
            api_name=self._plan.api_name,
            service_name=self._plan.service_name,
            service_impl_name=self._plan.service_impl_name,
            api_member_name=self._plan.api_member_name,
            public_methods=public_methods,
            protected_methods=protected_methods,
            private_methods=private_methods,
        )

    def iter_headers(self) -> Iterator[Tuple[str, str]]:
        yield (
            self._plan.ifc_header,
            self.render_ifc_header_content(),
        )

        if self._plan.generate_api:
            yield (
                self._plan.api_header,
                self.render_api_header_content(),
            )

        if self._plan.generate_service:
            yield (
                self._plan.service_header,
                self.render_service_header_content(),
            )

        if self._plan.generate_service_impl:
            yield (
                self._plan.service_impl_header,
                self.render_service_impl_header_content(),
            )

    @staticmethod
    def _render_template(template_name: str, **context) -> str:
        rendered = _ENV.get_template(template_name).render(**context)
        if rendered.endswith("\n"):
            return rendered
        return f"{rendered}\n"

    def _group_surface_methods(
        self,
        in_surface: Callable[[PlannedMethod], bool],
    ) -> Tuple[List[MethodSpec], List[MethodSpec], List[MethodSpec]]:
        public_methods: List[MethodSpec] = []
        protected_methods: List[MethodSpec] = []
        private_methods: List[MethodSpec] = []

        for planned in self._plan.methods:
            if not in_surface(planned):
                continue
            spec = planned.spec
            if spec.visibility == "protected":
                protected_methods.append(spec)
            elif spec.visibility == "private":
                private_methods.append(spec)
            else:
                public_methods.append(spec)

        return public_methods, protected_methods, private_methods
