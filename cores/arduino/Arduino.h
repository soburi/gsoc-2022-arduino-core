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
#define ZARD_CONNECTOR arduino_header
#elif DT_NODE_EXISTS(DT_NODELABEL(arduino_mkr_header))
#define ZARD_CONNECTOR arduino_mkr_header
#elif DT_NODE_EXISTS(DT_NODELABEL(arduino_nano_header))
#define ZARD_CONNECTOR arduino_nano_header
#elif DT_NODE_EXISTS(DT_NODELABEL(pico_header))
#define ZARD_CONNECTOR pico_header
#elif DT_NODE_EXISTS(DT_NODELABEL(boosterpack_header))
#define ZARD_CONNECTOR boosterpack_header
#endif

#if DT_NODE_EXISTS(DT_NODELABEL(arduino_adc))
#define ZARD_ADC_CONNECTOR arduino_adc
#endif

#if DT_NODE_EXISTS(DT_NODELABEL(arduino_pwm))
#define ZARD_PWM_CONNECTOR arduino_pwm
#endif

#define ZARD_CHECK_GPIO_CTLR_OKAY(node_id)                                                         \
	COND_CODE_1(DT_NODE_HAS_STATUS_OKAY(node_id),                                                    \
        (COND_CODE_1(DT_NODE_HAS_PROP(node_id, gpio_controller), (node_id,), ())), ())

#define ZARD_ALL_OKAY_GPIO_CTLR                                                                    \
	GET_ARGS_FIRST_N(NUM_VA_ARGS_LESS_1(DT_FOREACH_NODE(ZARD_CHECK_GPIO_CTLR_OKAY)),               \
					 DT_FOREACH_NODE(ZARD_CHECK_GPIO_CTLR_OKAY))

#define ZARD_IDX_IF_MATCH(i, n)                                                                    \
	COND_CODE_1(DT_SAME_NODE(n, GET_ARG_N(UTIL_INC(i), ZARD_ALL_OKAY_GPIO_CTLR)), (i), ())

#define ZARD_MATCH_IDX(n)                                                                          \
	LISTIFY(NUM_VA_ARGS_LESS_1(ZARD_ALL_OKAY_GPIO_CTLR), ZARD_IDX_IF_MATCH, (), n)

#define ZARD_GET_NGPIOS(i, ...) DT_PROP(GET_ARG_N(UTIL_INC(i), __VA_ARGS__), ngpios)
#define ZARD_SUM_NGPIOS(...)                                                                       \
	LISTIFY(NUM_VA_ARGS_LESS_1(__VA_ARGS__), ZARD_GET_NGPIOS, (+), __VA_ARGS__)
#define ZARD_GLOBAL_GPIO_NUM_(ph)                                                                  \
	ZARD_SUM_NGPIOS(GET_ARGS_FIRST_N(ZARD_MATCH_IDX(ph), ZARD_ALL_OKAY_GPIO_CTLR))

#define ZARD_GLOBAL_GPIO_NUM(ph)                                                                   \
	COND_CODE_1(IS_EQ(NUM_VA_ARGS(ZARD_GLOBAL_GPIO_NUM_(ph)), 0),     \
					     (0), (ZARD_GLOBAL_GPIO_NUM_(ph)))

#define ZARD_CONN_DN_ENUMS(n, p, i)                                                                \
	UTIL_CAT(D, DT_MAP_ENTRY_CHILD_SPECIFIER_BY_IDX(n, p, i, 0)) =                                 \
		ZARD_GLOBAL_GPIO_NUM(DT_MAP_ENTRY_PARENT_BY_IDX(n, p, i)) +                                \
		DT_MAP_ENTRY_PARENT_SPECIFIER_BY_IDX(n, p, i, 0)

#define ZARD_CONN_AN_ENUMS(n, p, i)                                                                \
	UTIL_CAT(A, DT_MAP_ENTRY_CHILD_SPECIFIER_BY_IDX(n, p, i, 0)) =                                 \
		ZARD_GLOBAL_GPIO_NUM(                                                                      \
			DT_MAP_ENTRY_PARENT_BY_IDX(DT_NODELABEL(ZARD_CONNECTOR), gpio_map, i)) +               \
		DT_MAP_ENTRY_PARENT_SPECIFIER_BY_IDX(DT_NODELABEL(ZARD_CONNECTOR), gpio_map, i, 0)

#if DT_NODE_EXISTS(DT_ALIAS(led0))
#define LED_BUILTIN_                                                                               \
	ZARD_GLOBAL_GPIO_NUM(DT_PHANDLE_BY_IDX(DT_ALIAS(led0), gpios, 0)) +                            \
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
	DT_FOREACH_MAP_ENTRY_SEP(DT_NODELABEL(ZARD_CONNECTOR), gpio_map, ZARD_CONN_DN_ENUMS, (, )),
#endif
	NUM_OF_DIGITAL_PINS
};

#ifdef CONFIG_ADC

#define AN_ENUMS(n, p, i) A ## i = DIGITAL_PIN_GPIOS_FIND_PIN( \
		DT_REG_ADDR(DT_PHANDLE_BY_IDX(DT_PATH(zephyr_user), p, i)),        \
		DT_PHA_BY_IDX(DT_PATH(zephyr_user), p, i, pin)),
enum analogPins {
#if DT_NODE_HAS_PROP(DT_PATH(zephyr_user), adc_pin_gpios)
	DT_FOREACH_PROP_ELEM(DT_PATH(zephyr_user), adc_pin_gpios, AN_ENUMS)
#elif defined(ZARD_ADC_CONNECTOR)
	DT_FOREACH_MAP_ENTRY_SEP(DT_NODELABEL(ZARD_ADC_CONNECTOR), io_channel_map, ZARD_CONN_AN_ENUMS,
							 (, )),
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
