#pragma once
#include <cstring>
#include <Preferences.h>
#include <WebServer.h>
#include <WiFi.h>
#include "wifi_provisioning.h"

namespace eink::network_progress {
constexpr char kProvisioningSsid[] = "eink-panel-setup";

// SSIDs are operator data: escape every HTML metacharacter before they reach
// the page. Passwords never enter this function or any response body.
inline void appendEscaped(String& out, const char* text) {
  for (const char* p = text; *p; ++p) {
    switch (*p) {
      case '&': out += "&amp;"; break;
      case '<': out += "&lt;"; break;
      case '>': out += "&gt;"; break;
      case '"': out += "&quot;"; break;
      case '\'': out += "&#39;"; break;
      default: out += *p;
    }
  }
}

inline String provisioningPage(const WifiNetworkStore& store, const char* resultLine) {
  String page = "<!doctype html><html><head><meta charset=utf-8><title>Wi-Fi setup</title></head>"
    "<body><h1>Wi-Fi setup</h1>";
  page += resultLine;
  page += "<h2>Saved networks</h2><table>";
  for (uint8_t i = 0; i < kMaxWifiNetworks; ++i) {
    if (!store.slots[i].used) continue;
    page += "<tr><td>"; page += char('0' + i); page += "</td><td>";
    appendEscaped(page, store.slots[i].value.ssid);
    page += "</td><td><form method=post action=/forget style=display:inline>"
      "<input type=hidden name=index value=";
    page += char('0' + i);
    page += "><button>Forget</button></form></td></tr>";
  }
  page += "</table><p>";
  page += store.count ? "Stored networks are tried last-success first." : "No saved network yet.";
  page += "</p><h2>Add or update</h2><form method=post action=/configure>"
    "<label>SSID <input name=ssid required maxlength=32></label><br>"
    "<label>Password <input name=password type=password maxlength=64></label><br>"
    "<button>Connect and save</button></form><p>Credentials are saved only after connection. "
    "Reload this page to see the result.</p></body></html>";
  return page;
}

class EspWifiPort {
 public:
  bool loadCredentials(WifiCredentials& out) {
    Preferences storage;
    if (!storage.begin("eink-wifi", true)) return false;
    const bool loaded = storage.getBytesLength("validated") == sizeof(out) &&
      storage.getBytes("validated", &out, sizeof(out)) == sizeof(out);
    storage.end();
    return loaded;
  }
  bool saveCredentials(const WifiCredentials& value) {
    Preferences storage;
    if (!storage.begin("eink-wifi")) return false;
    const bool saved = storage.putBytes("validated", &value, sizeof(value)) == sizeof(value);
    storage.end();
    return saved;
  }
  bool loadStore(WifiNetworkStore& out) {
    Preferences storage;
    if (!storage.begin("eink-wifi", true)) return false;
    const bool loaded = storage.getBytesLength("networks") == sizeof(out) &&
      storage.getBytes("networks", &out, sizeof(out)) == sizeof(out);
    storage.end();
    return loaded;
  }
  // Spec §7: a present but unusable blob (malformed, or written by a newer
  // version) is ignored for selection and never rewritten by the load path.
  bool hasStore() {
    Preferences storage;
    if (!storage.begin("eink-wifi", true)) return false;
    const bool present = storage.isKey("networks");
    storage.end();
    return present;
  }
  bool saveStore(const WifiNetworkStore& value) {
    Preferences storage;
    if (!storage.begin("eink-wifi")) return false;
    const bool saved = storage.putBytes("networks", &value, sizeof(value)) == sizeof(value);
    storage.end();
    return saved;
  }
  bool connect(const WifiCredentials& value) {
    connectStartStatus_ = WiFi.status();
    // begin() can return an inherited failure while starting a new attempt.
    return WiFi.begin(value.ssid, value.password) != WL_CONNECT_FAILED ||
      connectStartStatus_ == WL_CONNECT_FAILED;
  }
  void cancelConnect() { WiFi.disconnect(false, false); }
  bool stationConnected() { return WiFi.status() == WL_CONNECTED; }
  bool candidateConnected(const WifiCredentials& value) {
    return stationConnected() && uint32_t(WiFi.localIP()) != 0 && WiFi.SSID() == value.ssid;
  }
  bool connectionFailed() {
    const auto status = WiFi.status();
    return (status == WL_CONNECT_FAILED || status == WL_NO_SSID_AVAIL) &&
      status != connectStartStatus_;
  }
  bool startSoftAP() {
    if (WiFi.mode(WIFI_AP_STA) && WiFi.softAP(kProvisioningSsid)) return true;
    WiFi.enableAP(false);
    return false;
  }
  // Arduino-ESP32 2.0.17 softAPdisconnect(true) compares this bool to ESP_OK.
  // Check enableAP directly so successful AP removal preserves the STA link.
  bool stopSoftAP() { return WiFi.enableAP(false); }
 private:
  wl_status_t connectStartStatus_ = WL_IDLE_STATUS;
};

class EspWifiProvisioning {
 public:
  explicit EspWifiProvisioning(WifiCredentials configured) : wifi_(port_, configured) {}
  void load() { wifi_.load(); }
  void beginNormal() { wifi_.beginNormal(); }
  void normalConnected() { wifi_.normalConnected(); }
  // Shares EspWifiPort's connectStartStatus_ guard with connectionFailed(): a
  // sticky WL_CONNECT_FAILED / WL_NO_SSID_AVAIL inherited from the previous
  // attempt is not a fresh failure, so it cannot burn attempts 2 and 3.
  bool associationFailed() { return port_.connectionFailed(); }
  // Machine already cancelled the previous association before calling this;
  // WifiProvisioning::nextAttempt() repeats WiFi.disconnect(false, false)
  // intentionally. It is idempotent (no stored credentials, no radio mode
  // change) and also serves callers that advance without the Machine cancel.
  bool nextAttempt() { return wifi_.nextAttempt(); }
  bool beginProvisioning() {
    if (!wifi_.enterProvisioning()) return false;
    if (!routesInstalled_) {
      server_.on("/", HTTP_GET, [this] {
        server_.send(200, "text/html; charset=utf-8",
          provisioningPage(wifi_.store(), resultText()));
      });
      server_.on("/configure", HTTP_POST, [this] {
        const String ssid = server_.arg("ssid"), password = server_.arg("password");
        if (!server_.hasArg("ssid") || !server_.hasArg("password") ||
            ssid.length() != std::strlen(ssid.c_str()) ||
            password.length() != std::strlen(password.c_str())) {
          server_.send(400, "text/plain", "Invalid credentials or connection already in progress.");
          return;
        }
        if (!wifi_.submit(wifiCredentials(ssid.c_str(), password.c_str()), millis())) {
          if (wifi_.result() == WifiResult::StoreFull) {
            server_.send(409, "text/plain", "Store full; forget one network first.");
          } else {
            server_.send(400, "text/plain", "Invalid credentials or connection already in progress.");
          }
          return;
        }
        server_.send(202, "text/plain",
          "Connecting. Save follows successful LAN connection. Reload / for result; setup AP closes on success.");
        // Close the AP listener before the candidate window (existing lwIP safety rule).
        // Disabling the AP while the WebServer still owns AP-side TCP PCB(s) was
        // observed to abort/free corrupted lwIP TCP state on this SDK.
        server_.stop();
        serverStopped_ = true;
      });
      server_.on("/forget", HTTP_POST, [this] {
        const String raw = server_.arg("index");
        if (!server_.hasArg("index") || raw.length() != 1 || raw[0] < '0' || raw[0] > '2') {
          server_.send(400, "text/plain", "Invalid index.");
          return;
        }
        const uint8_t index = uint8_t(raw[0] - '0');
        // An unused index is a client error, not a forgotten-network failure;
        // forget() would answer 409 with the "connection pending" wording.
        if (!wifi_.store().slots[index].used) {
          server_.send(400, "text/plain", "No network at that index.");
          return;
        }
        if (!wifi_.forget(index)) {
          server_.send(wifi_.result() == WifiResult::StoreWriteFailed ? 500 : 409,
            "text/plain", wifi_.result() == WifiResult::StoreWriteFailed
              ? "Store write failed; nothing changed."
              : "Cannot forget while a connection attempt is pending.");
          return;
        }
        server_.send(202, "text/plain", "Network forgotten. Reload / to see the list.");
      });
      routesInstalled_ = true;
    }
    server_.begin();
    return true;
  }
  bool pollProvisioning() {
    server_.handleClient();
    if (!wifi_.poll(millis())) {
      // A failed candidate returns to Provisioning; reopen the listener so the
      // operator can retry. A pending candidate keeps it closed.
      if (serverStopped_ && wifi_.mode() == WifiMode::Provisioning) {
        server_.begin();
        serverStopped_ = false;
      }
      return false;
    }
    server_.stop();
    serverStopped_ = false;
    return true;
  }
 private:
  const char* resultText() const {
    switch (wifi_.result()) {
      case WifiResult::None: return "<p>Ready.</p>";
      case WifiResult::Connecting: return "<p>Connecting; credentials not saved yet.</p>";
      case WifiResult::Saved: return "<p>Connected and saved.</p>";
      case WifiResult::Timeout: return "<p>Connection timed out. Previous credentials retained.</p>";
      case WifiResult::ConnectFailed: return "<p>Connection failed. Previous credentials retained.</p>";
      case WifiResult::SaveFailed: return "<p>Credential save failed.</p>";
      case WifiResult::SoftApFailed: return "<p>Setup AP lifecycle failed.</p>";
      case WifiResult::StoreFull: return "<p>Store full; forget one network first.</p>";
      case WifiResult::StoreWriteFailed: return "<p>Store write failed; the previous list is unchanged.</p>";
      case WifiResult::Forgotten: return "<p>Network forgotten.</p>";
      case WifiResult::ForgetRejected: return "<p>Cannot forget now; finish or retry the connection first.</p>";
    }
    return "";
  }
  EspWifiPort port_;
  WifiProvisioning<EspWifiPort> wifi_;
  WebServer server_{IPAddress(192, 168, 4, 1), 80};
  bool routesInstalled_ = false;
  bool serverStopped_ = false;
};
}  // namespace eink::network_progress
