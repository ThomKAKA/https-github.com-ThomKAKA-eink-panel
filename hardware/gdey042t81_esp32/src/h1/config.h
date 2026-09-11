#pragma once
#if !defined(EINK_H1_ATOMIC_TEST) || !defined(EINK_BOARD_ESP32_M1) || !defined(ARDUINO_LOLIN32)
#error "H1 requires the dedicated ESP32-M1 / lolin32 environment"
#endif
#include "display_config.local.h"
static_assert(EPD_WIRING_CONFIRMED == 1 && H1_PRIVATE_PROFILE == 1);
static_assert(EPD_BUSY == 13 && EPD_RST == 12 && EPD_DC == 14 &&
              EPD_CS == 27 && EPD_SCK == 18 && EPD_MOSI == 23);
