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

TEST_CASE ("Testing String::compareTo(const String &)", "[String-compareTo-01]")
{
  WHEN ("Strings are equal")
  {
    arduino::String str1("Hello"), str2("Hello");
    REQUIRE(str1.compareTo(str2) == 0);
  }

  WHEN ("str2 is empty")
  {
    arduino::String str1("Hello"), str2;
    REQUIRE(str1.compareTo(str2) == strcmp(str1.c_str(), str2.c_str()));
  }

  WHEN ("str1 is empty")
  {
    arduino::String str1, str2("Hello");
    REQUIRE(str1.compareTo(str2) == strcmp(str1.c_str(), str2.c_str()));
  }
}

TEST_CASE ("Testing String::compareTo(const char *)", "[String-compareTo-02]")
{
  WHEN ("Strings are equal")
  {
    arduino::String str("Hello");
    REQUIRE(str.compareTo("Hello") == 0);
  }

  WHEN ("Passed string is empty")
  {
    arduino::String str1("Hello"), str2("");
    REQUIRE(str1.compareTo("") == strcmp(str1.c_str(), str2.c_str()));
  }

  WHEN ("Passed string is compared with empty string")
  {
    arduino::String str1, str2("Hello");
    REQUIRE(str1.compareTo("Hello") == strcmp(str1.c_str(), str2.c_str()));
  }
}
