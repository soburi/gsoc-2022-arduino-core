/*
 * Copyright (c) 2020 Arduino.  All rights reserved.
 */

#ifndef STREAM_MOCK_H_
#define STREAM_MOCK_H_

/**************************************************************************************
 * INCLUDE
 **************************************************************************************/

#include <sstream>

#include <Stream.h>

/**************************************************************************************
 * CLASS DECLARATION
 **************************************************************************************/

class StreamMock : public arduino::Stream
{
public:
  std::stringstream _ss;

  virtual size_t write(uint8_t ch) override { _ss << static_cast<char>(ch); return 1; }
  virtual int available() override { return _ss.gcount(); }
  virtual int read() override
  {
    char ch;
    _ss >> ch;
    return ch;
  }
  virtual int peek() override
  {
    char ch = _ss.peek();
    return ch;
  }
};

#endif /* STREAM_MOCK_H_ */
