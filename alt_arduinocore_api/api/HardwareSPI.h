/*
 * Copyright (c) 2026 TOKITA Hiroshi
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#pragma once

#include "Stream.h"
#include <hardware_spi_interface.hpp>

namespace arduino {

class HardwareSPI : virtual public HardwareSPIInterface {
};

typedef HardwareSPI SPIClass;
};
