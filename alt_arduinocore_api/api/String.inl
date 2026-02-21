/*
 * Copyright (c) 2026 TOKITA Hiroshi
 *
 * SPDX-License-Identifier: Apache-2.0
 */

namespace arduino {

inline void String::StringIfHelper() const {
}

inline String::String(const char *cstr)
	: buffer(NULL), capacity(0), len(0) {
	if (cstr) {
		copy(cstr, static_cast<unsigned int>(strlen(cstr)));
	}
}

inline String::String(const char *cstr, unsigned int length)
	: buffer(NULL), capacity(0), len(0) {
	if (cstr) {
		copy(cstr, length);
	}
}

inline String::String(const uint8_t *cstr, unsigned int length)
	: String((const char *)cstr, length) {
}

inline String::String(const String &str)
	: buffer(NULL), capacity(0), len(0) {
	*this = str;
}

inline String::String(const __FlashStringHelper *str)
	: buffer(NULL), capacity(0), len(0) {
	*this = str;
}

inline String::String(String &&rval)
	: buffer(NULL), capacity(0), len(0) {
	move(rval);
}

inline String::String(char c)
	: buffer(NULL), capacity(0), len(0) {
	invalidateOnFailure(arduino_string_copy_char(&buffer, &capacity, &len, c));
}

inline String::String(unsigned char value, unsigned char base)
	: buffer(NULL), capacity(0), len(0) {
	invalidateOnFailure(arduino_string_copy_unsigned_char_base(&buffer, &capacity, &len, value, base));
}

inline String::String(int value, unsigned char base)
	: buffer(NULL), capacity(0), len(0) {
	invalidateOnFailure(arduino_string_copy_int_base(&buffer, &capacity, &len, value, base));
}

inline String::String(unsigned int value, unsigned char base)
	: buffer(NULL), capacity(0), len(0) {
	invalidateOnFailure(arduino_string_copy_unsigned_int_base(&buffer, &capacity, &len, value, base));
}

inline String::String(long value, unsigned char base)
	: buffer(NULL), capacity(0), len(0) {
	invalidateOnFailure(arduino_string_copy_long_base(&buffer, &capacity, &len, value, base));
}

inline String::String(unsigned long value, unsigned char base)
	: buffer(NULL), capacity(0), len(0) {
	invalidateOnFailure(arduino_string_copy_unsigned_long_base(&buffer, &capacity, &len, value, base));
}

inline String::String(float value, unsigned char decimalPlaces)
	: buffer(NULL), capacity(0), len(0) {
	invalidateOnFailure(arduino_string_copy_float_precision(&buffer, &capacity, &len, value, decimalPlaces));
}

inline String::String(double value, unsigned char decimalPlaces)
	: buffer(NULL), capacity(0), len(0) {
	invalidateOnFailure(arduino_string_copy_double_precision(&buffer, &capacity, &len, value, decimalPlaces));
}

inline String::~String(void) {
	arduino_string_free(&buffer, &capacity, &len);
}

inline bool String::reserve(unsigned int size) {
	if (buffer && capacity >= size) {
		return true;
	}
	if (changeBuffer(size)) {
		if (len == 0) {
			buffer[0] = 0;
		}
		return true;
	}
	return false;
}

inline unsigned int String::length(void) const {
	return len;
}

inline bool String::isEmpty(void) const {
	return length() == 0;
}

inline String &String::operator=(const String &rhs) {
	if (this == &rhs) {
		return *this;
	}
	if (rhs.buffer) {
		copy(rhs.buffer, rhs.len);
	} else {
		invalidate();
	}
	return *this;
}

inline String &String::operator=(const char *cstr) {
	if (cstr) {
		copy(cstr, static_cast<unsigned int>(strlen(cstr)));
	} else {
		invalidate();
	}
	return *this;
}

inline String &String::operator=(const __FlashStringHelper *str) {
	if (str) {
		copy(str, static_cast<unsigned int>(strlen((const char *)str)));
	} else {
		invalidate();
	}
	return *this;
}

inline String &String::operator=(String &&rval) {
	move(rval);
	return *this;
}

inline bool String::concat(const String &str) {
	return arduino_string_concat_bytes(&buffer, &capacity, &len, str.buffer, str.len);
}

inline bool String::concat(const char *cstr) {
	return arduino_string_concat_bytes(
		&buffer, &capacity, &len, cstr, cstr ? static_cast<unsigned int>(strlen(cstr)) : 0);
}

inline bool String::concat(const char *cstr, unsigned int length) {
	return arduino_string_concat_bytes(&buffer, &capacity, &len, cstr, length);
}

inline bool String::concat(const uint8_t *cstr, unsigned int length) {
	return arduino_string_concat_bytes(&buffer, &capacity, &len, reinterpret_cast<const char *>(cstr), length);
}

inline bool String::concat(char c) {
	return arduino_string_concat_bytes(&buffer, &capacity, &len, reinterpret_cast<const char *>(&c), 1);
}

inline bool String::concat(unsigned char num) {
	return arduino_string_concat_unsigned_char(&buffer, &capacity, &len, num);
}

inline bool String::concat(int num) {
	return arduino_string_concat_int(&buffer, &capacity, &len, num);
}

inline bool String::concat(unsigned int num) {
	return arduino_string_concat_unsigned_int(&buffer, &capacity, &len, num);
}

inline bool String::concat(long num) {
	return arduino_string_concat_long(&buffer, &capacity, &len, num);
}

inline bool String::concat(unsigned long num) {
	return arduino_string_concat_unsigned_long(&buffer, &capacity, &len, num);
}

inline bool String::concat(float num) {
	return arduino_string_concat_float(&buffer, &capacity, &len, num);
}

inline bool String::concat(double num) {
	return arduino_string_concat_double(&buffer, &capacity, &len, num);
}

inline bool String::concat(const __FlashStringHelper *str) {
	if (!str) {
		return false;
	}
	const unsigned int length = static_cast<unsigned int>(strlen((const char *)str));
	if (length == 0) {
		return true;
	}
	return arduino_string_concat_bytes(&buffer, &capacity, &len, (const char *)str, length);
}

inline String &String::operator+=(const String &str) {
	(void)arduino_string_concat_bytes(&buffer, &capacity, &len, str.buffer, str.len);
	return *this;
}

inline String &String::operator+=(const char *cstr) {
	(void)arduino_string_concat_bytes(
		&buffer, &capacity, &len, cstr, cstr ? static_cast<unsigned int>(strlen(cstr)) : 0);
	return *this;
}

inline String &String::operator+=(char c) {
	(void)arduino_string_concat_bytes(&buffer, &capacity, &len, reinterpret_cast<const char *>(&c), 1);
	return *this;
}

inline String &String::operator+=(unsigned char num) {
	(void)arduino_string_concat_unsigned_char(&buffer, &capacity, &len, num);
	return *this;
}

inline String &String::operator+=(int num) {
	(void)arduino_string_concat_int(&buffer, &capacity, &len, num);
	return *this;
}

inline String &String::operator+=(unsigned int num) {
	(void)arduino_string_concat_unsigned_int(&buffer, &capacity, &len, num);
	return *this;
}

inline String &String::operator+=(long num) {
	(void)arduino_string_concat_long(&buffer, &capacity, &len, num);
	return *this;
}

inline String &String::operator+=(unsigned long num) {
	(void)arduino_string_concat_unsigned_long(&buffer, &capacity, &len, num);
	return *this;
}

inline String &String::operator+=(float num) {
	(void)arduino_string_concat_float(&buffer, &capacity, &len, num);
	return *this;
}

inline String &String::operator+=(double num) {
	(void)arduino_string_concat_double(&buffer, &capacity, &len, num);
	return *this;
}

inline String &String::operator+=(const __FlashStringHelper *str) {
	concat(str);
	return *this;
}

inline String::operator StringIfHelperType() const {
	return buffer ? &String::StringIfHelper : 0;
}

inline int String::compareTo(const String &s) const {
	return compareTo(s.buffer);
}

inline int String::compareTo(const char *cstr) const {
	return arduino_string_compare_cstr(buffer, len, cstr);
}

inline bool String::equals(const String &s) const {
	return arduino_string_equals_bytes(buffer, len, s.buffer, s.len);
}

inline bool String::equals(const char *cstr) const {
	return arduino_string_equals_cstr(buffer, len, cstr);
}

inline bool String::equalsIgnoreCase(const String &s) const {
	if (this == &s) {
		return true;
	}
	return arduino_string_equals_ignore_case(buffer, len, s.buffer, s.len);
}

inline bool String::startsWith(const String &prefix) const {
	return arduino_string_starts_with(buffer, len, prefix.buffer, prefix.len, 0);
}

inline bool String::startsWith(const String &prefix, unsigned int offset) const {
	return arduino_string_starts_with(buffer, len, prefix.buffer, prefix.len, offset);
}

inline bool String::endsWith(const String &suffix) const {
	return arduino_string_ends_with(buffer, len, suffix.buffer, suffix.len);
}

inline char String::charAt(unsigned int index) const {
	return operator[](index);
}

inline void String::setCharAt(unsigned int index, char c) {
	if (index < len && buffer) {
		buffer[index] = c;
	}
}

inline char String::operator[](unsigned int index) const {
	if (index >= len || !buffer) {
		return 0;
	}
	return buffer[index];
}

inline char &String::operator[](unsigned int index) {
	static char dummy_writable_char;
	if (index >= len || !buffer) {
		dummy_writable_char = 0;
		return dummy_writable_char;
	}
	return buffer[index];
}

inline void String::getBytes(unsigned char *buf, unsigned int bufsize, unsigned int index) const {
	arduino_string_get_bytes(buffer, len, buf, bufsize, index);
}

inline void String::toCharArray(char *buf, unsigned int bufsize, unsigned int index) const {
	getBytes(reinterpret_cast<unsigned char *>(buf), bufsize, index);
}

inline const char *String::c_str() const {
	return buffer;
}

inline char *String::begin() {
	return buffer;
}

inline char *String::end() {
	return buffer + length();
}

inline const char *String::begin() const {
	return c_str();
}

inline const char *String::end() const {
	return c_str() + length();
}

inline int String::indexOf(char ch) const {
	return arduino_string_index_of_char(buffer, len, ch, 0);
}

inline int String::indexOf(char ch, unsigned int fromIndex) const {
	return arduino_string_index_of_char(buffer, len, ch, fromIndex);
}

inline int String::indexOf(const String &str) const {
	return arduino_string_index_of_bytes(buffer, len, str.buffer, str.len, 0);
}

inline int String::indexOf(const String &str, unsigned int fromIndex) const {
	return arduino_string_index_of_bytes(buffer, len, str.buffer, str.len, fromIndex);
}

inline int String::lastIndexOf(char ch) const {
	return lastIndexOf(ch, len - 1);
}

inline int String::lastIndexOf(char ch, unsigned int fromIndex) const {
	return arduino_string_last_index_of_char(buffer, len, ch, fromIndex);
}

inline int String::lastIndexOf(const String &str) const {
	return lastIndexOf(str, len - str.len);
}

inline int String::lastIndexOf(const String &str, unsigned int fromIndex) const {
	return arduino_string_last_index_of_bytes(buffer, len, str.buffer, str.len, fromIndex);
}

inline String String::substring(unsigned int beginIndex) const {
	return substring(beginIndex, len);
}

inline String String::substring(unsigned int beginIndex, unsigned int endIndex) const {
	String out("");
	if (!arduino_string_copy_substring(buffer, len, beginIndex, endIndex, &out.buffer,
									   &out.capacity, &out.len)) {
		out.invalidate();
	}
	return out;
}

inline void String::replace(char find, char replace) {
	arduino_string_replace_char(buffer, len, find, replace);
}

inline void String::replace(const String &find, const String &replace) {
	(void)arduino_string_replace_bytes(&buffer, &capacity, &len, find.buffer, find.len,
									   replace.buffer, replace.len);
}

inline void String::remove(unsigned int index) {
	len = arduino_string_remove(buffer, len, index, static_cast<unsigned int>(-1));
}

inline void String::remove(unsigned int index, unsigned int count) {
	len = arduino_string_remove(buffer, len, index, count);
}

inline void String::toLowerCase(void) {
	if (!buffer) {
		return;
	}
	for (char *p = buffer; *p; ++p) {
		*p = static_cast<char>(tolower(static_cast<unsigned char>(*p)));
	}
}

inline void String::toUpperCase(void) {
	if (!buffer) {
		return;
	}
	for (char *p = buffer; *p; ++p) {
		*p = static_cast<char>(toupper(static_cast<unsigned char>(*p)));
	}
}

inline void String::trim(void) {
	if (!buffer || len == 0) {
		return;
	}

	char *begin = buffer;
	while (begin < buffer + len && isspace(static_cast<unsigned char>(*begin))) {
		++begin;
	}

	if (begin >= buffer + len) {
		len = 0;
		buffer[0] = 0;
		return;
	}

	char *end = buffer + len - 1;
	while (end > begin && isspace(static_cast<unsigned char>(*end))) {
		--end;
	}

	len = static_cast<unsigned int>(end + 1 - begin);
	if (begin > buffer) {
		memmove(buffer, begin, len);
	}
	buffer[len] = 0;
}

inline void String::reverse(void) {
	arduino_string_reverse(buffer, len);
}

inline long String::toInt(void) const {
	return buffer ? strtol(buffer, NULL, 10) : 0;
}

inline float String::toFloat(void) const {
	return static_cast<float>(toDouble());
}

inline double String::toDouble(void) const {
	return buffer ? strtod(buffer, NULL) : 0.0;
}

inline void String::invalidate(void) {
	arduino_string_free(&buffer, &capacity, &len);
}

inline void String::invalidateOnFailure(bool success) {
	if (!success) {
		invalidate();
	}
}

inline bool String::changeBuffer(unsigned int maxStrLen) {
	return arduino_string_change_buffer(&buffer, &capacity, &len, maxStrLen);
}

inline String &String::copy(const char *cstr, unsigned int length) {
	invalidateOnFailure(cstr && arduino_string_copy_bytes(&buffer, &capacity, &len, cstr, length));
	return *this;
}

inline String &String::copy(const __FlashStringHelper *pstr, unsigned int length) {
	invalidateOnFailure(
		pstr && arduino_string_copy_bytes(&buffer, &capacity, &len, (const char *)pstr, length));
	return *this;
}

inline void String::move(String &rhs) {
	if (this != &rhs) {
		arduino_string_free(&buffer, &capacity, &len);
		buffer = rhs.buffer;
		len = rhs.len;
		capacity = rhs.capacity;
		rhs.buffer = NULL;
		rhs.len = 0;
		rhs.capacity = 0;
	}
}

inline StringSumHelper::StringSumHelper(const String &s) : String(s) {
}

inline StringSumHelper::StringSumHelper(const char *p) : String(p) {
}

inline StringSumHelper::StringSumHelper(char c) : String(c) {
}

inline StringSumHelper::StringSumHelper(unsigned char num) : String(num) {
}

inline StringSumHelper::StringSumHelper(int num) : String(num) {
}

inline StringSumHelper::StringSumHelper(unsigned int num) : String(num) {
}

inline StringSumHelper::StringSumHelper(long num) : String(num) {
}

inline StringSumHelper::StringSumHelper(unsigned long num) : String(num) {
}

inline StringSumHelper::StringSumHelper(float num) : String(num) {
}

inline StringSumHelper::StringSumHelper(double num) : String(num) {
}

inline StringSumHelper &operator+(const StringSumHelper &lhs, const String &rhs) {
	StringSumHelper &a = const_cast<StringSumHelper &>(lhs);
	a.invalidateOnFailure(arduino_string_concat_bytes(&a.buffer, &a.capacity, &a.len, rhs.buffer, rhs.len));
	return a;
}

inline StringSumHelper &operator+(const StringSumHelper &lhs, const char *cstr) {
	StringSumHelper &a = const_cast<StringSumHelper &>(lhs);
	a.invalidateOnFailure(arduino_string_concat_bytes(
		&a.buffer, &a.capacity, &a.len, cstr, cstr ? static_cast<unsigned int>(strlen(cstr)) : 0));
	return a;
}

inline StringSumHelper &operator+(const StringSumHelper &lhs, char c) {
	StringSumHelper &a = const_cast<StringSumHelper &>(lhs);
	a.invalidateOnFailure(arduino_string_concat_bytes(
		&a.buffer, &a.capacity, &a.len, reinterpret_cast<const char *>(&c), 1));
	return a;
}

inline StringSumHelper &operator+(const StringSumHelper &lhs, unsigned char num) {
	StringSumHelper &a = const_cast<StringSumHelper &>(lhs);
	a.invalidateOnFailure(arduino_string_concat_unsigned_char(&a.buffer, &a.capacity, &a.len, num));
	return a;
}

inline StringSumHelper &operator+(const StringSumHelper &lhs, int num) {
	StringSumHelper &a = const_cast<StringSumHelper &>(lhs);
	a.invalidateOnFailure(arduino_string_concat_int(&a.buffer, &a.capacity, &a.len, num));
	return a;
}

inline StringSumHelper &operator+(const StringSumHelper &lhs, unsigned int num) {
	StringSumHelper &a = const_cast<StringSumHelper &>(lhs);
	a.invalidateOnFailure(arduino_string_concat_unsigned_int(&a.buffer, &a.capacity, &a.len, num));
	return a;
}

inline StringSumHelper &operator+(const StringSumHelper &lhs, long num) {
	StringSumHelper &a = const_cast<StringSumHelper &>(lhs);
	a.invalidateOnFailure(arduino_string_concat_long(&a.buffer, &a.capacity, &a.len, num));
	return a;
}

inline StringSumHelper &operator+(const StringSumHelper &lhs, unsigned long num) {
	StringSumHelper &a = const_cast<StringSumHelper &>(lhs);
	a.invalidateOnFailure(arduino_string_concat_unsigned_long(&a.buffer, &a.capacity, &a.len, num));
	return a;
}

inline StringSumHelper &operator+(const StringSumHelper &lhs, float num) {
	StringSumHelper &a = const_cast<StringSumHelper &>(lhs);
	a.invalidateOnFailure(arduino_string_concat_float(&a.buffer, &a.capacity, &a.len, num));
	return a;
}

inline StringSumHelper &operator+(const StringSumHelper &lhs, double num) {
	StringSumHelper &a = const_cast<StringSumHelper &>(lhs);
	a.invalidateOnFailure(arduino_string_concat_double(&a.buffer, &a.capacity, &a.len, num));
	return a;
}

inline StringSumHelper &operator+(const StringSumHelper &lhs, const __FlashStringHelper *rhs) {
	StringSumHelper &a = const_cast<StringSumHelper &>(lhs);
	a.invalidateOnFailure(arduino_string_concat_bytes(
		&a.buffer,
		&a.capacity,
		&a.len,
		(const char *)rhs,
		rhs ? static_cast<unsigned int>(strlen((const char *)rhs)) : 0));
	return a;
}

inline bool operator==(const String &a, const String &b) {
	return arduino_string_equals_bytes(a.buffer, a.len, b.buffer, b.len);
}

inline bool operator==(const String &a, const char *b) {
	return arduino_string_equals_cstr(a.buffer, a.len, b);
}

inline bool operator==(const char *a, const String &b) {
	return arduino_string_equals_cstr(b.buffer, b.len, a);
}

inline bool operator<(const String &a, const String &b) {
	return arduino_string_compare_cstr(a.buffer, a.len, b.buffer) < 0;
}

inline bool operator<(const String &a, const char *b) {
	return arduino_string_compare_cstr(a.buffer, a.len, b) < 0;
}

inline bool operator<(const char *a, const String &b) {
	return arduino_string_compare_cstr(b.buffer, b.len, a) > 0;
}

inline bool operator!=(const String &a, const String &b) {
	return !arduino_string_equals_bytes(a.buffer, a.len, b.buffer, b.len);
}

inline bool operator!=(const String &a, const char *b) {
	return !arduino_string_equals_cstr(a.buffer, a.len, b);
}

inline bool operator!=(const char *a, const String &b) {
	return !arduino_string_equals_cstr(b.buffer, b.len, a);
}

inline bool operator>(const String &a, const String &b) {
	return arduino_string_compare_cstr(a.buffer, a.len, b.buffer) > 0;
}

inline bool operator>(const String &a, const char *b) {
	return arduino_string_compare_cstr(a.buffer, a.len, b) > 0;
}

inline bool operator>(const char *a, const String &b) {
	return arduino_string_compare_cstr(b.buffer, b.len, a) < 0;
}

inline bool operator<=(const String &a, const String &b) {
	return arduino_string_compare_cstr(a.buffer, a.len, b.buffer) <= 0;
}

inline bool operator<=(const String &a, const char *b) {
	return arduino_string_compare_cstr(a.buffer, a.len, b) <= 0;
}

inline bool operator<=(const char *a, const String &b) {
	return arduino_string_compare_cstr(b.buffer, b.len, a) >= 0;
}

inline bool operator>=(const String &a, const String &b) {
	return arduino_string_compare_cstr(a.buffer, a.len, b.buffer) >= 0;
}

inline bool operator>=(const String &a, const char *b) {
	return arduino_string_compare_cstr(a.buffer, a.len, b) >= 0;
}

inline bool operator>=(const char *a, const String &b) {
	return arduino_string_compare_cstr(b.buffer, b.len, a) <= 0;
}

} // namespace arduino
