/*
 * Copyright (c) 2020 Arduino.  All rights reserved.
 */

/**************************************************************************************
 * INCLUDE
 **************************************************************************************/

#include <catch.hpp>

#include <String.h>

/**************************************************************************************
 * TEST CODE
 **************************************************************************************/

TEST_CASE ("Testing String(const char *) constructor()", "[String-Ctor-01]")
{
  char const CSTR[] = "Hello Arduino String Class";
  arduino::String str(CSTR);
  REQUIRE(strcmp(CSTR, str.c_str()) == 0);
}

TEST_CASE ("Testing String(const String &) constructor()", "[String-Ctor-02]")
{
  arduino::String str1("Hello Arduino String class"),
                  str2(str1);
  REQUIRE(strcmp(str1.c_str(), str2.c_str()) == 0);
}

TEST_CASE ("Testing String(const __FlashStringHelper) constructor()", "[String-Ctor-03]")
{
#undef F
#define F(string_literal) (reinterpret_cast<const arduino::__FlashStringHelper *>(PSTR(string_literal)))
  arduino::String str1(F("Hello"));
  REQUIRE(str1.compareTo("Hello") == 0);
}

TEST_CASE ("Testing String(char) constructor()", "[String-Ctor-04]")
{
  char const ch = 'A';
  arduino::String str(ch);
  REQUIRE(strcmp(str.c_str(), "A") == 0);
}

TEST_CASE ("Testing String(unsigned char, unsigned char base = 10) constructor()", "[String-Ctor-05]")
{
  unsigned char const val = 1;
  arduino::String str(val);
  REQUIRE(strcmp(str.c_str(), "1") == 0);
}

TEST_CASE ("Testing String(int, unsigned char base = 10) constructor()", "[String-Ctor-06]")
{
  int const val = -1;
  arduino::String str(val);
  REQUIRE(strcmp(str.c_str(), "-1") == 0);
}

TEST_CASE ("Testing String(unsigned int, unsigned char base = 10) constructor()", "[String-Ctor-07]")
{
  unsigned int const val = 1;
  arduino::String str(val);
  REQUIRE(strcmp(str.c_str(), "1") == 0);
}

TEST_CASE ("Testing String(long, unsigned char base = 10) constructor()", "[String-Ctor-08]")
{
  long const val = -1;
  arduino::String str(val);
  REQUIRE(strcmp(str.c_str(), "-1") == 0);
}

TEST_CASE ("Testing String(unsigned long, unsigned char base = 10) constructor()", "[String-Ctor-09]")
{
  unsigned long const val = 1;
  arduino::String str(val);
  REQUIRE(strcmp(str.c_str(), "1") == 0);
}

TEST_CASE ("Testing String(float, unsigned char decimalPlaces = 2) constructor()", "[String-Ctor-10]")
{
  float const val = 1.234f;
  arduino::String str(val);
  REQUIRE(strcmp(str.c_str(), "1.23") == 0);
}

TEST_CASE ("Testing String(double, unsigned char decimalPlaces = 2) constructor()", "[String-Ctor-11]")
{
  double const val = 5.678;
  arduino::String str(val);
  REQUIRE(strcmp(str.c_str(), "5.68") == 0);
}

TEST_CASE ("Testing String(const __FlashStringHelper) constructor() with invalid buffer", "[String-Ctor-12]")
{
#undef F
#define F(string_literal) (reinterpret_cast<const arduino::__FlashStringHelper *>(PSTR(string_literal)))
  char *buffer = NULL;

  arduino::String str1(F(buffer));
  REQUIRE(str1.compareTo("Hello") == 0);
}

TEST_CASE ("Testing String(StringSumHelper &&) constructor()", "[String-Ctor-13]")
{
  arduino::String str("Hello");
  char const ch = '!';
  arduino::String str1(static_cast<arduino::StringSumHelper&&>(str+ch));
  REQUIRE(str1.compareTo("Hello!") == 0);
}

TEST_CASE ("Testing String(String &&) constructor()", "[String-Ctor-14]")
{
  arduino::String str("Hello");
  arduino::String str1(static_cast<arduino::String&&>(str));
  REQUIRE(str1.compareTo("Hello") == 0);
}

TEST_CASE ("Testing String(String &&) with move(String &rhs) to a valid buffer", "[String-Ctor-15]")
{
  arduino::String str("Hello");
  arduino::String str1("Arduino");
  str1 = static_cast<arduino::String&&>(str);
  REQUIRE(str1.compareTo("Hello") == 0);
}