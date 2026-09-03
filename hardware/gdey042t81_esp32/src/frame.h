#pragma once

#include "hardware_config.h"

namespace eink {

// Fixed MONO1: 400x300, top-left origin, row-major, MSB first, 0=black, 1=white.
struct FrameView {
  const std::uint8_t* pixels;
  std::size_t size;
};

constexpr bool validFrame(FrameView frame) {
  return frame.pixels != nullptr && frame.size == config::kFrameBytes;
}

}  // namespace eink
