Board Configuration Reference
=============================

A. Devicetree node: `/zephyr,user`
----------------------------------

### Pin mapping

#### `digital-pin-gpios`
- **Type:** `phandle-array` (GPIO specifiers)
- **Meaning:** Ordered Arduino digital pin list.
- **Affects:**
  - Defines `D0`, `D1`, … from the list order.
  - Switches numeric pin interpretation to **Arduino-index numbering** (index into this list).
- **Precedence:** higher than connector-derived digital namespace (`gpio-map`).
- **Notes:**
  - If absent, numeric pins use **global GPIO numbering**.
  - If absent, `D*` may still exist via connector `gpio-map` (see below).
  
- **Example**
    ```
    / {
        zephyr,user {
            digital-pin-gpios = <&arduino_header 6 0>,	/* Digital */
                        <&arduino_header 7 0>;
                        ...
                        <&arduino_header 19 0>;
                        <&arduino_header 0 0>;	/* Analog */
                        <&arduino_header 1 0>;
                        ...
                        <&arduino_header 5 0>;
                        <&arduino_header 20 0>;	/* SDA */
                        <&arduino_header 21 0>;	/* SCL */
                        <&gpio0 13 GPIO_ACTIVE_LOW>;	/* LED0 */
            };
        };
    };
    ```

#### `adc-pin-gpios`
- **Meaning:** Ordered list of GPIO pins treated as “ADC-capable pins” for Arduino mapping.
- **Affects:** ADC pin association (pin ↔ ADC channel mapping).
- **Precedence:** overrides connector `io-channel-map` (if present).
- **Notes:**
  - Association only; does not provision ADC channels (see `io-channels`).
  - **The list index defines the Arduino analog pin index** (e.g., index 0 corresponds to A0) and **associates with the corresponding provisioned `io-channels` entry by index**.

#### `pwm-pin-gpios`
- **Type:** `phandle-array` (GPIO specifiers)
- **Meaning:** Ordered list of GPIO pins treated as “PWM-capable pins” for Arduino mapping.
- **Affects:** PWM pin association (pin ↔ PWM channel mapping).
- **Precedence:** overrides connector `pwm-map` (if present).
- **Notes:**
  - Association only; does not provision PWM channels (see `pwms`).
  - **The list index defines the Arduino PWM-capable pin index** and **associates with the corresponding provisioned `pwms` entry by index**.

#### `builtin-led-gpios`
- **Type:** GPIO specifier
- **Meaning:** Explicit built-in LED GPIO.
- **Affects:** Derivation of `LED_BUILTIN` when `variant.h` does not override it.
- **Precedence:** higher than board `led0` alias, lower than `variant.h` `LED_BUILTIN`.
- **Notes:** If `LED_BUILTIN` is defined in `variant.h`, this property is ignored for that purpose.




### Bus node lists

#### `serials`
- **Type:** phandle list (UART devices)
- **Meaning:** List of UART devices backing Arduino Serial instances.
- **Affects:** `Serial`, `Serial1`, …
- **Precedence:** overrides board default bus label (commonly `arduino_serial`).
- **Example**
    ```
    / {
        zephyr,user {
                serials = <&uart0, &uart1>;
        };
    };
    ```

#### `i2cs`
- **Type:** phandle list (I2C controller devices)
- **Meaning:** List of I2C devices backing Arduino Wire instances.
- **Affects:** `Wire`, `Wire1`, …
- **Precedence:** overrides board default bus label (commonly `arduino_i2c`).
- **Example**
    ```
    / {
        zephyr,user {
                i2cs = <&i2c0, &i2c1>;
        };
    };
    ```

#### `spis`
- **Type:** phandle list (SPI controller devices)
- **Meaning:** List of SPI devices backing Arduino SPI instances.
- **Affects:** `SPI`, `SPI1`, …
- **Precedence:** overrides board default bus label (commonly `arduino_spi`).

### Port provisioning

#### `io-channels`
- **Type:** `io-channels` phandle-array specifiers
- **Meaning:** Declares the ADC controller/channel specifiers used by ArduinoCore-Zephyr.
- **Affects:** ADC channel provisioning (ADC availability).
- **Precedence:** primary/required provisioning source for ADC behavior.
- **Notes:** Without provisioning, ADC is considered unsupported regardless of pin association.

#### `pwms`
- **Type:** PWM phandle-array specifiers
- **Meaning:** Declares PWM controller/channel specifiers used by ArduinoCore-Zephyr.
- **Affects:** PWM channel provisioning (PWM availability).
- **Precedence:** primary/required provisioning source for PWM behavior.
- **Notes:** Without provisioning, PWM output is considered unsupported regardless of pin association.



B. Board devicetree constructs (board-provided defaults)
--------------------------------------------------------

### `gpio-map` (connector digital namespace)
- **Location:** connector nexus node (board-defined; e.g., Arduino-compatible header node)
- **Type:** nexus mapping (`gpio-map`, `gpio-map-mask`, `gpio-map-pass-thru`, …)
- **Meaning:** Board-defined mapping that establishes an Arduino-style digital namespace from the connector model.
- **Affects:** **Defines `D0`, `D1`, … when `/zephyr,user/digital-pin-gpios` is absent.**
- **Precedence:** used only if `/zephyr,user/digital-pin-gpios` is not present.
- **Notes:** Does **not** change numeric pin interpretation by itself; numeric pins remain global-numbered unless `digital-pin-gpios` exists.

---

### `io-channel-map` (connector ADC association)
- **Location:** connector nexus node (board-defined)
- **Type:** nexus mapping (`io-channel-map`, `io-channel-map-mask`, `io-channel-map-pass-thru`, …)
- **Meaning:** Board-defined ADC pin association through connector mapping.
- **Affects:** ADC association when `/zephyr,user/adc-pin-gpios` is absent.
- **Precedence:** lower than `/zephyr,user/adc-pin-gpios`.
- **Notes:** Association only; ADC provisioning still requires `/zephyr,user/io-channels`.

---

### `pwm-map` (connector PWM association)
- **Location:** connector nexus node (board-defined)
- **Type:** nexus mapping (`pwm-map`, `pwm-map-mask`, `pwm-map-pass-thru`, …)
- **Meaning:** Board-defined PWM pin association through connector mapping.
- **Affects:** PWM association when `/zephyr,user/pwm-pin-gpios` is absent.
- **Precedence:** lower than `/zephyr,user/pwm-pin-gpios`.
- **Notes:** Association only; PWM provisioning still requires `/zephyr,user/pwms`.

---

### Node label: `arduino_i2c`
- **Location:** board devicetree node label
- **Type:** label pointing to an I2C controller node
- **Meaning:** Board default I2C controller for Arduino `Wire`.
- **Affects:** Used when `/zephyr,user/i2cs` is absent.
- **Precedence:** lower than `/zephyr,user/i2cs`.
- **Required:** **No.** (Board-defined convention.)
- **Notes:** The exact node label name used as a default is **board-defined**; `arduino_i2c` is a common convention.

---

### Node label: `arduino_serial`
- **Location:** board devicetree node label
- **Type:** label pointing to a UART controller node
- **Meaning:** Board default UART for Arduino `Serial`.
- **Affects:** Used when `/zephyr,user/serials` is absent.
- **Precedence:** lower than `/zephyr,user/serials`.
- **Required:** **No.** (Board-defined convention.)
- **Notes:** The exact node label name used as a default is **board-defined**; `arduino_serial` is a common convention.

### Node label: `arduino_spi`
- **Location:** board devicetree node label
- **Type:** label pointing to an SPI controller node
- **Meaning:** Board default SPI controller for Arduino `SPI`.
- **Affects:** Used when `/zephyr,user/spis` is absent.
- **Precedence:** lower than `/zephyr,user/spis`.
- **Required:** **No.** (Board-defined convention.)
- **Notes:** The exact node label name used as a default is **board-defined**; `arduino_spi` is a common convention.


### Alias: `led0`
- **Location:** devicetree `/aliases`
- **Type:** alias pointing to an LED node
- **Meaning:** Board default built-in LED (Zephyr convention).
- **Affects:** Used to derive `LED_BUILTIN` if neither `variant.h` `LED_BUILTIN` nor `/zephyr,user/builtin-led-gpios` is provided.
- **Precedence:** lowest in the built-in LED chain.
- **Notes:** If `/zephyr,user/digital-pin-gpios` is absent, the derived `LED_BUILTIN` uses the **global GPIO number** (matching numeric pin interpretation in that mode).


## C. `variant.h` symbols (highest-precedence C/C++ overrides)

### `LED_BUILTIN`
- **Location:** board-specific `variant.h`
- **Type:** C/C++ macro (integer Arduino pin number)
- **Meaning:** Explicit Arduino-visible LED pin number.
- **Affects:** `LED_BUILTIN` behavior regardless of devicetree LED selection.
- **Precedence:** highest for built-in LED pin numbering.

---

## D. Derived behavior switches (implicit rules)

### Numeric pin interpretation
- **Switch condition:** presence of `/zephyr,user/digital-pin-gpios`
- **If present:** numeric `pinNumber` = Arduino-index into `digital-pin-gpios`
- **If absent:** numeric `pinNumber` = global GPIO number
- **Notes:** **Global GPIO numbering follows Zephyr’s GPIO pin numbering model; the exact mapping is defined by the board devicetree and GPIO driver implementation.**

### ADC usability
- **Requires provisioning:** `/zephyr,user/io-channels`
- **Association source:** `/zephyr,user/adc-pin-gpios` or connector `io-channel-map`

### PWM usability
- **Requires provisioning:** `/zephyr,user/pwms`
- **Association source:** `/zephyr,user/pwm-pin-gpios` or connector `pwm-map`
