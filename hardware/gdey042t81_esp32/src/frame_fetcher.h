#pragma once

#include <cstddef>
#include <cstdint>

namespace eink {

enum class FetchStatus { Disabled };
struct FetchOutcome {
  FetchStatus status;
  std::size_t bytes_received;
};

// H2 boundary only. No Wi-Fi/HTTP dependencies and no writes to the destination.
// A future implementation must validate a complete frame before it is displayed.
class FrameFetcher {
 public:
  FetchOutcome fetch(std::uint8_t* destination, std::size_t capacity) const {
    (void)destination;
    (void)capacity;
    return {FetchStatus::Disabled, 0};
  }
};

}  // namespace eink
