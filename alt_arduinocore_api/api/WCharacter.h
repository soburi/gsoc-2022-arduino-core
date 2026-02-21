/*
 * Copyright (c) 2026 TOKITA Hiroshi
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#pragma once

extern "C" {
bool arduino_wchar_is_alnum(int c);
bool arduino_wchar_is_alpha(int c);
bool arduino_wchar_is_ascii(int c);
bool arduino_wchar_is_blank(int c);
bool arduino_wchar_is_cntrl(int c);
bool arduino_wchar_is_digit(int c);
bool arduino_wchar_is_graph(int c);
bool arduino_wchar_is_lower(int c);
bool arduino_wchar_is_print(int c);
bool arduino_wchar_is_punct(int c);
bool arduino_wchar_is_space(int c);
bool arduino_wchar_is_upper(int c);
bool arduino_wchar_is_xdigit(int c);
int arduino_wchar_to_ascii(int c);
int arduino_wchar_to_lower(int c);
int arduino_wchar_to_upper(int c);
}

namespace arduino {

ALWAYS_INLINE bool isAlphaNumeric(int c) {
	return arduino_wchar_is_alnum(c);
}

ALWAYS_INLINE bool isAlpha(int c)  {
	return arduino_wchar_is_alpha(c);
}

ALWAYS_INLINE bool isAscii(int c) {
	return arduino_wchar_is_ascii(c);
}

ALWAYS_INLINE bool isWhitespace(int c) {
	return arduino_wchar_is_blank(c);
}

ALWAYS_INLINE bool isControl(int c) {
	return arduino_wchar_is_cntrl(c);
}

ALWAYS_INLINE bool isDigit(int c) {
	return arduino_wchar_is_digit(c);
}

ALWAYS_INLINE bool isGraph(int c) {
	return arduino_wchar_is_graph(c);
}

ALWAYS_INLINE bool isLowerCase(int c) {
	return arduino_wchar_is_lower(c);
}

ALWAYS_INLINE bool isPrintable(int c) {
	return arduino_wchar_is_print(c);
}

ALWAYS_INLINE bool isPunct(int c) {
	return arduino_wchar_is_punct(c);
}

ALWAYS_INLINE bool isSpace(int c)  {
	return arduino_wchar_is_space(c);
}

ALWAYS_INLINE bool isUpperCase(int c) {
	return arduino_wchar_is_upper(c);
}

ALWAYS_INLINE bool isHexadecimalDigit(int c) {
	return arduino_wchar_is_xdigit(c);
}

ALWAYS_INLINE int toAscii(int c) {
	return arduino_wchar_to_ascii(c);
}

ALWAYS_INLINE int toLowerCase(int c) {
	return arduino_wchar_to_lower(c);
}

ALWAYS_INLINE int toUpperCase(int c) {
	return arduino_wchar_to_upper(c);
}

}
