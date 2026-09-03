#include <Arduino.h>
#include <cstring>

#include "display_driver.h"
#include "frame_fetcher.h"
#include "hardware_config.h"
#include "refresh_policy.h"
#include "test_frame.h"

namespace {

eink::DisplayDriver driver;
eink::RefreshPolicy policy(eink::config::kMaxFastUpdates,
                           eink::config::kMinRefreshIntervalMs,
                           eink::config::kPreferFastFull);
eink::FrameView last_frame{nullptr, 0};
bool ready = false;
unsigned demo_updates = 0;

bool submit(eink::FrameView frame, eink::RefreshMode mode) {
  const auto result = driver.displayFrame(frame, mode);
  if (result == eink::DisplayResult::Submitted) {
    policy.recordSuccess(mode, millis());
    last_frame = frame;  // Both local test frames have static, immutable storage.
  }
  Serial.printf("FRAME mode=%s result=%s fast_count=%u\n",
                eink::refreshModeName(mode), eink::displayResultName(result),
                static_cast<unsigned>(policy.fastUpdateCount()));
  return result == eink::DisplayResult::Submitted;
}

}  // namespace

void setup() {
  Serial.begin(eink::config::kSerialBaud);
  delay(eink::config::kSerialStartupMs);
  Serial.println("GDEY042T81 400x300 | P1.5 BRING-UP SCAFFOLD");
  Serial.println("Source=LOCAL_TEST_FRAME | FrameFetcher=DISABLED | Wi-Fi=OFF");
  const auto result = driver.begin();
  Serial.printf("INIT result=%s\n", eink::displayResultName(result));
  if (result != eink::DisplayResult::Submitted) {
    Serial.println("STOP: confirm the real board/adapter and private pin config first.");
    return;
  }
  if (eink::config::kBringupStage == 0) {
    const auto pattern_result = driver.showTestPattern();
    Serial.printf("H0 result=%s\n", eink::displayResultName(pattern_result));
    Serial.println("HOLD. Visually verify H0 before selecting H1; no automatic retry.");
    return;
  }
  ready = submit(eink::test_frame::frameA(), policy.decide(true, millis()));
  Serial.println("H1 local raw frame. Compare all edges, polarity and asymmetric markers.");
  if (!eink::config::kRunRefreshDemo) Serial.println("HOLD. Refresh demo is disabled.");
}

void loop() {
  if (ready && eink::config::kRunRefreshDemo) {
    // One bounded exercise, not an animation: N cheap updates, then cleanup FULL.
    const unsigned target_updates = eink::config::kMaxFastUpdates + 1u;
    if (demo_updates < target_updates) {
      const auto frame = demo_updates % 2 == 0 ? eink::test_frame::frameB()
                                                : eink::test_frame::frameA();
      const bool changed = !eink::validFrame(last_frame) ||
          std::memcmp(frame.pixels, last_frame.pixels, frame.size) != 0;
      const auto mode = policy.decide(changed, millis());
      if (mode != eink::RefreshMode::None) {
        ready = submit(frame, mode);
        if (ready) ++demo_updates;
        if (!ready) Serial.println("STOP: last physical image retained; check Serial/wiring.");
      }
    } else {
      ready = false;
      Serial.println("DEMO FINISHED. HOLD; inspect ghosting before any further test.");
    }
  }
  delay(eink::config::kLoopIdleMs);
}
