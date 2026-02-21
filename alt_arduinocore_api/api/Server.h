/*
 * Copyright (c) 2026 TOKITA Hiroshi
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#pragma once

#include "Stream.h"
#include <server_interface.hpp>

namespace arduino {

class Server : virtual public Print, virtual public ServerInterface {
};

};
