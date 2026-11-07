#pragma once
#include <Arduino.h>
#include <esp_ota_ops.h>
#include <mbedtls/sha256.h>
#include "ota.h"

namespace eink::network_progress {
class EspOtaSink final : public OtaSink {
 public:
  bool begin(size_t size) override {
    if (active_) return false;
    partition_ = esp_ota_get_next_update_partition(nullptr);
    if (!partition_ || size == 0 || size > partition_->size) return false;
    if (esp_ota_begin(partition_, size, &handle_) != ESP_OK) return false;
    mbedtls_sha256_init(&sha_);
    if (mbedtls_sha256_starts_ret(&sha_, 0) != 0) {
      esp_ota_abort(handle_);
      mbedtls_sha256_free(&sha_);
      return false;
    }
    active_ = true;
    return true;
  }
  bool write(const uint8_t* data, size_t size) override {
    return active_ && esp_ota_write(handle_, data, size) == ESP_OK &&
      mbedtls_sha256_update_ret(&sha_, data, size) == 0;
  }
  bool finish(const char* expected) override {
    if (!active_ || !expected) return false;
    active_ = false;
    const bool imageOk = esp_ota_end(handle_) == ESP_OK;
    unsigned char digest[32]{};
    const bool hashOk = mbedtls_sha256_finish_ret(&sha_, digest) == 0;
    mbedtls_sha256_free(&sha_);
    if (!imageOk || !hashOk) return false;
    constexpr char hex[] = "0123456789abcdef";
    char actual[65]{};
    for (unsigned i = 0; i < 32; ++i) {
      actual[i * 2] = hex[digest[i] >> 4];
      actual[i * 2 + 1] = hex[digest[i] & 15];
    }
    return std::strcmp(actual, expected) == 0;
  }
  bool activate() override {
    return partition_ && esp_ota_set_boot_partition(partition_) == ESP_OK;
  }
  void reboot() override { ESP.restart(); }
  void abort() override {
    if (active_) { esp_ota_abort(handle_); active_ = false; }
    mbedtls_sha256_free(&sha_);
  }
 private:
  const esp_partition_t* partition_ = nullptr;
  esp_ota_handle_t handle_ = 0;
  mbedtls_sha256_context sha_{};
  bool active_ = false;
};
}  // namespace eink::network_progress
