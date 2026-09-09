#pragma once

// ESP32-M1 schematic mapping, not physical wiring acceptance.
// Evidence: docs/STEP013_HARDWARE_AUDIT.md. Keep this tracked profile guarded.
// Only a separately reviewed, ignored display_config.local.h can authorize GPIO.
#define EPD_WIRING_CONFIRMED 0
#define EPD_CS 27
#define EPD_DC 14
#define EPD_RST 12
#define EPD_BUSY 13
#define EPD_SCK 18
#define EPD_MOSI 23

// Preserve the existing H0 defaults. No networking or H1 demonstration.
#define WIFI_SSID ""
#define WIFI_PASSWORD ""
#define EPD_BRINGUP_STAGE 0
#define EPD_RUN_REFRESH_DEMO 0
#define EPD_MAX_FAST_UPDATES 5
#define EPD_MIN_REFRESH_INTERVAL_MS 5000UL
#define EPD_PREFER_FAST_FULL 0
#define EPD_SPI_HZ 4000000UL
#define EPD_RESET_DURATION_MS 10
