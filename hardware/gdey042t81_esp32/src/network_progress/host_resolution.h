#pragma once
#include <cstddef>

namespace eink::network_progress {
constexpr const char* kDiscoveryService = "_eink-panel";
constexpr const char* kDiscoveryProtocol = "_tcp";
constexpr const char* kDiscoveryInstance = "eink-panel";
constexpr unsigned kDiscoveryTimeoutMs = 1000;

enum class HostSource { DISCOVERED, CONFIGURED_FALLBACK };
struct ResolvedHost {
  unsigned address[4];
  unsigned port;
  HostSource source;
};

inline bool validEndpoint(const ResolvedHost& host) {
  return host.address[0] > 0 && host.address[0] < 224 && host.address[0] != 127 &&
    host.address[1] <= 255 && host.address[2] <= 255 && host.address[3] <= 255 &&
    host.port > 0 && host.port <= 65535;
}

// Discovery absence, failure or an invalid result selects the existing config.
inline ResolvedHost resolveHost(const ResolvedHost* discovered, const ResolvedHost& configured) {
  ResolvedHost result = discovered && validEndpoint(*discovered) ? *discovered : configured;
  result.source = discovered && validEndpoint(*discovered)
    ? HostSource::DISCOVERED : HostSource::CONFIGURED_FALLBACK;
  return result;
}
}  // namespace eink::network_progress
