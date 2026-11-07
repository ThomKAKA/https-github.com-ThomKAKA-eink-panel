#pragma once

#include <cstdint>

namespace eink {

// FastFull is a fast full-screen waveform, not a separate image region mode.
enum class RefreshMode { None, Full, FastFull, Partial };

class RefreshPolicy {
 public:
  RefreshPolicy(std::uint8_t max_fast_updates, std::uint32_t min_interval_ms,
                bool prefer_fast_full = false);

  RefreshMode decide(bool content_changed, std::uint32_t now_ms) const;
  // Call only after the driver returns Submitted. Failures do not advance state.
  void recordSuccess(RefreshMode mode, std::uint32_t completed_at_ms);
  std::uint8_t fastUpdateCount() const { return fast_update_count_; }

 private:
  std::uint8_t max_fast_updates_;
  std::uint32_t min_interval_ms_;
  bool prefer_fast_full_;
  bool has_frame_ = false;
  std::uint8_t fast_update_count_ = 0;
  std::uint32_t last_completed_at_ms_ = 0;
};

const char* refreshModeName(RefreshMode mode);

}  // namespace eink
