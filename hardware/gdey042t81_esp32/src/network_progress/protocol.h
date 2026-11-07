#pragma once

// Restricted STEP017C profile, not a general-purpose HTTP parser.
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <string_view>

namespace eink::network_progress {
constexpr size_t kFrameBytes = 15000;
constexpr const char* kFormat = "epd-t-400x300-mono1-msb-v1";
constexpr const char* kEndpoint = "/api/panels/progress/frame";
using View = std::string_view;
inline char lower(char c) { return c >= 'A' && c <= 'Z' ? char(c + 32) : c; }
inline bool equalCI(View a, View b) {
  if (a.size() != b.size()) return false;
  for (size_t i = 0; i < a.size(); ++i) if (lower(a[i]) != lower(b[i])) return false;
  return true;
}
inline View trim(View v) {
  while (!v.empty() && (v.front() == ' ' || v.front() == '\t')) v.remove_prefix(1);
  while (!v.empty() && (v.back() == ' ' || v.back() == '\t')) v.remove_suffix(1);
  return v;
}
inline bool token(char c) {
  return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
         (c >= '0' && c <= '9') || (c && std::strchr("!#$%&'*+-.^_`|~", c));
}
inline bool validTag(View v) {
  if (v.size() != 66 || v.front() != '"' || v.back() != '"') return false;
  for (size_t i = 1; i < 65; ++i)
    if (!((v[i] >= '0' && v[i] <= '9') || (v[i] >= 'a' && v[i] <= 'f'))) return false;
  return true;
}
inline bool cachePolicy(View v) {
  const auto comma = v.find(',');
  if (comma == View::npos || v.find(',', comma + 1) != View::npos) return false;
  const auto a = trim(v.substr(0, comma)), b = trim(v.substr(comma + 1));
  return (equalCI(a, "no-cache") && equalCI(b, "no-transform")) ||
         (equalCI(b, "no-cache") && equalCI(a, "no-transform"));
}
inline bool expired(uint32_t now, uint32_t start, uint32_t budget) {
  return uint32_t(now - start) >= budget;
}

class Headers {
 public:
  void reset(const char* accepted) {
    *this = Headers{};
    if (accepted) std::memcpy(sent_, accepted, 67);
  }
  bool feed(uint8_t c) {
    if (done_ || bad_ || ++total_ > 4096 || ++wireLine_ > 512) return fail();
    if (cr_) {
      if (c != '\n') return fail();
      cr_ = false;
      const bool ok = line(View(line_, used_));
      used_ = wireLine_ = 0;
      if (!ok) return fail();
      return true;
    }
    if (c == '\r') { cr_ = true; return true; }
    if (c == '\n' || c == 0 || (c < 32 && c != '\t') || c >= 127) return fail();
    if (used_ >= sizeof(line_)) return fail();
    line_[used_++] = char(c);
    return true;
  }
  bool done() const { return done_; }
  int status() const { return status_; }
  const char* etag() const { return tag_; }
 private:
  bool fail() { bad_ = true; return false; }
  bool line(View v) {
    if (!status_) {
      if (v.size() < 13 || !(v.substr(0, 9) == "HTTP/1.1 " || v.substr(0, 9) == "HTTP/1.0 ") || v[12] != ' ') return false;
      if (v.substr(9, 3) == "200") status_ = 200;
      else if (v.substr(9, 3) == "304") status_ = 304;
      else return false;
      return v.find('\t') == View::npos;
    }
    if (v.empty()) {
      constexpr unsigned common = (1u << 2) | (1u << 3) | (1u << 4);
      if ((seen_ & common) != common) return false;
      if (status_ == 200 && (seen_ & 3u) != 3u) return false;
      if (status_ == 304 && ((seen_ & 2u) || !sent_[0] || std::strcmp(sent_, tag_))) return false;
      done_ = true; return true;
    }
    const auto colon = v.find(':');
    if (colon == View::npos || colon == 0) return false;
    for (char c : v.substr(0, colon)) if (!token(c)) return false;
    const View name = v.substr(0, colon), value = trim(v.substr(colon + 1));
    if (equalCI(name, "Content-Encoding") || equalCI(name, "Transfer-Encoding")) return false;
    const char* keys[] = {"Content-Type", "Content-Length", "ETag", "X-Frame-Format", "Cache-Control", "Connection"};
    for (unsigned i = 0; i < 6; ++i) {
      if (!equalCI(name, keys[i])) continue;
      if (seen_ & (1u << i)) return false;
      seen_ |= 1u << i;
      if (i == 0) return status_ == 304 || equalCI(value, "application/octet-stream");
      if (i == 1) {
        if (status_ != 200 || value.empty()) return false;
        unsigned n = 0;
        for (char c : value) {
          if (c < '0' || c > '9' || n > kFrameBytes / 10) return false;
          n = n * 10 + unsigned(c - '0');
          if (n > kFrameBytes) return false;
        }
        return n == kFrameBytes;
      }
      if (i == 2) {
        if (!validTag(value)) return false;
        std::memcpy(tag_, value.data(), 66); tag_[66] = 0; return true;
      }
      if (i == 3) return value == kFormat;
      if (i == 4) return cachePolicy(value);
      return equalCI(value, "close");
    }
    return true;
  }
  char line_[512]{};
  char tag_[67]{}, sent_[67]{};
  size_t used_ = 0, wireLine_ = 0, total_ = 0;
  unsigned seen_ = 0;
  int status_ = 0;
  bool cr_ = false, done_ = false, bad_ = false;
};
}  // namespace eink::network_progress
