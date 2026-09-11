#pragma once
#include <cstddef>
#include <cstdint>

namespace eink::h1 {
enum class State { New, Initialized, Preparing, Prepared, Finished };
inline constexpr std::size_t kBytes = 15000;
inline constexpr bool kMirrorY = true;
inline constexpr bool kInvert = false;
inline constexpr bool kPgm = false;
inline constexpr std::uint32_t kTimeoutUs = 10000000;

constexpr bool canPrepare(State state, const std::uint8_t* pixels,
                          std::size_t bytes, int x, int y, int w, int h) {
  return state == State::Initialized && pixels != nullptr && bytes == kBytes &&
         x == 0 && y == 0 && w == 400 && h == 300;
}
constexpr bool canRefresh(State state) { return state == State::Prepared; }
constexpr bool timedOutOrUnknown(std::uint32_t elapsed, bool busy) {
  return busy || elapsed >= kTimeoutUs;
}
inline constexpr std::uint8_t kProbe = 0;
static_assert(canPrepare(State::Initialized, &kProbe, kBytes, 0, 0, 400, 300));
static_assert(!canPrepare(State::Initialized, nullptr, kBytes, 0, 0, 400, 300));
static_assert(!canPrepare(State::Initialized, &kProbe, kBytes - 1, 0, 0, 400, 300));
static_assert(!canPrepare(State::Initialized, &kProbe, kBytes + 1, 0, 0, 400, 300));
static_assert(!canPrepare(State::Initialized, &kProbe, kBytes, 1, 0, 400, 300));
static_assert(!canPrepare(State::Initialized, &kProbe, kBytes, 0, 1, 400, 300));
static_assert(!canPrepare(State::Initialized, &kProbe, kBytes, 0, 0, 399, 300));
static_assert(!canPrepare(State::Initialized, &kProbe, kBytes, 0, 0, 400, 299));
static_assert(!canPrepare(State::New, &kProbe, kBytes, 0, 0, 400, 300));
static_assert(!canPrepare(State::Preparing, &kProbe, kBytes, 0, 0, 400, 300));
static_assert(!canPrepare(State::Prepared, &kProbe, kBytes, 0, 0, 400, 300));
static_assert(!canPrepare(State::Finished, &kProbe, kBytes, 0, 0, 400, 300));
static_assert(canRefresh(State::Prepared) && !canRefresh(State::Finished));
static_assert(kMirrorY && !kInvert && !kPgm);
static_assert(!timedOutOrUnknown(kTimeoutUs - 1, false));
static_assert(timedOutOrUnknown(kTimeoutUs, false));
static_assert(timedOutOrUnknown(0, true));
static_assert(std::uint32_t(std::uint32_t(5) - std::uint32_t(0xFFFFFFFE)) == 7);
}  // namespace eink::h1
