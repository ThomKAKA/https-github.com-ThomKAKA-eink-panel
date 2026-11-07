#include "display_driver.h"

#include <Arduino.h>
#include <GxEPD2_BW.h>
#include <SPI.h>

namespace eink {
namespace {

GxEPD2_BW<GxEPD2_420_GDEY042T81, GxEPD2_420_GDEY042T81::HEIGHT> display(
    GxEPD2_420_GDEY042T81(EPD_CS, EPD_DC, EPD_RST, EPD_BUSY));
static_assert(config::kWidth == GxEPD2_420_GDEY042T81::WIDTH);
static_assert(config::kHeight == GxEPD2_420_GDEY042T81::HEIGHT);

}  // namespace

DisplayResult DisplayDriver::begin() {
  // Do not touch any display GPIO unless the private configuration was confirmed.
  if (!config::kWiringConfirmed) return DisplayResult::ConfigUnconfirmed;
  SPI.begin(EPD_SCK, -1, EPD_MOSI, EPD_CS);
  display.init(config::kSerialBaud, true, config::kResetDurationMs, false,
               SPI, SPISettings(config::kSpiHz, MSBFIRST, SPI_MODE0));
  display.setRotation(0);
  display.setFullWindow();
  display.epd2.selectFastFullUpdate(false);
  initialized_ = true;
  has_frame_ = false;
  return DisplayResult::Submitted;
}

DisplayResult DisplayDriver::showTestPattern() {
  if (!initialized_) return DisplayResult::NotInitialized;
  display.epd2.selectFastFullUpdate(false);
  display.fillScreen(GxEPD_WHITE);  // Clear drawing RAM; GxEPD2 owns the initial refresh sequence.
  display.setTextColor(GxEPD_BLACK);
  display.setTextSize(2);
  display.setCursor(20, 20);
  display.print("E-INK TEST");
  display.setCursor(20, 52);
  display.print("400x300");
  display.setCursor(20, 84);
  display.print("GDEY042T81");
  display.fillRect(20, 140, 100, 60, GxEPD_BLACK);
  display.drawRect(160, 140, 100, 60, GxEPD_BLACK);
  display.drawFastHLine(20, 240, config::kWidth - 40, GxEPD_BLACK);
  display.drawRect(0, 0, config::kWidth, config::kHeight, GxEPD_BLACK);
  display.display(false);
  return finishRefresh();
}

DisplayResult DisplayDriver::displayFrame(FrameView frame, RefreshMode mode) {
  if (!initialized_) return DisplayResult::NotInitialized;
  if (!validFrame(frame)) return DisplayResult::InvalidFrame;
  if (mode == RefreshMode::None || (!has_frame_ && mode != RefreshMode::Full)) {
    return DisplayResult::InvalidRefreshMode;
  }
  // Cleanup FULL must disable the library's default fast-full waveform.
  display.epd2.selectFastFullUpdate(mode == RefreshMode::FastFull);
  if (mode == RefreshMode::Partial) {
    display.epd2.writeImage(frame.pixels, 0, 0, config::kWidth, config::kHeight);
  } else {
    display.epd2.writeImageForFullRefresh(
        frame.pixels, 0, 0, config::kWidth, config::kHeight);
  }
  display.epd2.refresh(mode == RefreshMode::Partial);
  // GxEPD2's methods return void. Catch BUSY still active, but do not claim pixel ACK.
  if (digitalRead(EPD_BUSY) == HIGH) {
    initialized_ = false;
    return DisplayResult::BusyActive;
  }
  // Differential refresh requires current and previous controller RAM to agree.
  display.epd2.writeImageAgain(frame.pixels, 0, 0, config::kWidth, config::kHeight);
  display.epd2.powerOff();  // Disable panel driving voltages; not ESP32 deep sleep.
  return finishRefresh();
}

DisplayResult DisplayDriver::finishRefresh() {
  if (digitalRead(EPD_BUSY) == HIGH) {
    initialized_ = false;  // Stop; do not auto-clear or repeatedly flash an error page.
    return DisplayResult::BusyActive;
  }
  has_frame_ = true;
  return DisplayResult::Submitted;
}

const char* displayResultName(DisplayResult result) {
  switch (result) {
    case DisplayResult::Submitted: return "SUBMITTED_NOT_VISUALLY_VERIFIED";
    case DisplayResult::ConfigUnconfirmed: return "CONFIG_UNCONFIRMED";
    case DisplayResult::NotInitialized: return "NOT_INITIALIZED";
    case DisplayResult::InvalidFrame: return "INVALID_FRAME";
    case DisplayResult::InvalidRefreshMode: return "INVALID_REFRESH_MODE";
    case DisplayResult::BusyActive: return "BUSY_ACTIVE_CHECK_WIRING";
  }
  return "UNKNOWN";
}

}  // namespace eink
