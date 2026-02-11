/*
 * Copyright (c) 2022 Dhruva Gole
 * Copyright (c) 2026 TOKITA Hiroshi
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#pragma once

#include "api/ArduinoAPI.h"

#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/pwm.h>
#include <zephyr/drivers/adc.h>
#include <zephyr/drivers/i2c.h>

#if DT_NODE_HAS_PROP(DT_PATH(zephyr_user), digital_pin_gpios)

#define DIGITAL_PIN_EXISTS(n, p, i, dev, num)                                                      \
	(((dev == DT_REG_ADDR(DT_PHANDLE_BY_IDX(n, p, i))) &&                                      \
	  (num == DT_PHA_BY_IDX(n, p, i, pin)))                                                    \
		 ? 1                                                                               \
		 : 0)

/* Check all pins are defined only once */
#define DIGITAL_PIN_CHECK_UNIQUE(i, _)                                                             \
	((DT_FOREACH_PROP_ELEM_SEP_VARGS(                                                          \
		 DT_PATH(zephyr_user), digital_pin_gpios, DIGITAL_PIN_EXISTS, (+),                 \
		 DT_REG_ADDR(DT_PHANDLE_BY_IDX(DT_PATH(zephyr_user), digital_pin_gpios, i)),       \
		 DT_PHA_BY_IDX(DT_PATH(zephyr_user), digital_pin_gpios, i, pin))) == 1)

#if !LISTIFY(DT_PROP_LEN(DT_PATH(zephyr_user), digital_pin_gpios), DIGITAL_PIN_CHECK_UNIQUE, (&&))
#error "digital_pin_gpios has duplicate definition"
#endif

#undef DIGITAL_PIN_CHECK_UNIQUE

/* Return the index of it if matched, oterwise return 0 */
#define LED_BUILTIN_INDEX_BY_REG_AND_PINNUM(n, p, i, dev, num)                                     \
	(DIGITAL_PIN_EXISTS(n, p, i, dev, num) ? i : 0)

/* Only matched pin returns non-zero value, so the sum is matched pin's index */
#define DIGITAL_PIN_GPIOS_FIND_PIN(dev, pin)                                                     \
	DT_FOREACH_PROP_ELEM_SEP_VARGS(DT_PATH(zephyr_user), digital_pin_gpios,                    \
				       LED_BUILTIN_INDEX_BY_REG_AND_PINNUM, (+), dev, pin)

#if DT_NODE_HAS_PROP(DT_PATH(zephyr_user), builtin_led_gpios) &&                                   \
	(DT_PROP_LEN(DT_PATH(zephyr_user), builtin_led_gpios) > 0)

#if !(DT_FOREACH_PROP_ELEM_SEP_VARGS(                                                               \
	     DT_PATH(zephyr_user), digital_pin_gpios, DIGITAL_PIN_EXISTS, (+),                     \
	     DT_REG_ADDR(DT_PHANDLE_BY_IDX(DT_PATH(zephyr_user), builtin_led_gpios, 0)),           \
	     DT_PHA_BY_IDX(DT_PATH(zephyr_user), builtin_led_gpios, 0, pin)) > 0)
#warning "pin not found in digital_pin_gpios"
#else
#define ZARD_LED_BUILTIN                                                                           \
	DIGITAL_PIN_GPIOS_FIND_PIN(                                                                    \
		DT_REG_ADDR(DT_PHANDLE_BY_IDX(DT_PATH(zephyr_user), builtin_led_gpios, 0)),                \
		DT_PHA_BY_IDX(DT_PATH(zephyr_user), builtin_led_gpios, 0, pin))
#endif

/* If digital-pin-gpios is not defined, tries to use the led0 alias */
#elif DT_NODE_EXISTS(DT_ALIAS(led0))

#if !(DT_FOREACH_PROP_ELEM_SEP_VARGS(DT_PATH(zephyr_user), digital_pin_gpios, DIGITAL_PIN_EXISTS,   \
				    (+), DT_REG_ADDR(DT_PHANDLE_BY_IDX(DT_ALIAS(led0), gpios, 0)), \
				    DT_PHA_BY_IDX(DT_ALIAS(led0), gpios, 0, pin)) > 0)
#warning "pin not found in digital_pin_gpios"
#else
#define ZARD_LED_BUILTIN                                                                           \
	DIGITAL_PIN_GPIOS_FIND_PIN(DT_REG_ADDR(DT_PHANDLE_BY_IDX(DT_ALIAS(led0), gpios, 0)),           \
							   DT_PHA_BY_IDX(DT_ALIAS(led0), gpios, 0, pin))
#endif

#endif // builtin_led_gpios

#define DN_ENUMS(n, p, i) D##i = i

#else

#if DT_NODE_EXISTS(DT_NODELABEL(arduino_header))
#if DT_NODE_HAS_COMPAT(DT_NODELABEL(arduino_header), arduino_header_r3)
#define ZARD_CONNECTOR arduino_header

#define ZARD_ARDUINO_HEADER_R3_PIN_NAME_A_0 A0
#define ZARD_ARDUINO_HEADER_R3_PIN_NAME_A_1 A1
#define ZARD_ARDUINO_HEADER_R3_PIN_NAME_A_2 A2
#define ZARD_ARDUINO_HEADER_R3_PIN_NAME_A_3 A3
#define ZARD_ARDUINO_HEADER_R3_PIN_NAME_A_4 A4
#define ZARD_ARDUINO_HEADER_R3_PIN_NAME_A_5 A5

#define ZARD_ARDUINO_HEADER_R3_PIN_NAME_D_6 D0
#define ZARD_ARDUINO_HEADER_R3_PIN_NAME_D_7 D1
#define ZARD_ARDUINO_HEADER_R3_PIN_NAME_D_8 D2
#define ZARD_ARDUINO_HEADER_R3_PIN_NAME_D_9 D3
#define ZARD_ARDUINO_HEADER_R3_PIN_NAME_D_10 D4
#define ZARD_ARDUINO_HEADER_R3_PIN_NAME_D_11 D5
#define ZARD_ARDUINO_HEADER_R3_PIN_NAME_D_12 D6
#define ZARD_ARDUINO_HEADER_R3_PIN_NAME_D_13 D7
#define ZARD_ARDUINO_HEADER_R3_PIN_NAME_D_14 D8
#define ZARD_ARDUINO_HEADER_R3_PIN_NAME_D_15 D9
#define ZARD_ARDUINO_HEADER_R3_PIN_NAME_D_16 D10
#define ZARD_ARDUINO_HEADER_R3_PIN_NAME_D_17 D11
#define ZARD_ARDUINO_HEADER_R3_PIN_NAME_D_18 D12
#define ZARD_ARDUINO_HEADER_R3_PIN_NAME_D_19 D13
#define ZARD_ARDUINO_HEADER_R3_PIN_NAME_D_20 D14
#define ZARD_ARDUINO_HEADER_R3_PIN_NAME_D_21 D15

#define ZARD_ARDUINO_HEADER_R3_IS_ANALOG_0 1
#define ZARD_ARDUINO_HEADER_R3_IS_ANALOG_1 1
#define ZARD_ARDUINO_HEADER_R3_IS_ANALOG_2 1
#define ZARD_ARDUINO_HEADER_R3_IS_ANALOG_3 1
#define ZARD_ARDUINO_HEADER_R3_IS_ANALOG_4 1
#define ZARD_ARDUINO_HEADER_R3_IS_ANALOG_5 1
#define ZARD_ARDUINO_HEADER_R3_IS_DIGITAL_6 1
#define ZARD_ARDUINO_HEADER_R3_IS_DIGITAL_7 1
#define ZARD_ARDUINO_HEADER_R3_IS_DIGITAL_8 1
#define ZARD_ARDUINO_HEADER_R3_IS_DIGITAL_9 1
#define ZARD_ARDUINO_HEADER_R3_IS_DIGITAL_10 1
#define ZARD_ARDUINO_HEADER_R3_IS_DIGITAL_11 1
#define ZARD_ARDUINO_HEADER_R3_IS_DIGITAL_12 1
#define ZARD_ARDUINO_HEADER_R3_IS_DIGITAL_13 1
#define ZARD_ARDUINO_HEADER_R3_IS_DIGITAL_14 1
#define ZARD_ARDUINO_HEADER_R3_IS_DIGITAL_15 1
#define ZARD_ARDUINO_HEADER_R3_IS_DIGITAL_16 1
#define ZARD_ARDUINO_HEADER_R3_IS_DIGITAL_17 1
#define ZARD_ARDUINO_HEADER_R3_IS_DIGITAL_18 1
#define ZARD_ARDUINO_HEADER_R3_IS_DIGITAL_19 1
#define ZARD_ARDUINO_HEADER_R3_IS_DIGITAL_20 1
#define ZARD_ARDUINO_HEADER_R3_IS_DIGITAL_21 1

#else
#error "Only arduino-header-r3 connector is supported"
#endif
#endif

#if DT_NODE_EXISTS(DT_NODELABEL(arduino_adc))
#define ZARD_ADC_CONNECTOR arduino_adc
#endif

#if DT_NODE_EXISTS(DT_NODELABEL(arduino_pwm))
#define ZARD_PWM_CONNECTOR arduino_pwm
#endif

#define ZARD_CONNECTOR_PIN_IS_DIGITAL(node, num)                                                   \
	UTIL_CAT(UTIL_CAT(ZARD_, UTIL_CAT(                                                         \
	                  DT_STRING_UPPER_TOKEN_BY_IDX(node, compatible, 0), _IS_DIGITAL_)), num)

#define ZARD_CONNECTOR_PIN_IS_ANALOG(node, num)                                                    \
	UTIL_CAT(UTIL_CAT(ZARD_, UTIL_CAT(                                                         \
	                  DT_STRING_UPPER_TOKEN_BY_IDX(node, compatible, 0), _IS_ANALOG_)), num)

#define ZARD_CONNECTOR_PIN_NAME_D(node, num)                                                       \
	UTIL_CAT(UTIL_CAT(ZARD_, UTIL_CAT(                                                         \
		 DT_STRING_UPPER_TOKEN_BY_IDX(node, compatible, 0), _PIN_NAME_D_)), num)

#define ZARD_CONNECTOR_PIN_NAME_A(node, num)                                                       \
	UTIL_CAT(UTIL_CAT(ZARD_, UTIL_CAT(                                                         \
		 DT_STRING_UPPER_TOKEN_BY_IDX(node, compatible, 0), _PIN_NAME_A_)), num)

#define ZARD_CHECK_GPIO_CTLR(node_id)                                                              \
        COND_CODE_1(DT_NODE_HAS_PROP(node_id, gpio_controller), (node_id,), ())

#define ZARD_ALL_GPIO_CTLR DT_FOREACH_NODE(ZARD_CHECK_GPIO_CTLR)

#define ZARD_IDX_IF_MATCH(i, n)                                                                    \
	COND_CODE_1(DT_SAME_NODE(n, GET_ARG_N(UTIL_INC(i), ZARD_ALL_GPIO_CTLR)), (i), ())

#define ZARD_MATCH_IDX(n)                                                                          \
	LISTIFY(NUM_VA_ARGS_LESS_1(ZARD_ALL_GPIO_CTLR), ZARD_IDX_IF_MATCH, (), n)

#define ZARD_GET_NGPIOS(i, ...) DT_PROP(GET_ARG_N(UTIL_INC(i), __VA_ARGS__), ngpios)
#define ZARD_SUM_NGPIOS(...)                                                                       \
	LISTIFY(NUM_VA_ARGS(__VA_ARGS__), ZARD_GET_NGPIOS, (+), __VA_ARGS__)

#define ZARD_GLOBAL_GPIO_OFFSET_(ph)                                                               \
	ZARD_SUM_NGPIOS(GET_ARGS_FIRST_N(ZARD_MATCH_IDX(ph), ZARD_ALL_GPIO_CTLR))

#define ZARD_GLOBAL_GPIO_OFFSET(ph)                                                                \
	COND_CODE_1(IS_EQ(NUM_VA_ARGS(ZARD_GLOBAL_GPIO_OFFSET_(ph)), 0),                           \
					     (0), (ZARD_GLOBAL_GPIO_OFFSET_(ph)))


#define ZARD_CONN_DN_ENUMS(n, p, i)                                                                \
	COND_CODE_1(ZARD_CONNECTOR_PIN_IS_DIGITAL(DT_NODELABEL(ZARD_CONNECTOR),                    \
		     DT_MAP_ENTRY_CHILD_SPECIFIER_BY_IDX(n, p, i, 0)),                             \
		    (ZARD_CONNECTOR_PIN_NAME_D(DT_NODELABEL(ZARD_CONNECTOR),                       \
		     DT_MAP_ENTRY_CHILD_SPECIFIER_BY_IDX(n, p, i, 0)) =                            \
	             ZARD_GLOBAL_GPIO_OFFSET(DT_MAP_ENTRY_PARENT_BY_IDX(n, p, i)) +                \
		     DT_MAP_ENTRY_PARENT_SPECIFIER_BY_IDX(n, p, i, 0),), ())

#define ZARD_CONN_AN_ENUMS(n, p, i)                                                                \
	COND_CODE_1(ZARD_CONNECTOR_PIN_IS_ANALOG(DT_NODELABEL(ZARD_CONNECTOR),                     \
		     DT_MAP_ENTRY_CHILD_SPECIFIER_BY_IDX(n, p, i, 0)),                             \
		    (ZARD_CONNECTOR_PIN_NAME_A(DT_NODELABEL(ZARD_CONNECTOR),                       \
		     DT_MAP_ENTRY_CHILD_SPECIFIER_BY_IDX(n, p, i, 0)) =                            \
	             ZARD_GLOBAL_GPIO_OFFSET(DT_MAP_ENTRY_PARENT_BY_IDX(n, p, i)) +                \
		     DT_MAP_ENTRY_PARENT_SPECIFIER_BY_IDX(n, p, i, 0),), ())

#if DT_NODE_HAS_PROP(DT_PATH(zephyr_user), builtin_led_gpios) &&                                   \
	(DT_PROP_LEN(DT_PATH(zephyr_user), builtin_led_gpios) > 0)
#define ZARD_LED_BUILTIN                                                                           \
	ZARD_GLOBAL_GPIO_OFFSET(DT_PHANDLE_BY_IDX(DT_PATH(zephyr_user), builtin_led_gpios, 0)) +   \
		DT_PHA_BY_IDX(DT_PATH(zephyr_user), builtin_led_gpios, 0, pin)
#elif DT_NODE_EXISTS(DT_ALIAS(led0))
#define ZARD_LED_BUILTIN                                                                           \
	ZARD_GLOBAL_GPIO_OFFSET(DT_PHANDLE_BY_IDX(DT_ALIAS(led0), gpios, 0)) +                     \
		DT_PHA_BY_IDX(DT_ALIAS(led0), gpios, 0, pin)
#endif
#endif

/*
 * expand as
 * enum digitalPins { D0, D1, ... LED... NUM_OF_DIGITAL_PINS };
 */
enum digitalPins {
#if DT_PROP_LEN_OR(DT_PATH(zephyr_user), digital_pin_gpios, 0) > 0
	DT_FOREACH_PROP_ELEM_SEP(DT_PATH(zephyr_user), digital_pin_gpios, DN_ENUMS, (, )),
#elif defined(ZARD_CONNECTOR)
	DT_FOREACH_MAP_ENTRY(DT_NODELABEL(ZARD_CONNECTOR), gpio_map, ZARD_CONN_DN_ENUMS)
#endif
	NUM_OF_DIGITAL_PINS
};

#ifdef CONFIG_ADC

#define AN_ENUMS(n, p, i) A ## i = DIGITAL_PIN_GPIOS_FIND_PIN( \
		DT_REG_ADDR(DT_PHANDLE_BY_IDX(DT_PATH(zephyr_user), p, i)),        \
		DT_PHA_BY_IDX(DT_PATH(zephyr_user), p, i, pin)),
#define ZARD_AN_ENUM_GLOBAL(n, p, i) \
	ZARD_GLOBAL_GPIO_OFFSET(DT_PHANDLE_BY_IDX(n, p, i)) + DT_PHA_BY_IDX(n, p, i, pin)
enum analogPins {
#if DT_NODE_HAS_PROP(DT_PATH(zephyr_user), adc_pin_gpios)
#if DT_NODE_HAS_PROP(DT_PATH(zephyr_user), digital_pin_gpios)
	DT_FOREACH_PROP_ELEM(DT_PATH(zephyr_user), adc_pin_gpios, AN_ENUMS)
#else
	DT_FOREACH_PROP_ELEM(DT_PATH(zephyr_user), adc_pin_gpios, ZARD_AN_ENUM_GLOBAL)
#endif
#elif defined(ZARD_ADC_CONNECTOR)
	DT_FOREACH_MAP_ENTRY(DT_NODELABEL(ZARD_CONNECTOR), gpio_map, ZARD_CONN_AN_ENUMS)
#endif
	NUM_OF_ANALOG_PINS
};

#endif

void interrupts(void);
void noInterrupts(void);

int digitalPinToInterrupt(pin_size_t pin);

#include <variant.h>

#if !defined(LED_BUILTIN) && defined(ZARD_LED_BUILTIN)
#define LED_BUILTIN ZARD_LED_BUILTIN
#endif // LED_BUILTIN

#ifdef __cplusplus
#include <zephyrSerial.h>
#endif // __cplusplus
