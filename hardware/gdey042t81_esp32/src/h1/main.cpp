#ifdef EINK_H1_ATOMIC_TEST
// Required; missing private header is a build error, not a fallback.
#include "config.h"
#include "atomic_display.h"
#include "pattern.h"

namespace {
eink::h1::H1SafeGDEY042T81 display(EPD_CS, EPD_DC, EPD_RST, EPD_BUSY);
}
void setup() {
  Serial.begin(115200);
  Serial.println("H1_BOOT_COMPILE_PREFLIGHT_NOT_PHYSICAL_VERIFICATION");
  SPI.begin(EPD_SCK, -1, EPD_MOSI, EPD_CS);
  if (!display.coldInit(SPI) ||
      !display.prepareColdStartFullFrame(eink::h1::kPattern.data(),
          eink::h1::kPattern.size(), 0, 0, 400, 300)) {
    Serial.println("H1_PREPARATION_REJECTED");
    return;
  }
  const std::uint32_t start = micros();
  const bool invoked = display.refreshOnce();
  const std::uint32_t elapsed = std::uint32_t(micros() - start);
  const bool busy = digitalRead(EPD_BUSY) == HIGH;
  Serial.printf("H1 elapsed_us=%lu busy=%u\n", (unsigned long)elapsed, busy);
  Serial.println(!invoked || eink::h1::timedOutOrUnknown(elapsed, busy)
      ? "H1_FULL_TIMEOUT_OR_UNKNOWN"
      : "H1_SOFTWARE_RETURN_CONDITIONS_MET_NOT_DISPLAY_PASS");
  // No further display operations on ANY result. Not a sleep confirmation.
}
void loop() { delay(1000); }
#endif
