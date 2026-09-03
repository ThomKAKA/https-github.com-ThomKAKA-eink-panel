#pragma once

#include <cstddef>
#include <cstdint>

#if __has_include("display_config.local.h")
#include "display_config.local.h"
#define EINK_HAS_LOCAL_CONFIG 1
#else
#include "display_config.example.h"
#define EINK_HAS_LOCAL_CONFIG 0
#endif

namespace eink::config {

inline constexpr std::uint16_t kWidth = 400;
inline constexpr std::uint16_t kHeight = 300;
inline constexpr std::size_t kRowBytes = kWidth / 8;
inline constexpr std::size_t kFrameBytes = kRowBytes * kHeight;
inline constexpr bool kWiringConfirmed =
    EINK_HAS_LOCAL_CONFIG && EPD_WIRING_CONFIRMED == 1;
inline constexpr unsigned kBringupStage = EPD_BRINGUP_STAGE;
inline constexpr bool kRunRefreshDemo = EPD_RUN_REFRESH_DEMO == 1;
inline constexpr std::uint8_t kMaxFastUpdates = EPD_MAX_FAST_UPDATES;
inline constexpr std::uint32_t kMinRefreshIntervalMs = EPD_MIN_REFRESH_INTERVAL_MS;
inline constexpr bool kPreferFastFull = EPD_PREFER_FAST_FULL == 1;
inline constexpr std::uint32_t kSpiHz = EPD_SPI_HZ;
inline constexpr std::uint16_t kResetDurationMs = EPD_RESET_DURATION_MS;
inline constexpr std::uint32_t kSerialBaud = 115200;
inline constexpr std::uint32_t kSerialStartupMs = 250;
inline constexpr std::uint32_t kLoopIdleMs = 50;

static_assert(kWidth % 8 == 0 && kFrameBytes == 15000, "Invalid MONO1 geometry");
static_assert(EPD_BRINGUP_STAGE == 0 || EPD_BRINGUP_STAGE == 1, "Select H0 or H1");
static_assert(!kRunRefreshDemo || kBringupStage == 1, "Refresh demo requires H1");
static_assert(EPD_MAX_FAST_UPDATES >= 0 && EPD_MAX_FAST_UPDATES <= 254,
              "Fast-update limit must be 0..254");
static_assert(EPD_MIN_REFRESH_INTERVAL_MS >= 1000UL &&
                  EPD_MIN_REFRESH_INTERVAL_MS < 0x80000000UL,
              "Use seconds-scale refresh intervals below half the millis range");
static_assert(EPD_SPI_HZ > 0 && EPD_SPI_HZ <= 4000000UL,
              "Bring-up SPI clock must be within 1..4000000 Hz");

}  // namespace eink::config
