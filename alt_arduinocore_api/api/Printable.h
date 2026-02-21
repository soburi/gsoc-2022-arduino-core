/*
 * Copyright (c) 2026 TOKITA Hiroshi
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#pragma once

namespace arduino {
	class Print;
};

#include <printable_interface.hpp>

namespace arduino {

class Printable : virtual public PrintableInterface {
};

}
