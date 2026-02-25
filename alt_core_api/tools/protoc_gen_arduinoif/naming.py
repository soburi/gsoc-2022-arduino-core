# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

__all__ = [
    "full_service_name",
]


def full_service_name(package_name: str, service_name: str) -> str:
    if package_name:
        return f".{package_name}.{service_name}"
    return f".{service_name}"
