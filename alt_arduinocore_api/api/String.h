/*
  String library for Wiring & Arduino
  ...mostly rewritten by Paul Stoffregen...
  Copyright (c) 2009-10 Hernando Barragan.  All right reserved.
  Copyright 2011, Paul Stoffregen, paul@pjrc.com

  This library is free software; you can redistribute it and/or
  modify it under the terms of the GNU Lesser General Public
  License as published by the Free Software Foundation; either
  version 2.1 of the License, or (at your option) any later version.

  This library is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
  Lesser General Public License for more details.

  You should have received a copy of the GNU Lesser General Public
  License along with this library; if not, write to the Free Software
  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
*/

#ifdef __cplusplus

#ifndef __ARDUINO_STRINGS__
#define __ARDUINO_STRINGS__

#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <stdint.h>
#if defined(__AVR__)
#include "avr/pgmspace.h"
#else
#ifndef PSTR
#define PSTR(str) (str)
#endif
#ifndef strcpy_P
#define strcpy_P(dest, src) strcpy((dest), (src))
#endif
#endif

extern "C" {

void arduino_string_free(char **buffer, unsigned int *capacity, unsigned int *len);
bool arduino_string_change_buffer(
	char **buffer,
	unsigned int *capacity,
	unsigned int *len,
	unsigned int max_str_len);
bool arduino_string_copy_bytes(
	char **buffer,
	unsigned int *capacity,
	unsigned int *len,
	const char *src,
	unsigned int length);
bool arduino_string_copy_char(
	char **buffer,
	unsigned int *capacity,
	unsigned int *len,
	char value);
bool arduino_string_copy_unsigned_char_base(
	char **buffer,
	unsigned int *capacity,
	unsigned int *len,
	unsigned char value,
	unsigned char base);
bool arduino_string_copy_int_base(
	char **buffer,
	unsigned int *capacity,
	unsigned int *len,
	int value,
	unsigned char base);
bool arduino_string_copy_unsigned_int_base(
	char **buffer,
	unsigned int *capacity,
	unsigned int *len,
	unsigned int value,
	unsigned char base);
bool arduino_string_copy_long_base(
	char **buffer,
	unsigned int *capacity,
	unsigned int *len,
	long value,
	unsigned char base);
bool arduino_string_copy_unsigned_long_base(
	char **buffer,
	unsigned int *capacity,
	unsigned int *len,
	unsigned long value,
	unsigned char base);
bool arduino_string_copy_float_precision(
	char **buffer,
	unsigned int *capacity,
	unsigned int *len,
	float value,
	unsigned char decimal_places);
bool arduino_string_copy_double_precision(
	char **buffer,
	unsigned int *capacity,
	unsigned int *len,
	double value,
	unsigned char decimal_places);
bool arduino_string_concat_bytes(
	char **buffer,
	unsigned int *capacity,
	unsigned int *len,
	const char *src,
	unsigned int length);
bool arduino_string_concat_unsigned_char(
	char **buffer,
	unsigned int *capacity,
	unsigned int *len,
	unsigned char value);
bool arduino_string_concat_int(
	char **buffer,
	unsigned int *capacity,
	unsigned int *len,
	int value);
bool arduino_string_concat_unsigned_int(
	char **buffer,
	unsigned int *capacity,
	unsigned int *len,
	unsigned int value);
bool arduino_string_concat_long(
	char **buffer,
	unsigned int *capacity,
	unsigned int *len,
	long value);
bool arduino_string_concat_unsigned_long(
	char **buffer,
	unsigned int *capacity,
	unsigned int *len,
	unsigned long value);
bool arduino_string_concat_float(
	char **buffer,
	unsigned int *capacity,
	unsigned int *len,
	float value);
bool arduino_string_concat_double(
	char **buffer,
	unsigned int *capacity,
	unsigned int *len,
	double value);

int arduino_string_compare_cstr(const char *buffer, unsigned int len, const char *other);
bool arduino_string_equals_cstr(const char *buffer, unsigned int len, const char *other);
bool arduino_string_equals_bytes(
	const char *buffer,
	unsigned int len,
	const char *other,
	unsigned int other_len);
bool arduino_string_equals_ignore_case(
	const char *buffer,
	unsigned int len,
	const char *other,
	unsigned int other_len);
bool arduino_string_starts_with(
	const char *buffer,
	unsigned int len,
	const char *prefix,
	unsigned int prefix_len,
	unsigned int offset);
bool arduino_string_ends_with(
	const char *buffer,
	unsigned int len,
	const char *suffix,
	unsigned int suffix_len);
int arduino_string_index_of_char(const char *buffer, unsigned int len, char ch, unsigned int from_index);
int arduino_string_index_of_bytes(
	const char *buffer,
	unsigned int len,
	const char *pattern,
	unsigned int pattern_len,
	unsigned int from_index);
int arduino_string_last_index_of_char(
	const char *buffer,
	unsigned int len,
	char ch,
	unsigned int from_index);
int arduino_string_last_index_of_bytes(
	const char *buffer,
	unsigned int len,
	const char *pattern,
	unsigned int pattern_len,
	unsigned int from_index);
void arduino_string_replace_char(char *buffer, unsigned int len, char find_ch, char replace_ch);
bool arduino_string_replace_bytes(
	char **buffer,
	unsigned int *capacity,
	unsigned int *len,
	const char *find,
	unsigned int find_len,
	const char *replace,
	unsigned int replace_len);
unsigned int arduino_string_remove(char *buffer, unsigned int len, unsigned int index, unsigned int count);
void arduino_string_reverse(char *buffer, unsigned int len);
void arduino_string_get_bytes(
	const char *buffer,
	unsigned int len,
	unsigned char *out,
	unsigned int out_size,
	unsigned int index);
bool arduino_string_copy_substring(
	const char *src_buffer,
	unsigned int src_len,
	unsigned int left,
	unsigned int right,
	char **out_buffer,
	unsigned int *out_capacity,
	unsigned int *out_len);

}

namespace arduino {

// When compiling programs with this class, the following gcc parameters
// dramatically increase performance and memory (RAM) efficiency, typically
// with little or no increase in code size.
//     -felide-constructors
//     -std=c++0x

class __FlashStringHelper;
#define F(string_literal) (reinterpret_cast<const __FlashStringHelper *>(PSTR(string_literal)))

// An inherited class for holding the result of a concatenation.  These
// result objects are assumed to be writable by subsequent concatenations.
class StringSumHelper;

class String
{
	friend class StringSumHelper;
	typedef void (String::*StringIfHelperType)() const;
	void StringIfHelper() const;

	static size_t const FLT_MAX_DECIMAL_PLACES = 10;
	static size_t const DBL_MAX_DECIMAL_PLACES = FLT_MAX_DECIMAL_PLACES;

public:
	String(const char *cstr = "");
	String(const char *cstr, unsigned int length);
	String(const uint8_t *cstr, unsigned int length);
	String(const String &str);
	String(const __FlashStringHelper *str);
	String(String &&rval);
	explicit String(char c);
	explicit String(unsigned char, unsigned char base=10);
	explicit String(int, unsigned char base=10);
	explicit String(unsigned int, unsigned char base=10);
	explicit String(long, unsigned char base=10);
	explicit String(unsigned long, unsigned char base=10);
	explicit String(float, unsigned char decimalPlaces=2);
	explicit String(double, unsigned char decimalPlaces=2);
	~String(void);

	bool reserve(unsigned int size);
	unsigned int length(void) const;
	bool isEmpty(void) const;

	String & operator = (const String &rhs);
	String & operator = (const char *cstr);
	String & operator = (const __FlashStringHelper *str);
	String & operator = (String &&rval);

	bool concat(const String &str);
	bool concat(const char *cstr);
	bool concat(const char *cstr, unsigned int length);
	bool concat(const uint8_t *cstr, unsigned int length);
	bool concat(char c);
	bool concat(unsigned char num);
	bool concat(int num);
	bool concat(unsigned int num);
	bool concat(long num);
	bool concat(unsigned long num);
	bool concat(float num);
	bool concat(double num);
	bool concat(const __FlashStringHelper * str);

	String & operator += (const String &rhs);
	String & operator += (const char *cstr);
	String & operator += (char c);
	String & operator += (unsigned char num);
	String & operator += (int num);
	String & operator += (unsigned int num);
	String & operator += (long num);
	String & operator += (unsigned long num);
	String & operator += (float num);
	String & operator += (double num);
	String & operator += (const __FlashStringHelper *str);

	friend StringSumHelper & operator + (const StringSumHelper &lhs, const String &rhs);
	friend StringSumHelper & operator + (const StringSumHelper &lhs, const char *cstr);
	friend StringSumHelper & operator + (const StringSumHelper &lhs, char c);
	friend StringSumHelper & operator + (const StringSumHelper &lhs, unsigned char num);
	friend StringSumHelper & operator + (const StringSumHelper &lhs, int num);
	friend StringSumHelper & operator + (const StringSumHelper &lhs, unsigned int num);
	friend StringSumHelper & operator + (const StringSumHelper &lhs, long num);
	friend StringSumHelper & operator + (const StringSumHelper &lhs, unsigned long num);
	friend StringSumHelper & operator + (const StringSumHelper &lhs, float num);
	friend StringSumHelper & operator + (const StringSumHelper &lhs, double num);
	friend StringSumHelper & operator + (const StringSumHelper &lhs, const __FlashStringHelper *rhs);

	operator StringIfHelperType() const;
	int compareTo(const String &s) const;
	int compareTo(const char *cstr) const;
	bool equals(const String &s) const;
	bool equals(const char *cstr) const;

	friend bool operator == (const String &a, const String &b);
	friend bool operator == (const String &a, const char *b);
	friend bool operator == (const char *a, const String &b);
	friend bool operator <  (const String &a, const String &b);
	friend bool operator <  (const String &a, const char *b);
	friend bool operator <  (const char *a, const String &b);

	friend bool operator != (const String &a, const String &b);
	friend bool operator != (const String &a, const char *b);
	friend bool operator != (const char *a, const String &b);
	friend bool operator >  (const String &a, const String &b);
	friend bool operator >  (const String &a, const char *b);
	friend bool operator >  (const char *a, const String &b);
	friend bool operator <= (const String &a, const String &b);
	friend bool operator <= (const String &a, const char *b);
	friend bool operator <= (const char *a, const String &b);
	friend bool operator >= (const String &a, const String &b);
	friend bool operator >= (const String &a, const char *b);
	friend bool operator >= (const char *a, const String &b);

	bool equalsIgnoreCase(const String &s) const;
	bool startsWith(const String &prefix) const;
	bool startsWith(const String &prefix, unsigned int offset) const;
	bool endsWith(const String &suffix) const;

	char charAt(unsigned int index) const;
	void setCharAt(unsigned int index, char c);
	char operator [] (unsigned int index) const;
	char& operator [] (unsigned int index);
	void getBytes(unsigned char *buf, unsigned int bufsize, unsigned int index=0) const;
	void toCharArray(char *buf, unsigned int bufsize, unsigned int index=0) const;
	const char* c_str() const;
	char* begin();
	char* end();
	const char* begin() const;
	const char* end() const;

	int indexOf(char ch) const;
	int indexOf(char ch, unsigned int fromIndex) const;
	int indexOf(const String &str) const;
	int indexOf(const String &str, unsigned int fromIndex) const;
	int lastIndexOf(char ch) const;
	int lastIndexOf(char ch, unsigned int fromIndex) const;
	int lastIndexOf(const String &str) const;
	int lastIndexOf(const String &str, unsigned int fromIndex) const;
	String substring(unsigned int beginIndex) const;
	String substring(unsigned int beginIndex, unsigned int endIndex) const;

	void replace(char find, char replace);
	void replace(const String& find, const String& replace);
	void remove(unsigned int index);
	void remove(unsigned int index, unsigned int count);
	void toLowerCase(void);
	void toUpperCase(void);
	void trim(void);
	void reverse(void);

	long toInt(void) const;
	float toFloat(void) const;
	double toDouble(void) const;

protected:
	char *buffer;
	unsigned int capacity;
	unsigned int len;

protected:
	void invalidate(void);
	void invalidateOnFailure(bool success);
	bool changeBuffer(unsigned int maxStrLen);

	String & copy(const char *cstr, unsigned int length);
	String & copy(const __FlashStringHelper *pstr, unsigned int length);
	void move(String &rhs);
};

class StringSumHelper : public String
{
public:
	StringSumHelper(const String &s);
	StringSumHelper(const char *p);
	StringSumHelper(char c);
	StringSumHelper(unsigned char num);
	StringSumHelper(int num);
	StringSumHelper(unsigned int num);
	StringSumHelper(long num);
	StringSumHelper(unsigned long num);
	StringSumHelper(float num);
	StringSumHelper(double num);
};

} // namespace arduino

using arduino::__FlashStringHelper;
using arduino::String;

#include "String.inl"

#endif  // __cplusplus
#endif  // __ARDUINO_STRINGS__
