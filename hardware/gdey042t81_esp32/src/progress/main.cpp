#ifdef EINK_PROGRESS_EMBEDDED_TEST
#include "config.h"
#include "../h1/atomic_display.h"
#include "progress_frame.h"
#include <array>
#include <cstring>

static_assert(progress_frame_length == eink::h1::kBytes, "Complete frame required");
static_assert(progress_frame_width == 400 && progress_frame_height == 300 &&
              progress_frame_stride == 50, "Frame geometry mismatch");
static_assert(progress_frame_coordinate == 'T', "Transport frame required");

namespace {
std::array<std::uint8_t, eink::h1::kBytes> frame_ram{};
eink::h1::H1SafeGDEY042T81 display(EPD_CS, EPD_DC, EPD_RST, EPD_BUSY);
}

void setup() {
  Serial.begin(115200);
  Serial.println("PROGRESS_BOOT_NOT_PHYSICAL_VERIFICATION");
  // ESP32 memory-mapped read-only data -> complete persistent RAM. No transform.
  std::memcpy(frame_ram.data(), progress_frame, frame_ram.size());
  SPI.begin(EPD_SCK, -1, EPD_MOSI, EPD_CS);
  if (!display.coldInit(SPI) ||
      !display.prepareColdStartFullFrame(frame_ram.data(), frame_ram.size(), 0, 0, 400, 300)) {
    Serial.println("PROGRESS_PREPARATION_REJECTED");
    return;
  }
  const std::uint32_t start = micros();
  const bool invoked = display.refreshOnce();
  const std::uint32_t elapsed = std::uint32_t(micros() - start);
  const bool busy = digitalRead(EPD_BUSY) == HIGH;
  Serial.printf("PROGRESS elapsed_us=%lu busy=%u\n", (unsigned long)elapsed, busy);
  Serial.println(!invoked || eink::h1::timedOutOrUnknown(elapsed, busy)
      ? "PROGRESS_FULL_TIMEOUT_OR_UNKNOWN"
      : "PROGRESS_SOFTWARE_RETURN_CONDITIONS_MET_NOT_DISPLAY_PASS");
  // Final EPD operation was refreshOnce, regardless of result. No sleep claim.
}
void loop() { delay(1000); }
#endif
