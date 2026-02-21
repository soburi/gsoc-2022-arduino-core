# SPDX-License-Identifier: Apache-2.0

list(APPEND CMAKE_MODULE_PATH ${ZEPHYR_BASE}/modules/nanopb)
include(nanopb)

set(ARDUINO_IDL_PROTO_DIR ${CMAKE_CURRENT_SOURCE_DIR}/proto)
set(ARDUINO_IDL_CLASS_PROTO_FILES
  print.proto
  stream.proto
  client.proto
  server.proto
  hardware_serial.proto
  hardware_i2c.proto
  hardware_spi.proto
  hardware_can.proto
  udp.proto
  pluggable_usb_module.proto
  printable.proto
)
set(ARDUINO_IDL_OPTS_PROTO ${ARDUINO_IDL_PROTO_DIR}/arduino_opts.proto)
set(ARDUINO_IDL_SHARED_PROTO_FILES
  common.proto
)
set(ARDUINO_IDL_PLUGIN ${CMAKE_CURRENT_SOURCE_DIR}/../../tools/protoc-gen-arduinoif)
set(ARDUINO_IDL_NANOPB_PROTO_DIR ${NANOPB_SRC_ROOT_FOLDER}/generator/proto)
set(ARDUINO_IDL_IF_OUTPUT_DIR ${CMAKE_CURRENT_BINARY_DIR}/generated/arduinoif)
set(ARDUINO_IDL_TYPE_HEADERS)
foreach(proto_file IN LISTS ARDUINO_IDL_SHARED_PROTO_FILES)
  get_filename_component(proto_stem ${proto_file} NAME_WE)
  list(APPEND ARDUINO_IDL_TYPE_HEADERS
    ${ARDUINO_IDL_IF_OUTPUT_DIR}/${proto_stem}_types.h)
endforeach()

set(ARDUINO_IDL_CLASS_PROTOS)
set(ARDUINO_IDL_CLASS_PROTO_REL_PATHS)
set(ARDUINO_IDL_IF_HEADERS)
foreach(proto_file IN LISTS ARDUINO_IDL_CLASS_PROTO_FILES)
  get_filename_component(proto_stem ${proto_file} NAME_WE)
  list(APPEND ARDUINO_IDL_CLASS_PROTOS
    ${ARDUINO_IDL_PROTO_DIR}/${proto_file})
  list(APPEND ARDUINO_IDL_CLASS_PROTO_REL_PATHS
    proto/${proto_file})
  list(APPEND ARDUINO_IDL_IF_HEADERS
    ${ARDUINO_IDL_IF_OUTPUT_DIR}/${proto_stem}_interface.hpp)
endforeach()
set(ARDUINO_IDL_PLUGIN_INPUT_PROTOS
  ${ARDUINO_IDL_CLASS_PROTOS}
)
foreach(proto_file IN LISTS ARDUINO_IDL_SHARED_PROTO_FILES)
  list(APPEND ARDUINO_IDL_PLUGIN_INPUT_PROTOS
    ${ARDUINO_IDL_PROTO_DIR}/${proto_file})
endforeach()

zephyr_library_named(arduinocore_idl)
zephyr_nanopb_sources(arduinocore_idl
  proto/google/protobuf/empty.proto
  proto/google/protobuf/wrappers.proto
  proto/arduino_opts.proto
  ${ARDUINO_IDL_CLASS_PROTO_REL_PATHS}
)

add_custom_command(
  OUTPUT ${ARDUINO_IDL_IF_HEADERS} ${ARDUINO_IDL_TYPE_HEADERS}
  COMMAND ${CMAKE_COMMAND} -E make_directory ${ARDUINO_IDL_IF_OUTPUT_DIR}
  COMMAND ${PROTOBUF_PROTOC_EXECUTABLE}
    --plugin=protoc-gen-arduinoif=${ARDUINO_IDL_PLUGIN}
    --arduinoif_out=${ARDUINO_IDL_IF_OUTPUT_DIR}
    --proto_path=${ARDUINO_IDL_PROTO_DIR}
    --proto_path=${ARDUINO_IDL_NANOPB_PROTO_DIR}
    ${ARDUINO_IDL_PLUGIN_INPUT_PROTOS}
  DEPENDS
    ${ARDUINO_IDL_PLUGIN_INPUT_PROTOS}
    ${ARDUINO_IDL_OPTS_PROTO}
    ${ARDUINO_IDL_PLUGIN}
  COMMENT "Generating C++ interface headers from Arduino IDL proto files"
  VERBATIM
)

add_custom_target(arduinocore_idl_generate_interfaces ALL DEPENDS ${ARDUINO_IDL_IF_HEADERS} ${ARDUINO_IDL_TYPE_HEADERS})
add_dependencies(arduinocore_idl arduinocore_idl_generate_interfaces)

zephyr_include_directories(${ARDUINO_IDL_IF_OUTPUT_DIR})
