#pragma once
#include "machine.h"

namespace eink::network_progress {
// ESP32-M1 schematic: physical KEY/S1 -> KEY1 -> U5 IO25 (module pin 10).
constexpr unsigned kProvisioningButtonGpio = 25;
constexpr uint32_t kProvisioningButtonDebounceMs = 30;
constexpr uint32_t kProvisioningButtonHoldMs = 2000;

class ProvisioningButton {
 public:
  template<class MachineType>
  constexpr bool poll(bool pressed, uint32_t now, MachineType& machine) {
    const State state = machine.state();
    // WifiConnect is reached only after the existing WifiInit succeeds.
    if (state == State::WifiConnect) ready_ = true;
    if (!ready_ || state == State::FaultStop) return false;
    if (pressed != raw_) { raw_ = pressed; changedAt_ = now; }
    if (uint32_t(now - changedAt_) >= kProvisioningButtonDebounceMs) {
      if (pressed != stable_) {
        stable_ = pressed;
        if (pressed) heldAt_ = now;
        else latched_ = false;
      }
      // A released input must be observed after initialization; a button held
      // across boot is not a provisioning gesture.
      if (!pressed) armed_ = true;
      else if (armed_ && !latched_ && uint32_t(now - heldAt_) >= kProvisioningButtonHoldMs) {
        latched_ = true; pending_ = true;
      }
    }
    // One pending bit, no queue or automatic retry. Never interrupt a transaction.
    if (pending_ && (state == State::PollWait || state == State::FailureWait)) {
      pending_ = false;
      return machine.requestProvisioning();
    }
    return false;
  }
 private:
  uint32_t changedAt_ = 0, heldAt_ = 0;
  bool raw_ = false, stable_ = false, armed_ = false;
  bool latched_ = false, pending_ = false, ready_ = false;
};
}  // namespace eink::network_progress
