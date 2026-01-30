Board Configuration Guide
=========================

This document defines practical support levels for ArduinoCore-Zephyr and explains how to reach each level.

The support level definitions
-----------------------------

### Level 0 - Basic GPIO runtime

Arduino GPIO APIs are usable with **numeric pins** (global GPIO numbering).  
All boards are expected to satisfy this level **once ArduinoCore-Zephyr is enabled**.

### Level 1 — Blinky-ready

The Blinky sample works if the board provides a built-in LED.

### Level 2 — Digital pin definitions are available

Arduino-style digital pin definitions `D0`, `D1`, … are available.

### Level 3 — Common bus definitions are available

Common buses (`Serial`, `Wire`, and `SPI`) are available for use.

### Level 4 — PWM and ADC are available for use

PWM and ADC can be used because channel provisioning and pin association are provided.

### Level 5 — Supports board-specific features

Board-specific peripherals and features are supported.

A well-made Zephyr board configuration should provide **Level 3** support without additional configurations.  
**Level 4** support is required to cover most standard Arduino use cases.
Reaching **Level 4 and above** requires a board-/variant-specific overlay, typically delivered as snippets.


Making a configuration for your board
-------------------------------------

The design goals are:

- **Level 3** should be reachable without extra configuration if the Zephyr board DTS is well-prepared.
- **Level 4** is the “Arduino satisfaction line” (ADC + PWM), but it cannot be configuration-free and should be delivered via snippets/overlays.

### Configuration sources

#### Board-provided defaults (Zephyr-style)

A well-defined board DTS typically includes:

- An Arduino-compatible connector definition (board-dependent)
- Connector-based pin mapping (e.g., `gpio-map`, `pwm-map`, `io-channel-map`)
- Bus defaults via node labels such as `arduino_serial`, `arduino_i2c`, `arduino_spi`
- A built-in LED via the `led0` alias (recommended)

These are the “works out of the box” ingredients.

#### Define overrides

Define nodes/properties under `/zephyr,user` to configure GPIO, ADC, PWM, I2C, and SPI.

### How to reach Level 1

If your board has an onboard LED, you can support it in one of the following ways (**highest precedence first**):

1. Manually define `LED_BUILTIN` in the board-specific `variant.h`
2. Define `/zephyr,user/builtin-led-gpios`
3. Define the `led0` alias for the LED node


### How to reach Level 2

Two ways to reach it (**highest precedence first**):

1. **Define `/zephyr,user/digital-pin-gpios`**  
   Set the list of GPIOs to use in `/zephyr,user/digital-pin-gpios`.  
   They will be assigned in the order you set them: `D0`, `D1`, `D2`, ...

2. **Define a connector nexus `gpio-map`** (such as `arduino_header`, board-dependent)  
   `D0`, `D1`, ... are derived from the connector mapping (the connector-defined pin index).

Each approach results in different numeric pin-numbering rules.  
See the reference document for details.


### How to reach Level 3

Two ways to reach it (**highest precedence first**):

1. **Define `/zephyr,user/serials`, `/zephyr,user/i2cs`, `/zephyr,user/spis`**  
   Set the list of UART devices to use in `/zephyr,user/serials`.  
   This will create Arduino `Serial`, `Serial1`, ... objects.  
   The same applies to `i2cs` and `spis` for `Wire/Wire1...` and `SPI/SPI1...`.

2. **Define board defaults via connector bus node labels**  
   If the board provides node labels such as `arduino_serial`, `arduino_i2c`, and `arduino_spi`,
   they will be used as defaults for `Serial`, `Wire`, and `SPI`.  
   The exact label names may vary depending on the connector model used by the board.


### How to reach Level 4

To correctly configure PWM and ADC, two independent items must be addressed:

1. **Pin association**: mapping PWM/ADC input/output pins to GPIO numbers  
2. **Channel provisioning**: PWM and ADC channel configuration

#### 1) Pin association
This is similar to configuring GPIO:

- Set GPIO lists in `/zephyr,user/pwm-pin-gpios` and `/zephyr,user/adc-pin-gpios`, **or**
- Provide connector mappings via the board’s nexus definitions (e.g., `pwm-map` and `io-channel-map`).

#### 2) Channel provisioning
You must provide channel lists for ArduinoCore-Zephyr:

- PWM channels: `/zephyr,user/pwms`
- ADC channels: `/zephyr,user/io-channels`

In most cases you will also need to configure the corresponding PWM and ADC nodes in devicetree.
See also the examples in `samples/drivers/adc/adc_dt` and `samples/basic/blinky_pwm`.


### How to reach Level 5

Level 5 supports special features of each board, and the way to achieve this varies by board.

It may require:
- adding definitions to `variant.h` or overlays,
- adding libraries to support the features, or
- adding features to Zephyr itself when necessary.
