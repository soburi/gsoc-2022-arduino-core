# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Dict, List, Tuple

__all__ = [
    "get_string_option",
    "get_bool_option",
    "get_string_list_option",
]

ParsedFields = Dict[int, List[Tuple[int, object]]]
_OPTIONS_PARSE_CACHE: Dict[int, Tuple[bytes, ParsedFields]] = {}
_OPTIONS_PARSE_CACHE_LIMIT = 1024


def _read_varint(data: bytes, index: int) -> Tuple[int, int]:
    value = 0
    shift = 0
    while True:
        if index >= len(data):
            raise ValueError("unexpected end of varint")
        byte = data[index]
        index += 1
        value |= (byte & 0x7F) << shift
        if not (byte & 0x80):
            return value, index
        shift += 7
        if shift > 63:
            raise ValueError("varint is too large")


def _parse_wire_fields(data: bytes) -> ParsedFields:
    parsed: ParsedFields = {}
    index = 0

    while index < len(data):
        key, index = _read_varint(data, index)
        field_number = key >> 3
        wire_type = key & 0x7

        if wire_type == 0:
            value, index = _read_varint(data, index)
        elif wire_type == 1:
            if index + 8 > len(data):
                raise ValueError("invalid fixed64 field")
            value = data[index : index + 8]
            index += 8
        elif wire_type == 2:
            length, index = _read_varint(data, index)
            if index + length > len(data):
                raise ValueError("invalid length-delimited field")
            value = data[index : index + length]
            index += length
        elif wire_type == 5:
            if index + 4 > len(data):
                raise ValueError("invalid fixed32 field")
            value = data[index : index + 4]
            index += 4
        else:
            raise ValueError(f"unsupported wire type {wire_type}")

        parsed.setdefault(field_number, []).append((wire_type, value))

    return parsed


def _parsed_fields_from_options(options) -> ParsedFields:
    raw = options.SerializeToString()
    if not raw:
        return {}

    cache_key = id(options)
    cached = _OPTIONS_PARSE_CACHE.get(cache_key)
    if cached is not None and cached[0] == raw:
        return cached[1]

    try:
        fields = _parse_wire_fields(raw)
    except ValueError:
        return {}

    if len(_OPTIONS_PARSE_CACHE) > _OPTIONS_PARSE_CACHE_LIMIT:
        _OPTIONS_PARSE_CACHE.clear()
    _OPTIONS_PARSE_CACHE[cache_key] = (raw, fields)
    return fields


def get_string_option(options, field_number: int) -> str:
    fields = _parsed_fields_from_options(options)
    if not fields:
        return ""

    for wire_type, value in fields.get(field_number, []):
        if wire_type == 2:
            try:
                return bytes(value).decode("utf-8")
            except UnicodeDecodeError:
                return ""
    return ""


def get_bool_option(options, field_number: int, default: bool = False) -> bool:
    fields = _parsed_fields_from_options(options)
    if not fields:
        return default

    for wire_type, value in fields.get(field_number, []):
        if wire_type == 0:
            return bool(value)
    return default


def get_string_list_option(options, field_number: int) -> List[str]:
    fields = _parsed_fields_from_options(options)
    if not fields:
        return []

    values: List[str] = []
    for wire_type, value in fields.get(field_number, []):
        if wire_type != 2:
            continue
        try:
            text = bytes(value).decode("utf-8").strip()
        except UnicodeDecodeError:
            continue
        if text:
            values.append(text)
    return values
