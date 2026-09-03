#pragma once

// EXAMPLE ONLY. These are NOT facts about your ESP32 board or adapter.
// Copy to display_config.local.h, check the actual wiring, then change ONLY
// the private file. Never put credentials into this tracked example.
#define EPD_WIRING_CONFIRMED 0
#define EPD_CS 5
#define EPD_DC 17
#define EPD_RST 16
#define EPD_BUSY 4
#define EPD_SCK 18
#define EPD_MOSI 23

// Reserved for H2. P1.5 neither reads these values nor starts Wi-Fi.
#define WIFI_SSID ""
#define WIFI_PASSWORD ""

// 0 = H0 ASCII/geometry pattern; 1 = H1 compiled-in raw frame.
// Only select H1 after visually accepting H0 on the real screen.
#define EPD_BRINGUP_STAGE 0
// Opt-in, finite H1 exercise: FULL, five PARTIAL updates, then FULL, then stop.
#define EPD_RUN_REFRESH_DEMO 0
#define EPD_MAX_FAST_UPDATES 5
#define EPD_MIN_REFRESH_INTERVAL_MS 5000UL
// 0 = prefer PARTIAL; 1 = prefer FAST_FULL. Cleanup FULL is always non-fast.
#define EPD_PREFER_FAST_FULL 0
#define EPD_SPI_HZ 4000000UL
#define EPD_RESET_DURATION_MS 10
