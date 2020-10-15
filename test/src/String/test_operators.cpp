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

TEST_CASE ("Testing String::operator + (const StringSumHelper, const String)", "[String-operator+-01]")
{
  arduino::String str1("Hello ");
  arduino::String str2("Arduino");
  arduino::String str("Hello Arduino");
  REQUIRE(str.compareTo(str1+str2) == 0);
}

TEST_CASE ("Testing String::operator + (const StringSumHelper, const char *)", "[String-operator+-02]")
{
  arduino::String str1("Hello ");
  arduino::String str("Hello Arduino");
  REQUIRE(str.compareTo(str1+"Arduino") == 0);
}

TEST_CASE ("Testing String::operator + (const StringSumHelper, char)", "[String-operator+-03]")
{
  arduino::String str1("Hello");
  char ch='!';
  arduino::String str("Hello!");
  REQUIRE(str.compareTo(str1+ch) == 0);
}

TEST_CASE ("Testing String::operator + (const StringSumHelper, unsigned char)", "[String-operator+-04]")
{
  arduino::String str1("Hello ");
  unsigned char ch='A';
  arduino::String str("Hello 65"); /* ASCII['A'] = 65 */
  REQUIRE(str.compareTo(str1+ch) == 0);
}

TEST_CASE ("Testing String::operator + (const StringSumHelper, int)", "[String-operator+-05]")
{
  arduino::String str1("Hello ");
  arduino::String str("Hello 1");
  REQUIRE(str.compareTo(str1+1) == 0);
}

TEST_CASE ("Testing String::operator + (unsigned int)", "[String-operator+-06]")
{
  arduino::String str1("Hello ");
  unsigned int const num = 1;
  arduino::String str("Hello 1");
  REQUIRE(str.compareTo(str1+num) == 0);
}

TEST_CASE ("Testing String::operator + (long)", "[String-operator+-07]")
{
  arduino::String str1("Hello ");
  long const num = -1;
  arduino::String str("Hello -1");
  REQUIRE(str.compareTo(str1+num) == 0);
}

TEST_CASE ("Testing String::operator + (unsigned long)", "[String-operator+-08]")
{
  arduino::String str1("Hello ");
  unsigned long const num = 1;
  arduino::String str("Hello 1");
  REQUIRE(str.compareTo(str1+num) == 0);
}

TEST_CASE ("Testing String::operator + (float)", "[String-operator+-09]")
{
  arduino::String str1("Hello ");
  float const num = 1.234f;
  arduino::String str("Hello 1.23");
  REQUIRE(str.compareTo(str1+num) == 0);
}

TEST_CASE ("Testing String::operator + (double)", "[String-operator+-10]")
{
  arduino::String str1("Hello ");
  double const num = 5.678;
  arduino::String str("Hello 5.68");
  REQUIRE(str.compareTo(str1+num) == 0);
}

TEST_CASE ("Testing String::operator + (const __FlashStringHelper *)", "[String-operator+-11]")
{
#undef F
#define F(string_literal) (reinterpret_cast<const arduino::__FlashStringHelper *>(PSTR(string_literal)))
  arduino::String str1("Hello ");
  arduino::String str("Hello Arduino");
  REQUIRE(str.compareTo(str1+F("Arduino")) == 0);
}