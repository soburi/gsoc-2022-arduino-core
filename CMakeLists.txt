# SPDX-License-Identifier: Apache-2.0

if (CONFIG_ARDUINO_API)

  add_subdirectory(cores)
  add_subdirectory(libraries)

  if (IS_DIRECTORY variants/${BOARD})
    zephyr_include_directories(variants/${BOARD})
  else()
    zephyr_include_directories(variants/fallback)
  endif()

endif()

