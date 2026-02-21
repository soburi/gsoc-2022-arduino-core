#pragma once

#include "Stream.h"
#include <client_interface.hpp>

namespace arduino {

class Client : virtual public Stream, virtual public ClientInterface {
protected:
  uint8_t* rawIPAddress(IPAddress& addr); //TODO
};

};
