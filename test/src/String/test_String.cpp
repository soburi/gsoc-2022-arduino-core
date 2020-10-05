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

TEST_CASE ("Testing String(char) constructor()", "[String-Ctor-03]")
{
  char const ch = 'A';
  arduino::String str(ch);
  REQUIRE(strcmp(str.c_str(), "A") == 0);
}

TEST_CASE ("Testing String(int, unsigned char base = 10) constructor()", "[String-Ctor-04]")
{
  int const val = -1;
  arduino::String str(val);
  REQUIRE(strcmp(str.c_str(), "-1") == 0);
}

TEST_CASE ("Testing String(unsigned int, unsigned char base = 10) constructor()", "[String-Ctor-05]")
{
  unsigned int const val = 1;
  arduino::String str(val);
  REQUIRE(strcmp(str.c_str(), "1") == 0);
}

TEST_CASE ("Testing String(long, unsigned char base = 10) constructor()", "[String-Ctor-06]")
{
  long const val = -1;
  arduino::String str(val);
  REQUIRE(strcmp(str.c_str(), "-1") == 0);
}

TEST_CASE ("Testing String(unsigned long, unsigned char base = 10) constructor()", "[String-Ctor-06]")
{
  unsigned long const val = 1;
  arduino::String str(val);
  REQUIRE(strcmp(str.c_str(), "1") == 0);
}

TEST_CASE ("Testing String(float, unsigned char decimalPlaces = 2) constructor()", "[String-Ctor-07]")
{
  float const val = 1.234f;
  arduino::String str(val);
  REQUIRE(strcmp(str.c_str(), "1.23") == 0);
}

TEST_CASE ("Testing String(double, unsigned char decimalPlaces = 2) constructor()", "[String-Ctor-08]")
{
  double const val = 5.678;
  arduino::String str(val);
  REQUIRE(strcmp(str.c_str(), "5.68") == 0);
}
