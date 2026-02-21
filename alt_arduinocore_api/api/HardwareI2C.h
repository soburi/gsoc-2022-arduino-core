/*
 * Copyright (c) 2026 TOKITA Hiroshi
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#pragma once

#include "Stream.h"
#include <hardware_i2c_interface.hpp>

namespace arduino {

class HardwareI2C : virtual public Stream, virtual public HardwareI2CInterface {
};

};
