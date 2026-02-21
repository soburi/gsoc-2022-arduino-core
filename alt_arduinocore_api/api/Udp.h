/*
 * Copyright (c) 2026 TOKITA Hiroshi
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#pragma once

#include "Stream.h"
#include <udp_interface.hpp>

namespace arduino {

class Udp : virtual public Stream, virtual public UDPInterface {
protected:
  uint8_t* rawIPAddress(IPAddress& addr); //TODO
}

};
