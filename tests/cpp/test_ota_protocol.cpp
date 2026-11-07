#include "../../hardware/gdey042t81_esp32/src/network_progress/ota_protocol.h"
#include <cassert>
#include <cstring>
#include <string>
using namespace eink::network_progress;

const std::string SHA(64, 'a');
const std::string VERSION = "round2-r6-2";

std::string manifest() {
  return "{\"armed\":true,\"version\":\"" + VERSION + "\",\"size\":33,\"sha256\":\"" + SHA + "\"}";
}

std::string imageHead(int status = 200, const std::string& extra = "") {
  return "HTTP/1.1 " + std::to_string(status) + " OK\r\n"
    "Content-Type: application/octet-stream\r\nContent-Length: 33\r\n"
    "X-Firmware-Version: " + VERSION + "\r\n"
    "X-Firmware-SHA256: " + SHA + "\r\n"
    "Cache-Control: no-store\r\nConnection: close\r\n" + extra + "\r\n";
}

bool parseImage(const std::string& text, ImageHeaders& out) {
  ImageHeaderParser parser;
  for (unsigned char c : text) if (!parser.feed(c)) return false;
  if (!parser.done()) return false;
  out = parser.headers();
  return true;
}

int main() {
  FirmwareOffer offer{};
  assert(parseManifestBody("{\"armed\":false}", offer));
  assert(!offer.armed);
  assert(parseManifestBody(manifest().c_str(), offer));
  assert(offer.armed && offer.size == 33);
  assert(std::strcmp(offer.version, VERSION.c_str()) == 0);
  assert(std::strcmp(offer.sha256, SHA.c_str()) == 0);

  const char* bad[] = {
    "",
    "{}",
    "{\"armed\":true}",
    "{\"armed\":false,\"x\":1}",
    "{\"armed\":true,\"version\":\"round2-r6-2\",\"size\":0,\"sha256\":\"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\"}",
    "{\"armed\":true,\"version\":\"bad version\",\"size\":33,\"sha256\":\"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\"}",
    "{\"armed\":true,\"version\":\"round2-r6-2\",\"size\":33,\"sha256\":\"Aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\"}",
    "{\"armed\":false} ",
  };
  for (const char* value : bad) assert(!parseManifestBody(value, offer));

  ManifestHeaderParser manifestHeaders;
  const std::string manifestHead =
    "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
    "Content-Length: 102\r\nConnection: close\r\n\r\n";
  for (unsigned char c : manifestHead) assert(manifestHeaders.feed(c));
  assert(manifestHeaders.done() && manifestHeaders.headers().length == 102);

  ManifestHeaderParser wrongManifestHeaders;
  const std::string wrongManifest =
    "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n"
    "Content-Length: 102\r\nConnection: close\r\n\r\n";
  bool wrongOk = true;
  for (unsigned char c : wrongManifest) {
    if (!wrongManifestHeaders.feed(c)) { wrongOk = false; break; }
  }
  assert(!wrongOk && !wrongManifestHeaders.done());

  ImageHeaders headers{};
  assert(parseImage(imageHead(), headers));
  assert(headers.length == 33);
  assert(std::strcmp(headers.version, VERSION.c_str()) == 0);
  assert(std::strcmp(headers.sha256, SHA.c_str()) == 0);

  assert(!parseImage(imageHead(304), headers));
  assert(!parseImage("HTTP/1.1 200 OK\r\nContent-Length: 33\r\n\r\n", headers));
  assert(!parseImage(imageHead(200, "Transfer-Encoding: chunked\r\n"), headers));
  assert(!parseImage(imageHead(200, "Content-Encoding: identity\r\n"), headers));
  assert(!parseImage(imageHead(200, "X-Firmware-Version: round2-r6-3\r\n"), headers));
  assert(!parseImage(imageHead(200, "Content-Length: 0\r\n"), headers));
  assert(!parseImage(imageHead(200, "Cache-Control: no-cache\r\n"), headers));
  assert(!parseImage(imageHead(200, "Connection: keep-alive\r\n"), headers));
  assert(!parseImage(imageHead(200, "X-Firmware-SHA256: " + SHA + "\r\n"), headers));
  return 0;
}
