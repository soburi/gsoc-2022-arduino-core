/*
 * Copyright (c) 2022 Dhruva Gole
 * Copyright (c) 2026 TOKITA Hiroshi
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <Arduino.h>
#include "zephyrInternal.h"

#include <zephyr/spinlock.h>

#if DT_NODE_HAS_PROP(DT_PATH(zephyr_user), digital_pin_gpios)
static constexpr struct gpio_dt_spec arduino_pins[] = {DT_FOREACH_PROP_ELEM_SEP(
	DT_PATH(zephyr_user), digital_pin_gpios, GPIO_DT_SPEC_GET_BY_IDX, (, ))};
#else
#define GET_GPIO_DEVICES(node_id)                                                                  \
	COND_CODE_1(DT_NODE_HAS_STATUS_OKAY(node_id),                                              \
        (COND_CODE_1(DT_NODE_HAS_PROP(node_id, gpio_controller),                       \
         (DEVICE_DT_GET(node_id),), ())), ())

#define GET_GPIO_NGPIOS(node_id)                                                                   \
	COND_CODE_1(DT_NODE_HAS_STATUS_OKAY(node_id),                                              \
        (COND_CODE_1(DT_NODE_HAS_PROP(node_id, gpio_controller),                       \
         (DT_PROP(node_id, ngpios),), ())), ())

static constexpr const struct device *gpio_ports[] = {DT_FOREACH_NODE(GET_GPIO_DEVICES)};
static constexpr uint32_t gpio_ngpios[] = {DT_FOREACH_NODE(GET_GPIO_NGPIOS)};
#endif

namespace {

/*
 * Calculate GPIO ports/pins number statically from devicetree configuration
 */

template <class N, class Head> constexpr const N sum_of_list(const N sum, const Head &head)
{
  return sum + head;
}

template <class N, class Head, class... Tail>
constexpr const N sum_of_list(const N sum, const Head &head, const Tail &...tail)
{
  return sum_of_list(sum + head, tail...);
}

template <class N, class Head> constexpr const N max_in_list(const N max, const Head &head)
{
  return (max >= head) ? max : head;
}

template <class N, class Head, class... Tail>
constexpr const N max_in_list(const N max, const Head &head, const Tail &...tail)
{
  return max_in_list((max >= head) ? max : head, tail...);
}

template <class Query, class Head>
constexpr const size_t is_first_appearance(const size_t &idx, const size_t &at, const size_t &found,
             const Query &query, const Head &head)
{
  return ((found == ((size_t)-1)) && (query == head) && (idx == at)) ? 1 : 0;
}

template <class Query, class Head, class... Tail>
constexpr const size_t is_first_appearance(const size_t &idx, const size_t &at, const size_t &found,
             const Query &query, const Head &head,
             const Tail &...tail)
{
  return ((found == ((size_t)-1)) && (query == head) && (idx == at))
           ? 1
           : is_first_appearance(idx + 1, at, (query == head ? idx : found), query,
               tail...);
}

#if !DT_NODE_HAS_PROP(DT_PATH(zephyr_user), digital_pin_gpios)
constexpr inline const struct device *local_gpio_port(pin_size_t gpin);

constexpr inline const struct device *local_gpio_port_r(pin_size_t pin,
							const struct device *const *ctrl,
							const uint32_t accum, const uint32_t *end,
							size_t n) {
  return (n == 0) ? nullptr :
		    (pin < accum + end[0]) ?  ctrl[0] :
  				  local_gpio_port_r(pin, ctrl + 1, accum + end[0], end + 1, n - 1);
}

constexpr inline size_t port_index_r(const struct device *target, const struct device *const *table,
  								 pin_size_t idx, size_t n) {
  return (n == 0) ? size_t(-1) :
  	   (target == table[0]) ? idx : port_index_r(target, table + 1, idx + 1, n - 1);
}

constexpr inline pin_size_t port_idx(pin_size_t gpin) {
  return port_index_r(local_gpio_port(gpin), gpio_ports, 0, ARRAY_SIZE(gpio_ports));
}

constexpr inline pin_size_t end_accum_r(const uint32_t accum, const uint32_t *end, size_t n) {
  return (n == 0) ? accum : end_accum_r(accum + end[0], end + 1, n - 1);
}

constexpr inline pin_size_t end_accum(size_t n) {
  return end_accum_r(0, gpio_ngpios, n);
}

constexpr inline pin_size_t global_gpio_pin_(size_t port_idx, pin_size_t lpin) {
  return port_idx == size_t(-1) ? size_t(-1) : end_accum(port_idx) + lpin;
}

constexpr inline pin_size_t global_gpio_pin(const struct device *lport, pin_size_t lpin) {
  return global_gpio_pin_(port_index_r(lport, gpio_ports, 0, ARRAY_SIZE(gpio_ports)), lpin);
}
#endif

constexpr inline const struct device *local_gpio_port(pin_size_t gpin) {
#if DT_NODE_HAS_PROP(DT_PATH(zephyr_user), digital_pin_gpios)
  return (gpin < ARRAY_SIZE(arduino_pins)) ? arduino_pins[gpin].port : nullptr;
#else
  return local_gpio_port_r(gpin, gpio_ports, 0, gpio_ngpios, ARRAY_SIZE(gpio_ports));
#endif
}

constexpr inline pin_size_t local_gpio_pin(pin_size_t gpin) {
#if DT_NODE_HAS_PROP(DT_PATH(zephyr_user), digital_pin_gpios)
  return (gpin < ARRAY_SIZE(arduino_pins)) ? arduino_pins[gpin].pin : pin_size_t(-1);
#else
  return port_idx(gpin) == pin_size_t(-1) ? pin_size_t(-1) : gpin - end_accum(port_idx(gpin));
#endif
}

inline int global_gpio_pin_configure(pin_size_t pinNumber, int flags) {
#if DT_NODE_HAS_PROP(DT_PATH(zephyr_user), digital_pin_gpios)
  if (pinNumber >= ARRAY_SIZE(arduino_pins)) {
    return -1;
  }
  return gpio_pin_configure_dt(&arduino_pins[pinNumber], flags);
#else
  const struct device *port = local_gpio_port(pinNumber);

  if (port) {
    return gpio_pin_configure(port, local_gpio_pin(pinNumber), flags);
  } else {
    return -1;
  }
#endif
}

#if DT_NODE_HAS_PROP(DT_PATH(zephyr_user), digital_pin_gpios)
#if DT_PROP_LEN_OR(DT_PATH(zephyr_user), digital_pin_gpios, 0) > 0
#define GET_DEVICE_VARGS(n, p, i, _) DEVICE_DT_GET(DT_GPIO_CTLR_BY_IDX(n, p, i))
#define FIRST_APPEARANCE(n, p, i)                                                                  \
  is_first_appearance(0, i, ((size_t)-1), DEVICE_DT_GET(DT_GPIO_CTLR_BY_IDX(n, p, i)),       \
          DT_FOREACH_PROP_ELEM_SEP_VARGS(n, p, GET_DEVICE_VARGS, (, ), 0))
const int port_num =
  sum_of_list(0, DT_FOREACH_PROP_ELEM_SEP(DT_PATH(zephyr_user), digital_pin_gpios,
            FIRST_APPEARANCE, (, )));

#define GPIO_NGPIOS(n, p, i) DT_PROP(DT_GPIO_CTLR_BY_IDX(n, p, i), ngpios)
const int max_ngpios = max_in_list(
  0, DT_FOREACH_PROP_ELEM_SEP(DT_PATH(zephyr_user), digital_pin_gpios, GPIO_NGPIOS, (, )));
#else
const int port_num = 1;
const int max_ngpios = 0;
#endif
#else
const int port_num = ARRAY_SIZE(gpio_ports);
const int max_ngpios = max_in_list(DT_FOREACH_NODE(GET_GPIO_NGPIOS) 0);
#endif

/*
 * GPIO callback implementation
 */

struct arduino_callback {
  voidFuncPtr handler;
  bool enabled;
};

struct gpio_port_callback {
  struct gpio_callback callback;
  struct arduino_callback handlers[max_ngpios];
  gpio_port_pins_t pins;
  const struct device *dev;
} port_callback[port_num] = {0};

struct gpio_port_callback *find_gpio_port_callback(const struct device *dev)
{
  if (dev == nullptr) {
    return nullptr;
  }

  for (size_t i = 0; i < ARRAY_SIZE(port_callback); i++) {
    if (port_callback[i].dev == dev) {
      return &port_callback[i];
    }
    if (port_callback[i].dev == nullptr) {
      port_callback[i].dev = dev;
      return &port_callback[i];
    }
  }

  return nullptr;
}

void setInterruptHandler(pin_size_t pinNumber, voidFuncPtr func)
{
  struct gpio_port_callback *pcb = find_gpio_port_callback(local_gpio_port(pinNumber));

  if (pcb) {
    pcb->handlers[local_gpio_pin(pinNumber)].handler = func;
  }
}

void handleGpioCallback(const struct device *port, struct gpio_callback *cb, uint32_t pins)
{
  struct gpio_port_callback *pcb = (struct gpio_port_callback *)cb;

  for (uint32_t i = 0; i < max_ngpios; i++) {
    if (pins & BIT(i) && pcb->handlers[i].enabled) {
      pcb->handlers[i].handler();
    }
  }
}

#ifdef CONFIG_PWM

#define PWM_DT_SPEC(n,p,i) PWM_DT_SPEC_GET_BY_IDX(n, i),
#define PWM_PINS(n, p, i) \
	DIGITAL_PIN_GPIOS_FIND_PIN( \
                DT_REG_ADDR(DT_PHANDLE_BY_IDX(DT_PATH(zephyr_user), p, i)),        \
                DT_PHA_BY_IDX(DT_PATH(zephyr_user), p, i, pin)),
#define PWM_CONN_CHANNEL_DT(n, p, i)                                                               \
	COND_CODE_1(DT_NODE_HAS_STATUS_OKAY(DT_MAP_ENTRY_PARENT_BY_IDX(n, p, i)),                  \
		    ({ .dev = DEVICE_DT_GET(DT_MAP_ENTRY_PARENT_BY_IDX(n, p, i)),                  \
		       .channel = DT_MAP_ENTRY_PARENT_SPECIFIER_BY_IDX(n, p, i, 0),                \
		       .period = 255, },),                                                         \
		    ())
#define PWM_CONN_PINNUM(n, p, i)                                                                   \
	COND_CODE_1(DT_NODE_HAS_STATUS_OKAY(DT_MAP_ENTRY_PARENT_BY_IDX(n, p, i)),                  \
		    (DT_MAP_ENTRY_CHILD_SPECIFIER_BY_IDX(n, p, i, 0),),                            \
		    ())

const struct pwm_dt_spec arduino_pwm[] = {
#if DT_NODE_HAS_PROP(DT_PATH(zephyr_user), pwms)
	DT_FOREACH_PROP_ELEM(DT_PATH(zephyr_user), pwms, PWM_DT_SPEC)
#elif defined(ZARD_PWM_CONNECTOR)
	DT_FOREACH_MAP_ENTRY(DT_NODELABEL(ZARD_PWM_CONNECTOR), pwm_map, PWM_CONN_CHANNEL_DT)
#endif
};

/* pwm-pins node provides a mapping digital pin numbers to pwm channels */
const pin_size_t arduino_pwm_pins[] = {
#if DT_NODE_HAS_PROP(DT_PATH(zephyr_user), pwm_pin_gpios)
  DT_FOREACH_PROP_ELEM(DT_PATH(zephyr_user), pwm_pin_gpios, PWM_PINS)
#elif defined(ZARD_PWM_CONNECTOR)
  DT_FOREACH_MAP_ENTRY(DT_NODELABEL(ZARD_PWM_CONNECTOR), pwm_map, PWM_CONN_PINNUM)
#endif
};

size_t pwm_pin_index(pin_size_t pinNumber) {
  for(size_t i=0; i<ARRAY_SIZE(arduino_pwm_pins); i++) {
    if (arduino_pwm_pins[i] == pinNumber) {
      return i;
    }
  }
  return (size_t)-1;
}

#endif //CONFIG_PWM

#ifdef CONFIG_ADC

#define ADC_DT_SPEC(n,p,i) ADC_DT_SPEC_GET_BY_IDX(n, i),
#define ADC_PINS(n, p, i) \
	DIGITAL_PIN_GPIOS_FIND_PIN( \
                DT_REG_ADDR(DT_PHANDLE_BY_IDX(DT_PATH(zephyr_user), p, i)),        \
                DT_PHA_BY_IDX(DT_PATH(zephyr_user), p, i, pin)),
#define ADC_CH_CFG(n,p,i) arduino_adc[i].channel_cfg,
#define ADC_CONN_CHANNEL_CFG(n, p, i)                                                              \
	COND_CODE_1(DT_NODE_HAS_STATUS_OKAY(DT_MAP_ENTRY_PARENT_BY_IDX(n, p, i)),                  \
	            (ADC_CHANNEL_CFG_DT(ADC_CHANNEL_DT_NODE(DT_MAP_ENTRY_PARENT_BY_IDX(n, p, i),                       \
					DT_MAP_ENTRY_PARENT_SPECIFIER_BY_IDX(n, p, i, 0))),),        \
		    ())
#define ADC_CONN_CHANNEL_DT(n, p, i)                                                               \
	COND_CODE_1(DT_NODE_HAS_STATUS_OKAY(DT_MAP_ENTRY_PARENT_BY_IDX(n, p, i)),                  \
	            (ADC_DT_SPEC_STRUCT(DT_MAP_ENTRY_PARENT_BY_IDX(n, p, i),                       \
					DT_MAP_ENTRY_PARENT_SPECIFIER_BY_IDX(n, p, i, 0)),),        \
		    ())
#define ADC_CONN_PINNUM(n, p, i)                                                                   \
	COND_CODE_1(DT_NODE_HAS_STATUS_OKAY(DT_MAP_ENTRY_PARENT_BY_IDX(n, p, i)),                  \
	            (DT_MAP_ENTRY_CHILD_SPECIFIER_BY_IDX(n, p, i, 0),),                            \
		    ())

const struct adc_dt_spec arduino_adc[] = {
#if DT_NODE_HAS_PROP(DT_PATH(zephyr_user), io_channels)
  DT_FOREACH_PROP_ELEM(DT_PATH(zephyr_user), io_channels, ADC_DT_SPEC)
#elif defined(ZARD_ADC_CONNECTOR)
  DT_FOREACH_MAP_ENTRY(DT_NODELABEL(ZARD_ADC_CONNECTOR), io_channel_map, ADC_CONN_CHANNEL_DT)
#endif
};

/* io-channel-pins node provides a mapping digital pin numbers to adc channels */
const pin_size_t arduino_analog_pins[] = {
#if DT_NODE_HAS_PROP(DT_PATH(zephyr_user), adc_pin_gpios)
  DT_FOREACH_PROP_ELEM(DT_PATH(zephyr_user), adc_pin_gpios, ADC_PINS)
#elif defined(ZARD_ADC_CONNECTOR)
  DT_FOREACH_MAP_ENTRY(DT_NODELABEL(ZARD_ADC_CONNECTOR), io_channel_map, ADC_CONN_PINNUM)
#endif
};

struct adc_channel_cfg channel_cfg[ARRAY_SIZE(arduino_analog_pins)] = {
#if DT_NODE_HAS_PROP(DT_PATH(zephyr_user), io_channels)
  DT_FOREACH_PROP_ELEM(DT_PATH(zephyr_user), io_channels, ADC_CH_CFG)
#elif defined(ZARD_ADC_CONNECTOR)
  DT_FOREACH_MAP_ENTRY(DT_NODELABEL(ZARD_ADC_CONNECTOR), io_channel_map, ADC_CONN_CHANNEL_CFG)
#endif
};

size_t analog_pin_index(pin_size_t pinNumber) {
  for(size_t i=0; i<ARRAY_SIZE(arduino_analog_pins); i++) {
    if (arduino_analog_pins[i] == pinNumber) {
      return i;
    }
  }
  return (size_t)-1;
}

#endif //CONFIG_ADC

static unsigned int irq_key;
static bool interrupts_disabled = false;
}  // namespace

void yield(void) {
  k_yield();
}

/*
 *  The ACTIVE_HIGH flag is set so that A low physical
 *  level on the pin will be interpreted as value 0.
 *  A high physical level will be interpreted as value 1
 */
void pinMode(pin_size_t pinNumber, PinMode pinMode) {
  if (pinMode == INPUT) { // input mode
    global_gpio_pin_configure(pinNumber,
                          GPIO_INPUT | GPIO_ACTIVE_HIGH);
  } else if (pinMode == INPUT_PULLUP) { // input with internal pull-up
    global_gpio_pin_configure(pinNumber,
                          GPIO_INPUT | GPIO_PULL_UP | GPIO_ACTIVE_HIGH);
  } else if (pinMode == INPUT_PULLDOWN) { // input with internal pull-down
    global_gpio_pin_configure(pinNumber,
                          GPIO_INPUT | GPIO_PULL_DOWN | GPIO_ACTIVE_HIGH);
  } else if (pinMode == OUTPUT) { // output mode
    global_gpio_pin_configure(pinNumber,
                          GPIO_OUTPUT_LOW | GPIO_ACTIVE_HIGH);
  }
}

void digitalWrite(pin_size_t pinNumber, PinStatus status) {
  const struct device *port = local_gpio_port(pinNumber);

  if (port) {
    gpio_pin_set(port, local_gpio_pin(pinNumber), status);
  }
}

PinStatus digitalRead(pin_size_t pinNumber) {
  const struct device *port = local_gpio_port(pinNumber);

  if (port) {
    return (gpio_pin_get(port, local_gpio_pin(pinNumber)) == 1) ? HIGH : LOW;
  } else {
    return LOW;
  }
}

#if CONFIG_ARDUINO_MAX_TONES < 0
#if DT_NODE_HAS_PROP(DT_PATH(zephyr_user), digital_pin_gpios)
#define MAX_TONE_PINS DT_PROP_LEN(DT_PATH(zephyr_user), digital_pin_gpios)
#elif defined(ZARD_CONNECTOR)
#define MAX_TONE_PINS DT_PROP_LEN(DT_NODELABEL(ZARD_CONNECTOR), gpio_map)
#else
#define MAX_TONE_PINS 1
#endif
#else
#define MAX_TONE_PINS CONFIG_ARDUINO_MAX_TONES
#endif

#define TOGGLES_PER_CYCLE 2ULL

static struct pin_timer {
  struct k_timer timer;
  uint32_t count{0};
  pin_size_t pin{pin_size_t(-1)};
  bool infinity{false};
  struct k_spinlock lock;
} arduino_pin_timers[MAX_TONE_PINS];

static struct pin_timer* find_pin_timer(pin_size_t pinNumber, bool active_only) {
  for (size_t i = 0; i < ARRAY_SIZE(arduino_pin_timers); i++) {
    k_spinlock_key_t key = k_spin_lock(&arduino_pin_timers[i].lock);

    if (arduino_pin_timers[i].pin == pinNumber) {
      k_spin_unlock(&arduino_pin_timers[i].lock, key);
      return &arduino_pin_timers[i];
    }

    k_spin_unlock(&arduino_pin_timers[i].lock, key);
  }

  if (active_only) {
    return nullptr;
  }

  for (size_t i = 0; i < ARRAY_SIZE(arduino_pin_timers); i++) {
    k_spinlock_key_t key = k_spin_lock(&arduino_pin_timers[i].lock);

    if (arduino_pin_timers[i].pin == pin_size_t(-1)) {
      arduino_pin_timers[i].pin = pinNumber;
      k_spin_unlock(&arduino_pin_timers[i].lock, key);
      return &arduino_pin_timers[i];
    }

    k_spin_unlock(&arduino_pin_timers[i].lock, key);
  }

  return nullptr;
}

void tone_expiry_cb(struct k_timer *timer) {
  struct pin_timer *pt = CONTAINER_OF(timer, struct pin_timer, timer);
  k_spinlock_key_t key = k_spin_lock(&pt->lock);
  const struct device *port = local_gpio_port(pt->pin);
  pin_size_t pin = pt->pin;

  if (pt->count == 0 && !pt->infinity) {
    if (port) {
      gpio_pin_set(port, local_gpio_pin(pt->pin), 0);
    }

    k_timer_stop(timer);
    pt->pin = pin_size_t(-1);
  } else {
    if (port) {
      gpio_pin_toggle(port, local_gpio_pin(pt->pin));
    }

    pt->count--;
  }

  k_spin_unlock(&pt->lock, key);
}

void tone(pin_size_t pinNumber, unsigned int frequency,
          unsigned long duration) {
  k_spinlock_key_t key;
  struct pin_timer *pt;
  k_timeout_t timeout;
  const struct device *port;

  pt = find_pin_timer(pinNumber, false);

  if (pt == nullptr) {
    return;
  }

  port = local_gpio_port(pt->pin);

  pinMode(pinNumber, OUTPUT);
  k_timer_stop(&pt->timer);

  if (frequency == 0) {
    key = k_spin_lock(&pt->lock);
    pt->pin = pin_size_t(-1);
    k_spin_unlock(&pt->lock, key);

    if (port) {
      gpio_pin_set(port, local_gpio_pin(pinNumber), 0);
    }
    return;
  }

  timeout = K_NSEC(NSEC_PER_SEC / (TOGGLES_PER_CYCLE * frequency));
  if (timeout.ticks == 0) {
    timeout.ticks = 1;
  }

  key = k_spin_lock(&pt->lock);
  pt->infinity = (duration == 0);
  pt->count = min((uint64_t)duration * frequency * TOGGLES_PER_CYCLE / MSEC_PER_SEC, UINT32_MAX);
  pt->pin = pinNumber;
  k_spin_unlock(&pt->lock, key);

  k_timer_init(&pt->timer, tone_expiry_cb, NULL);

  if (port) {
    gpio_pin_set(port, local_gpio_pin(pinNumber), 0);
  }
  k_timer_start(&pt->timer, timeout, timeout);
}

void noTone(pin_size_t pinNumber) {
  struct pin_timer *pt;
  k_spinlock_key_t key;
  const struct device *port;

  pt = find_pin_timer(pinNumber, true);

  if (pt == nullptr) {
    return;
  }

  port = local_gpio_port(pt->pin);

  key = k_spin_lock(&pt->lock);
  k_timer_stop(&pt->timer);
  pt->pin = pin_size_t(-1);
  k_spin_unlock(&pt->lock, key);

  if (port) {
    gpio_pin_set(port, local_gpio_pin(pinNumber), 0);
  }
}

void delay(unsigned long ms) {
  k_sleep(K_MSEC(ms));
}

void delayMicroseconds(unsigned int us) {
  k_busy_wait(us);
}

unsigned long micros(void) {
  return k_cyc_to_us_floor32(k_cycle_get_32());
}

unsigned long millis(void) {
  return k_uptime_get_32();
}

#ifdef CONFIG_PWM

void analogWrite(pin_size_t pinNumber, int value)
{
  size_t idx = pwm_pin_index(pinNumber);

  if (idx >= ARRAY_SIZE(arduino_pwm)) {
    return;
  }

  if (!pwm_is_ready_dt(&arduino_pwm[idx])) {
    return;
  }

  if (((uint32_t)value) > arduino_pwm[idx].period) {
    value = arduino_pwm[idx].period;
  } else if (value < 0) {
    value = 0;
  }

  /*
   * A duty ratio determines by the period value defined in dts
   * and the value arguments. So usually the period value sets as 255.
   */
  (void)pwm_set_pulse_dt(&arduino_pwm[idx], value);
}

#endif

#ifdef CONFIG_ADC

void analogReference(uint8_t mode)
{
  /*
   * The Arduino API not clearly defined what means of
   * the mode argument of analogReference().
   * Treat the value as equivalent to zephyr's adc_reference.
   */
  for (size_t i=0; i<ARRAY_SIZE(channel_cfg); i++) {
    channel_cfg[i].reference = static_cast<adc_reference>(mode);
  }
}

int analogRead(pin_size_t pinNumber)
{
  int err;
  int16_t buf;
  struct adc_sequence seq = { .buffer = &buf, .buffer_size = sizeof(buf) };
  size_t idx = analog_pin_index(pinNumber);

  if (idx >= ARRAY_SIZE(arduino_adc) ) {
    return -EINVAL;
  }

  /*
   * ADC that is on MCU supported by Zephyr exists
   * only 16bit resolution, currently.
   */
  if (arduino_adc[idx].resolution > 16) {
    return -ENOTSUP;
  }

  err = adc_channel_setup(arduino_adc[idx].dev, &arduino_adc[idx].channel_cfg);
  if (err < 0) {
    return err;
  }

  seq.channels = BIT(arduino_adc[idx].channel_id);
  seq.resolution = arduino_adc[idx].resolution;
  seq.oversampling = arduino_adc[idx].oversampling;

  err = adc_read(arduino_adc[idx].dev, &seq);
  if (err < 0) {
    return err;
  }

  return buf;
}

#endif

void attachInterrupt(pin_size_t pinNumber, voidFuncPtr callback, PinStatus pinStatus)
{
  const struct device *port = local_gpio_port(pinNumber);
  struct gpio_port_callback *pcb;
  gpio_flags_t intmode = 0;

  if (!callback) {
    return;
  }

  if (pinStatus == LOW) {
    intmode |= GPIO_INT_LEVEL_LOW;
  } else if (pinStatus == HIGH) {
    intmode |= GPIO_INT_LEVEL_HIGH;
  } else if (pinStatus == CHANGE) {
    intmode |= GPIO_INT_EDGE_BOTH;
  } else if (pinStatus == FALLING) {
    intmode |= GPIO_INT_EDGE_FALLING;
  } else if (pinStatus == RISING) {
    intmode |= GPIO_INT_EDGE_RISING;
  } else {
    return;
  }

  pcb = find_gpio_port_callback(port);
  __ASSERT(pcb != nullptr, "gpio_port_callback not found");

  pcb->pins |= BIT(local_gpio_pin(pinNumber));
  setInterruptHandler(pinNumber, callback);
  enableInterrupt(pinNumber);

  if (port) {
    gpio_pin_interrupt_configure(port, local_gpio_pin(pinNumber), intmode);
    gpio_init_callback(&pcb->callback, handleGpioCallback, pcb->pins);
    gpio_add_callback(port, &pcb->callback);
  }
}

void detachInterrupt(pin_size_t pinNumber)
{
  setInterruptHandler(pinNumber, nullptr);
  disableInterrupt(pinNumber);
}

#ifndef CONFIG_MINIMAL_LIBC_RAND

#include <stdlib.h>

void randomSeed(unsigned long seed) {
	srand(seed);
}

long random(long min, long max) {
	return rand() % (max - min) + min;
}

long random(long max) {
	return rand() % max;
}

#endif

unsigned long pulseIn(pin_size_t pinNumber, uint8_t state, unsigned long timeout) {
  const struct device *port = local_gpio_port(pinNumber);
  const size_t pin = local_gpio_pin(pinNumber);
  struct k_timer timer;
  int64_t start, end, delta = 0;

  if (!device_is_ready(port)) {
    return 0;
  }

  k_timer_init(&timer, NULL, NULL);
  k_timer_start(&timer, K_MSEC(timeout), K_NO_WAIT);

  while(gpio_pin_get(port, pin) == state && k_timer_status_get(&timer) == 0);
  if (k_timer_status_get(&timer) > 0) {
    goto cleanup;
  }

  while(gpio_pin_get(port, pin) != state && k_timer_status_get(&timer) == 0);
  if (k_timer_status_get(&timer) > 0) {
    goto cleanup;
  }

  start = k_uptime_ticks();
  while(gpio_pin_get(port, pin) == state && k_timer_status_get(&timer) == 0);
  if (k_timer_status_get(&timer) > 0) {
    goto cleanup;
  }
  end = k_uptime_ticks();

  delta = k_ticks_to_us_floor64(end - start);

cleanup:
  k_timer_stop(&timer);
  return (unsigned long)delta;
}

void enableInterrupt(pin_size_t pinNumber) {
  struct gpio_port_callback *pcb = find_gpio_port_callback(local_gpio_port(pinNumber));

  if (pcb) {
    pcb->handlers[local_gpio_pin(pinNumber)].enabled = true;
  }
}

void disableInterrupt(pin_size_t pinNumber) {
  struct gpio_port_callback *pcb = find_gpio_port_callback(local_gpio_port(pinNumber));

  if (pcb) {
    pcb->handlers[local_gpio_pin(pinNumber)].enabled = false;
  }
}

void interrupts(void) {
  if (interrupts_disabled) {
    irq_unlock(irq_key);
    interrupts_disabled = false;
  }
}

void noInterrupts(void) {
  if (!interrupts_disabled) {
    irq_key = irq_lock();
    interrupts_disabled = true;
  }
}

int digitalPinToInterrupt(pin_size_t pin) {
  struct gpio_port_callback *pcb =
      find_gpio_port_callback(local_gpio_port(pin));

  return (pcb) ? pin : -1;
}
