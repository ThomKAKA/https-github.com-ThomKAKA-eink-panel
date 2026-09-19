#pragma once
#ifndef EINK_NETWORK_PROGRESS
#error "Network configuration is exclusive to the network Progress entry"
#endif
#include "protocol.h"
#include "../h1/config.h"
#include "network_config.local.h"
static_assert(NETWORK_PROGRESS_PRIVATE_PROFILE == 1, "Network profile must be explicitly confirmed");

namespace eink::network_progress {
// Use string literals, not pointers, to validate embedded NULs and byte lengths.
constexpr char kSsid[] = NETWORK_SSID;
constexpr char kPassword[] = NETWORK_PASSWORD;
constexpr unsigned kHost[] = { NETWORK_HOST_IPV4 };
constexpr unsigned kPort = NETWORK_HOST_PORT;
#ifndef NETWORK_POLL_SECONDS
#define NETWORK_POLL_SECONDS 60
#endif
constexpr unsigned kPollSeconds = NETWORK_POLL_SECONDS;
static_assert(sizeof(kHost) / sizeof(kHost[0]) == 4, "Numeric IPv4 requires four octets");
inline bool validConfig() {
  if (sizeof(kSsid) < 2 || sizeof(kSsid) > 33) return false;
  for (size_t i = 0; i + 1 < sizeof(kSsid); ++i) if (!kSsid[i]) return false;
  for (size_t i = 0; i + 1 < sizeof(kPassword); ++i) if (!kPassword[i]) return false;
  // Personal PSK: empty for explicitly open LAN, 8..63 bytes or 64 hex digits.
  const size_t length = sizeof(kPassword) - 1;
  if (length && (length < 8 || length > 64)) return false;
  if (length == 64) for (char c : View(kPassword, length))
    if (!((c >= '0' && c <= '9') || (lower(c) >= 'a' && lower(c) <= 'f'))) return false;
  for (unsigned octet : kHost) if (octet > 255) return false;
  // Reject unspecified, loopback, multicast and reserved address classes.
  // Whether an address is on the intended LAN (or a subnet broadcast) also
  // requires deployment/netmask review; numeric validation is not authorization.
  const bool unicast = kHost[0] > 0 && kHost[0] < 224 && kHost[0] != 127;
  return unicast && kPort >= 1 && kPort <= 65535 && kPollSeconds >= 60 && kPollSeconds <= 86400;
}
}  // namespace eink::network_progress
