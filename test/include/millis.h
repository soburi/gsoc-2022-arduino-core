/*
 * Copyright (c) 2020 Arduino.  All rights reserved.
 */

#ifndef MILLIS_H_
#define MILLIS_H_

/**************************************************************************************
 * INCLUDE
 **************************************************************************************/

#include <Common.h>

/**************************************************************************************
 * FUNCTION DECLARATION
 **************************************************************************************/

#ifdef __cplusplus
extern "C" {
#endif

void set_millis(unsigned long const val);

#ifdef __cplusplus
}
#endif

#endif /* MILLIS_H_ */