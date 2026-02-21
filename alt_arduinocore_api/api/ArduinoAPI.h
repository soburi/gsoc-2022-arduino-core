#pragma once

#ifdef __cplusplus
#include <cstdint>
#include <cstddef>
#include <stdlib.h>
#else
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#endif
#include <zephyr/drivers/gpio.h>

#include "api/HardwareSerial.h"
#include "common_types.h"

#define lowByte(w) ((uint8_t) ((w) & 0xff))
#define highByte(w) ((uint8_t) ((w) >> 8))

#define bit(b) BIT(b)
#define bitRead(value, bit) FIELD_GET(BIT(bit), value)
#define bitSet(value, bit) ((value) |= BIT(bit))
#define bitClear(value, bit) ((value) &= ~BIT(bit))
#define bitToggle(value, bit) ((value) ^= BIT(bit))
#define bitWrite(value, bit, bitvalue) WRITE_BIT(value, bit, bitvalue)


#ifdef __cplusplus
extern "C" {
#endif

typedef gpio_port_pins_t pin_size_t;

typedef void (*voidFuncPtr)(void);
typedef void (*voidFuncPtrParam)(void*);

void yield(void);

void init(void);
void initVariant(void);

int main() __attribute__((weak));

void pinMode(pin_size_t pinNumber, PinMode pinMode);
void digitalWrite(pin_size_t pinNumber, PinStatus status);
PinStatus digitalRead(pin_size_t pinNumber);
int analogRead(pin_size_t pinNumber);
void analogReference(uint8_t mode);
void analogWrite(pin_size_t pinNumber, int value);

unsigned long millis(void);
unsigned long micros(void);
void delay(unsigned long);
void delayMicroseconds(unsigned int us);
unsigned long pulseIn(pin_size_t pin, uint8_t state, unsigned long timeout);
unsigned long pulseInLong(pin_size_t pin, uint8_t state, unsigned long timeout);

void shiftOut(pin_size_t dataPin, pin_size_t clockPin, BitOrder bitOrder, uint8_t val);
uint8_t shiftIn(pin_size_t dataPin, pin_size_t clockPin, BitOrder bitOrder);

void attachInterrupt(pin_size_t interruptNumber, voidFuncPtr callback, PinStatus mode);
void attachInterruptParam(pin_size_t interruptNumber, voidFuncPtrParam callback, PinStatus mode, void* param);
void detachInterrupt(pin_size_t interruptNumber);

void setup(void);
void loop(void);

#ifdef __cplusplus
} // extern "C"
#endif

unsigned long pulseIn(uint8_t pin, uint8_t state, unsigned long timeout = 1000000L);
unsigned long pulseInLong(uint8_t pin, uint8_t state, unsigned long timeout = 1000000L);

void tone(uint8_t _pin, unsigned int frequency, unsigned long duration = 0);
void noTone(uint8_t _pin);

// WMath prototypes
long random(long);
long random(long, long);
void randomSeed(unsigned long);


extern "C" {
  int32_t map_i32(int32_t x, int32_t in_min, int32_t in_max, int32_t out_min, int32_t out_max);
  uint16_t makeWord_w(uint16_t w);
  uint16_t makeWord_hl(uint8_t h, uint8_t l);
}

inline long map(long x, long in_min, long in_max, long out_min, long out_max)
{
  return map_i32(x, in_min, in_max, out_min, out_max);
}

inline uint16_t makeWord(uint16_t w) {
  return makeWord_w(w);
}

inline uint16_t makeWord(uint8_t h, uint8_t l) {
  return makeWord_hl(h, l);
}

#define word(...) makeWord(__VA_ARGS__)

#ifdef __cplusplus
  template<class T, class L>
  auto min(const T& a, const L& b) -> decltype((b < a) ? b : a)
  {
    return (b < a) ? b : a;
  }

  template<class T, class L>
  auto max(const T& a, const L& b) -> decltype((b < a) ? b : a)
  {
    return (a < b) ? b : a;
  }
#else
#ifndef min
#define min(a,b) \
   ({ __typeof__ (a) _a = (a); \
       __typeof__ (b) _b = (b); \
     _a < _b ? _a : _b; })
#endif
#ifndef max
#define max(a,b) \
   ({ __typeof__ (a) _a = (a); \
       __typeof__ (b) _b = (b); \
     _a > _b ? _a : _b; })
#endif
#endif
