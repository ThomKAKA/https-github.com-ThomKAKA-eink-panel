#pragma once
#include <cstring>
#include <Preferences.h>
#include <WebServer.h>
#include <WiFi.h>
#include "wifi_provisioning.h"

namespace eink::network_progress {
constexpr char kProvisioningSsid[] = "eink-panel-setup";
constexpr char kProvisioningHtml[] =
  "<!doctype html><html><head><meta charset=utf-8><title>Wi-Fi setup</title></head>"
  "<body><h1>Wi-Fi setup</h1><form method=post action=/configure>"
  "<label>SSID <input name=ssid required maxlength=32></label><br>"
  "<label>Password <input name=password type=password maxlength=64></label><br>"
  "<button>Connect and save</button></form><p>Credentials are saved only after connection. "
  "Reload this page to see the result.</p>";

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
  bool beginProvisioning() {
    if (!wifi_.enterProvisioning()) return false;
    if (!routesInstalled_) {
      server_.on("/", HTTP_GET, [this] {
        server_.send(200, "text/html; charset=utf-8", String(kProvisioningHtml) + resultText() + "</body></html>");
      });
      server_.on("/configure", HTTP_POST, [this] {
        const String ssid = server_.arg("ssid"), password = server_.arg("password");
        if (!server_.hasArg("ssid") || !server_.hasArg("password") ||
            ssid.length() != std::strlen(ssid.c_str()) || password.length() != std::strlen(password.c_str()) ||
            !wifi_.submit(wifiCredentials(ssid.c_str(), password.c_str()), millis())) {
          server_.send(400, "text/plain", "Invalid credentials or connection already in progress.");
          return;
        }
        server_.send(202, "text/plain", "Connecting. Save follows successful LAN connection. Reload / for result; setup AP closes on success.");
      });
      routesInstalled_ = true;
    }
    server_.begin();
    return true;
  }
  bool pollProvisioning() {
    server_.handleClient();
    if (!wifi_.poll(millis())) return false;
    server_.stop();
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
    }
    return "";
  }
  EspWifiPort port_;
  WifiProvisioning<EspWifiPort> wifi_;
  WebServer server_{IPAddress(192, 168, 4, 1), 80};
  bool routesInstalled_ = false;
};
}  // namespace eink::network_progress
