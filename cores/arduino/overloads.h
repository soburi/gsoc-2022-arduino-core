/*
 * Copyright (c) Arduino s.r.l. and/or its affiliated companies
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#pragma once

#ifdef CONFIG_DAC

void analogWrite(enum dacPins pinNumber, int value);

#endif

// In c++ mode, we also provide analogReadResolution and analogWriteResolution getters
#if defined(CONFIG_ADC)
int analogReadResolution();
#endif

#if defined(CONFIG_DAC) || defined(CONFIG_PWM)
int analogWriteResolution();
#endif
