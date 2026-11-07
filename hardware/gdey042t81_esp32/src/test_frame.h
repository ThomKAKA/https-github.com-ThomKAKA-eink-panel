#pragma once

#include <array>

#include "frame.h"

namespace eink::test_frame {
namespace detail {

using Bitmap = std::array<std::uint8_t, config::kFrameBytes>;

constexpr void blackPixel(Bitmap& frame, unsigned x, unsigned y) {
  frame[y * config::kRowBytes + x / 8] &=
      static_cast<std::uint8_t>(~(0x80u >> (x % 8)));
}

constexpr void blackRect(Bitmap& frame, unsigned x, unsigned y,
                         unsigned width, unsigned height) {
  for (unsigned row = y; row < y + height; ++row) {
    for (unsigned col = x; col < x + width; ++col) blackPixel(frame, col, row);
  }
}

constexpr Bitmap make(bool center_marker) {
  Bitmap frame{};
  for (auto& byte : frame) byte = 0xFF;
  for (unsigned x = 0; x < config::kWidth; ++x) {
    blackPixel(frame, x, 0);
    blackPixel(frame, x, config::kHeight - 1);
  }
  for (unsigned y = 0; y < config::kHeight; ++y) {
    blackPixel(frame, 0, y);
    blackPixel(frame, config::kWidth - 1, y);
  }
  // Deliberately asymmetric markers expose rotations and mirroring.
  blackRect(frame, 8, 8, 16, 16);
  blackRect(frame, 368, 8, 24, 8);
  blackRect(frame, 8, 268, 8, 24);
  blackRect(frame, 368, 276, 24, 16);
  for (unsigned i = 0; i < 200; ++i) blackPixel(frame, 40 + i, 40 + i);
  // Adjacent byte-boundary probes: x=7 and x=8 on separate rows.
  blackPixel(frame, 7, 60);
  blackPixel(frame, 8, 61);
  for (unsigned x = 40; x < 360; x += 16) blackRect(frame, x, 260, 8, 8);
  if (center_marker) blackRect(frame, 180, 130, 40, 30);
  return frame;
}

}  // namespace detail

// Generated at compile time into read-only data; no binary assets or runtime heap.
inline constexpr auto kFrameA = detail::make(false);
inline constexpr auto kFrameB = detail::make(true);
static_assert(kFrameA.size() == 15000 && kFrameB.size() == 15000);

inline FrameView frameA() { return {kFrameA.data(), kFrameA.size()}; }
inline FrameView frameB() { return {kFrameB.data(), kFrameB.size()}; }

}  // namespace eink::test_frame
