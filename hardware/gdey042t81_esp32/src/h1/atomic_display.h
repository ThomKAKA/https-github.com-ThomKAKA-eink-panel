#pragma once
#ifndef EINK_H1_ATOMIC_TEST
#error "H1 adapter is available only in the dedicated test environment"
#endif
#include <Arduino.h>
#include <SPI.h>
#include <gdey/GxEPD2_420_GDEY042T81.h>
#include "contract.h"

namespace eink::h1 {
// Private inheritance intentionally prevents callers from issuing extra EPD
// operations through the broad upstream API. No controller driver is copied.
class H1SafeGDEY042T81 final : private GxEPD2_420_GDEY042T81 {
 public:
  H1SafeGDEY042T81(int cs, int dc, int rst, int busy)
      : GxEPD2_420_GDEY042T81(cs, dc, rst, busy) {}
  H1SafeGDEY042T81(const H1SafeGDEY042T81&) = delete;
  H1SafeGDEY042T81& operator=(const H1SafeGDEY042T81&) = delete;
  H1SafeGDEY042T81(H1SafeGDEY042T81&&) = delete;
  H1SafeGDEY042T81& operator=(H1SafeGDEY042T81&&) = delete;

  bool coldInit(SPIClass& spi) {
    if (state_ != State::New || _busy_timeout != kTimeoutUs) return false;
    selectSPI(spi, SPISettings(4000000, MSBFIRST, SPI_MODE0));
    GxEPD2_420_GDEY042T81::init(115200, true, 10, false);
    selectFastFullUpdate(false);
    state_ = State::Initialized;
    return true;
  }

  bool prepareColdStartFullFrame(const std::uint8_t* bitmap, std::size_t bytes,
                                 int x, int y, int w, int h) {
    if (!canPrepare(state_, bitmap, bytes, x, y, w, h) ||
        !_initial_write || !_initial_refresh) return false;
    state_ = State::Preparing;
    // H1 takes responsibility for a complete cold-start RAM overwrite, NOT
    // retained display RAM. Valid full geometry cannot take _writeImage's
    // clipping early-return path in the pinned upstream implementation.
    _initial_write = false;
    GxEPD2_420_GDEY042T81::writeImageForFullRefresh(
        bitmap, x, y, w, h, kInvert, kMirrorY, kPgm);
    // Software completion only: SPI writes have no controller acknowledgement.
    state_ = State::Prepared;
    return true;
  }

  bool refreshOnce() {
    if (!canRefresh(state_)) return false;
    state_ = State::Finished;  // Consume the one-shot even if BUSY times out.
    GxEPD2_420_GDEY042T81::refresh(false);  // FINAL EPD operation.
    return true;
  }

 private:
  State state_ = State::New;
};
}  // namespace eink::h1
