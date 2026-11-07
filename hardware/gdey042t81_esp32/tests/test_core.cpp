// Host-only tests: no Arduino, GxEPD2, SPI or hardware required.
#include <cassert>
#include <cstring>
#include <iostream>

#include "frame_fetcher.h"
#include "refresh_policy.h"
#include "test_frame.h"

using eink::RefreshMode;
using eink::RefreshPolicy;

void firstFrameAndFailure() {
  RefreshPolicy policy(5, 5000);
  assert(policy.decide(true, 0) == RefreshMode::Full);
  // A failed driver attempt is intentionally NOT recorded.
  assert(policy.decide(true, 9000) == RefreshMode::Full);
  policy.recordSuccess(RefreshMode::None, 9000);
  assert(policy.decide(true, 9000) == RefreshMode::Full);
}

void unchangedAndThrottled() {
  RefreshPolicy policy(5, 5000);
  policy.recordSuccess(RefreshMode::Full, 1000);
  assert(policy.decide(true, 5999) == RefreshMode::None);
  assert(policy.decide(false, 6000) == RefreshMode::None);
  assert(policy.decide(true, 6000) == RefreshMode::Partial);
}

void fivePartialThenFull() {
  RefreshPolicy policy(5, 5000);
  policy.recordSuccess(RefreshMode::Full, 0);
  for (unsigned i = 1; i <= 5; ++i) {
    assert(policy.decide(true, i * 5000) == RefreshMode::Partial);
    policy.recordSuccess(RefreshMode::Partial, i * 5000);
    assert(policy.fastUpdateCount() == i);
  }
  assert(policy.decide(false, 30000) == RefreshMode::None);
  assert(policy.decide(true, 30000) == RefreshMode::Full);
  policy.recordSuccess(RefreshMode::Full, 30000);
  assert(policy.fastUpdateCount() == 0);
  assert(policy.decide(true, 35000) == RefreshMode::Partial);
}

void fastFullAndZeroLimit() {
  RefreshPolicy fast(1, 5000, true);
  assert(fast.decide(true, 0) == RefreshMode::Full);
  fast.recordSuccess(RefreshMode::Full, 0);
  assert(fast.decide(true, 5000) == RefreshMode::FastFull);
  fast.recordSuccess(RefreshMode::FastFull, 5000);
  assert(fast.decide(true, 10000) == RefreshMode::Full);
  RefreshPolicy full_only(0, 5000);
  full_only.recordSuccess(RefreshMode::Full, 0);
  assert(full_only.decide(true, 5000) == RefreshMode::Full);
}

void millisWraparound() {
  RefreshPolicy policy(5, 5000);
  policy.recordSuccess(RefreshMode::Full, 0xFFFFFF00u);
  assert(policy.decide(true, 0x00000010u) == RefreshMode::None);
  assert(policy.decide(true, 0x00001288u) == RefreshMode::Partial);
}

void frameValidationAndLayout() {
  const auto a = eink::test_frame::frameA();
  const auto b = eink::test_frame::frameB();
  assert(eink::validFrame(a) && a.size == 15000);
  assert(!eink::validFrame({nullptr, 15000}));
  assert(!eink::validFrame({a.pixels, 14999}));
  assert(!eink::validFrame({a.pixels, 15001}));
  assert(a.pixels[0] == 0x00);  // Top border, black.
  assert(a.pixels[30 * 50 + 12] == 0xFF);  // White interior.
  assert(a.pixels[60 * 50] == 0x7E);  // x=0 border and x=7 probe.
  assert(a.pixels[61 * 50 + 1] == 0x7F);  // x=8 probe, MSB first.
  assert(a.pixels[150 * 50 + 24] == 0xFF);
  assert(b.pixels[150 * 50 + 24] == 0x00);  // Only B has a center block.
  assert(std::memcmp(a.pixels, b.pixels, a.size) != 0);
}

void disabledFetcherPreservesBuffer() {
  std::uint8_t buffer[4] = {1, 2, 3, 4};
  const eink::FrameFetcher fetcher;
  const auto result = fetcher.fetch(buffer, sizeof(buffer));
  assert(result.status == eink::FetchStatus::Disabled && result.bytes_received == 0);
  assert(buffer[0] == 1 && buffer[3] == 4);
  assert(fetcher.fetch(nullptr, 0).status == eink::FetchStatus::Disabled);
}

int main() {
  firstFrameAndFailure();
  unchangedAndThrottled();
  fivePartialThenFull();
  fastFullAndZeroLimit();
  millisWraparound();
  frameValidationAndLayout();
  disabledFetcherPreservesBuffer();
  std::cout << "7 core test groups passed\n";
}
