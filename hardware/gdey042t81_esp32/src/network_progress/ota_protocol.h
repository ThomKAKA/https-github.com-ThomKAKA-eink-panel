#pragma once
#include "protocol.h"
#include <cstdio>
#include <cstring>
#include <cstdint>
#include <cstddef>
#include <string_view>

namespace eink::network_progress {
constexpr const char* kOtaManifestEndpoint = "/api/device/firmware/manifest";
constexpr const char* kOtaImageEndpoint = "/api/device/firmware/image";
constexpr size_t kOtaManifestBytes = 512;
constexpr size_t kOtaHeaderBytes = 2048;
constexpr size_t kOtaLineBytes = 512;
constexpr uint32_t kOtaMaxImageBytes = 1200000;

struct FirmwareOffer {
  bool armed;
  char version[65];
  char sha256[65];
  uint32_t size;
};

inline bool validVersion(const char* value) {
  if (!value) return false;
  const size_t n = std::strlen(value);
  if (n < 1 || n > 64) return false;
  for (size_t i = 0; i < n; ++i) {
    const char c = value[i];
    if (i == 0 && !((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9'))) return false;
    if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
          (c >= '0' && c <= '9') || c == '.' || c == '_' || c == '-')) return false;
  }
  return true;
}

inline bool validSha256(const char* value) {
  if (!value || std::strlen(value) != 64) return false;
  for (size_t i = 0; i < 64; ++i)
    if (!((value[i] >= '0' && value[i] <= '9') || (value[i] >= 'a' && value[i] <= 'f'))) return false;
  return true;
}

inline bool parseManifestBody(const char* body, FirmwareOffer& out) {
  out = FirmwareOffer{};
  if (!body) return false;
  if (!std::strcmp(body, "{\"armed\":false}")) return true;
  char version[65]{}, sha[65]{};
  unsigned size = 0;
  if (std::sscanf(body,
      "{\"armed\":true,\"version\":\"%64[^\"]\",\"size\":%u,\"sha256\":\"%64[0-9a-f]\"}",
      version, &size, sha) != 3) return false;
  if (!validVersion(version) || !validSha256(sha) || size == 0 ||
      size > kOtaMaxImageBytes) return false;
  char expected[kOtaManifestBytes];
  const int n = std::snprintf(expected, sizeof(expected),
    "{\"armed\":true,\"version\":\"%s\",\"size\":%u,\"sha256\":\"%s\"}",
    version, size, sha);
  if (n <= 0 || size_t(n) >= sizeof(expected) || std::strcmp(expected, body)) return false;
  out.armed = true;
  out.size = size;
  std::memcpy(out.version, version, sizeof(version));
  std::memcpy(out.sha256, sha, sizeof(sha));
  return true;
}

struct ImageHeaders {
  uint32_t length;
  char version[65];
  char sha256[65];
};

struct ManifestHeaders {
  uint32_t length;
};

class ManifestHeaderParser {
 public:
  void reset() { *this = ManifestHeaderParser{}; }
  bool feed(uint8_t c) {
    if (done_ || bad_ || ++total_ > kOtaHeaderBytes || ++lineUsed_ > kOtaLineBytes) return fail();
    if (cr_) {
      if (c != '\n') return fail();
      cr_ = false;
      const bool ok = line(View(line_, used_));
      used_ = lineUsed_ = 0;
      return ok ? true : fail();
    }
    if (c == '\r') { cr_ = true; return true; }
    if (c == '\n' || c == 0 || (c < 32 && c != '\t') || c >= 127) return fail();
    if (used_ >= sizeof(line_)) return fail();
    line_[used_++] = char(c);
    return true;
  }
  bool done() const { return done_; }
  const ManifestHeaders& headers() const { return headers_; }
 private:
  bool fail() { bad_ = true; return false; }
  bool line(View v) {
    if (!status_) {
      if (v.size() < 13 || !(v.substr(0, 9) == "HTTP/1.1 " || v.substr(0, 9) == "HTTP/1.0 ")) return false;
      if (v.substr(9, 3) != "200") return false;
      status_ = 200;
      return true;
    }
    if (v.empty()) {
      if (seen_ != 7u) return false;
      done_ = true;
      return true;
    }
    const auto colon = v.find(':');
    if (colon == View::npos || colon == 0) return false;
    for (char c : v.substr(0, colon)) if (!token(c)) return false;
    const View name = v.substr(0, colon);
    const View value = trim(v.substr(colon + 1));
    if (equalCI(name, "Transfer-Encoding") || equalCI(name, "Content-Encoding")) return false;
    auto unique = [&](unsigned bit) { if (seen_ & bit) return false; seen_ |= bit; return true; };
    if (equalCI(name, "Content-Type")) {
      return unique(1u << 0) && equalCI(value, "application/json");
    }
    if (equalCI(name, "Content-Length")) {
      if (!unique(1u << 1) || value.empty()) return false;
      uint32_t n = 0;
      for (char c : value) {
        if (c < '0' || c > '9' || n > kOtaManifestBytes / 10) return false;
        n = n * 10 + uint32_t(c - '0');
      }
      if (n == 0 || n > kOtaManifestBytes) return false;
      headers_.length = n;
      return true;
    }
    if (equalCI(name, "Connection")) {
      return unique(1u << 2) && equalCI(value, "close");
    }
    return true;
  }
  char line_[kOtaLineBytes]{};
  size_t used_ = 0, lineUsed_ = 0, total_ = 0;
  unsigned seen_ = 0;
  int status_ = 0;
  bool cr_ = false, done_ = false, bad_ = false;
  ManifestHeaders headers_{};
};

class ImageHeaderParser {
 public:
  void reset() { *this = ImageHeaderParser{}; }
  bool feed(uint8_t c) {
    if (done_ || bad_ || ++total_ > kOtaHeaderBytes || ++lineUsed_ > kOtaLineBytes) return fail();
    if (cr_) {
      if (c != '\n') return fail();
      cr_ = false;
      const bool ok = line(View(line_, used_));
      used_ = lineUsed_ = 0;
      return ok ? true : fail();
    }
    if (c == '\r') { cr_ = true; return true; }
    if (c == '\n' || c == 0 || (c < 32 && c != '\t') || c >= 127) return fail();
    if (used_ >= sizeof(line_)) return fail();
    line_[used_++] = char(c);
    return true;
  }
  bool done() const { return done_; }
  const ImageHeaders& headers() const { return headers_; }
 private:
  bool fail() { bad_ = true; return false; }
  static bool copyValue(View value, char (&out)[65]) {
    if (value.size() > 64) return false;
    std::memcpy(out, value.data(), value.size());
    out[value.size()] = 0;
    return true;
  }
  bool line(View v) {
    if (!status_) {
      if (v.size() < 13 || !(v.substr(0, 9) == "HTTP/1.1 " || v.substr(0, 9) == "HTTP/1.0 ")) return false;
      if (v.substr(9, 3) != "200") return false;
      status_ = 200;
      return true;
    }
    if (v.empty()) {
      constexpr unsigned required = 63u;
      if (seen_ != required) return false;
      done_ = true;
      return true;
    }
    const auto colon = v.find(':');
    if (colon == View::npos || colon == 0) return false;
    for (char c : v.substr(0, colon)) if (!token(c)) return false;
    const View name = v.substr(0, colon);
    const View value = trim(v.substr(colon + 1));
    if (equalCI(name, "Transfer-Encoding") || equalCI(name, "Content-Encoding")) return false;
    auto unique = [&](unsigned bit) { if (seen_ & bit) return false; seen_ |= bit; return true; };
    if (equalCI(name, "Content-Type")) {
      if (!unique(1u << 0) || !equalCI(value, "application/octet-stream")) return false;
      return true;
    }
    if (equalCI(name, "Content-Length")) {
      if (!unique(1u << 1) || value.empty()) return false;
      uint32_t n = 0;
      for (char c : value) {
        if (c < '0' || c > '9' || n > kOtaMaxImageBytes / 10) return false;
        n = n * 10 + uint32_t(c - '0');
      }
      if (n == 0 || n > kOtaMaxImageBytes) return false;
      headers_.length = n;
      return true;
    }
    if (equalCI(name, "X-Firmware-Version")) {
      if (!unique(1u << 2) || !copyValue(value, headers_.version) || !validVersion(headers_.version)) return false;
      return true;
    }
    if (equalCI(name, "X-Firmware-SHA256")) {
      if (!unique(1u << 3) || !copyValue(value, headers_.sha256) || !validSha256(headers_.sha256)) return false;
      return true;
    }
    if (equalCI(name, "Cache-Control")) {
      if (!unique(1u << 4) || !equalCI(value, "no-store")) return false;
      return true;
    }
    if (equalCI(name, "Connection")) {
      if (!unique(1u << 5) || !equalCI(value, "close")) return false;
      return true;
    }
    return true;
  }
  char line_[kOtaLineBytes]{};
  size_t used_ = 0, lineUsed_ = 0, total_ = 0;
  unsigned seen_ = 0;
  int status_ = 0;
  bool cr_ = false, done_ = false, bad_ = false;
  ImageHeaders headers_{};
};
}  // namespace eink::network_progress
