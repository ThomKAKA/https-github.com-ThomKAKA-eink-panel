#pragma once
#include <array>
#include <cstdint>
#include "contract.h"

namespace eink::h1 {
// Same geometric content as the local H0 pattern; no vendor driver/assets.
constexpr auto makePattern() {
  std::array<std::uint8_t, kBytes> frame{};
  for (unsigned y = 0; y < 300; ++y) {
    for (unsigned x = 0; x < 400; ++x) {
      const bool border = x < 4 || x >= 396 || y < 4 || y >= 296;
      const bool solid = x >= 24 && x < 72 && y >= 24 && y < 72;
      const bool box = x >= 328 && x < 376 && y >= 24 && y < 72 &&
          (x < 332 || x >= 372 || y < 28 || y >= 68);
      const bool center = x >= 160 && x < 240 && y >= 120 && y < 180;
      const bool cross = (x >= 198 && x < 202) || (y >= 148 && y < 152);
      if (!(border || solid || box || center || cross))
        frame[y * 50 + x / 8] |= std::uint8_t(0x80u >> (x % 8));
    }
  }
  return frame;
}
inline constexpr auto kPattern = makePattern();
static_assert(kPattern.size() == 15000);
}  // namespace eink::h1
