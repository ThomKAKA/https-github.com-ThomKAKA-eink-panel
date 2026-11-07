// Production button logic is evaluated by C++17 static_assert, without GPIO.
#include "../../hardware/gdey042t81_esp32/src/network_progress/provisioning_button.h"
using namespace eink::network_progress;

struct ButtonMachine {
  State current = State::WifiConnect;
  unsigned requests = 0;
  bool accept = true;
  constexpr State state() const { return current; }
  constexpr bool requestProvisioning() {
    ++requests;
    if (accept) current = State::Provisioning;
    return accept;
  }
};
constexpr void arm(ProvisioningButton& button, ButtonMachine& machine) {
  button.poll(false, 0, machine); button.poll(false, 30, machine);
  machine.current = State::PollWait;
}
constexpr bool hold(ProvisioningButton& button, ButtonMachine& machine, uint32_t start = 100) {
  button.poll(true, start, machine);
  button.poll(true, start + 30, machine);
  return button.poll(true, start + 2030, machine);
}
constexpr bool noPress() {
  ProvisioningButton button; ButtonMachine machine; arm(button, machine);
  button.poll(false, 4000, machine);
  return machine.requests == 0 && machine.current == State::PollWait;
}
constexpr bool shortPress() {
  ProvisioningButton button; ButtonMachine machine; arm(button, machine);
  button.poll(true, 100, machine); button.poll(true, 130, machine);
  button.poll(true, 2129, machine); button.poll(false, 2130, machine);
  button.poll(false, 2160, machine); button.poll(false, 5000, machine);
  return machine.requests == 0;
}
constexpr bool bounce() {
  ProvisioningButton button; ButtonMachine machine; arm(button, machine);
  button.poll(true, 100, machine); button.poll(false, 110, machine);
  button.poll(true, 120, machine); button.poll(false, 130, machine);
  button.poll(false, 3000, machine);
  return machine.requests == 0;
}
constexpr bool accepted(State safe) {
  ProvisioningButton button; ButtonMachine machine; arm(button, machine);
  machine.current = safe;
  return hold(button, machine) && machine.requests == 1 && machine.current == State::Provisioning;
}
constexpr bool heldDoesNotRepeat() {
  ProvisioningButton button; ButtonMachine machine; arm(button, machine); hold(button, machine);
  // Even another idle boundary cannot turn this same held button into a request.
  machine.current = State::PollWait;
  button.poll(true, 9000, machine); button.poll(true, 12000, machine);
  return machine.requests == 1;
}
constexpr bool secondPress() {
  ProvisioningButton button; ButtonMachine machine; arm(button, machine); hold(button, machine);
  button.poll(false, 2200, machine); button.poll(false, 2230, machine);
  machine.current = State::FailureWait;
  return hold(button, machine, 2300) && machine.requests == 2;
}
constexpr bool pendingAt(State busy) {
  ProvisioningButton button; ButtonMachine machine; arm(button, machine);
  machine.current = busy; hold(button, machine);
  if (machine.requests || machine.current != busy) return false;
  button.poll(false, 2200, machine); button.poll(false, 2230, machine);
  machine.current = State::PollWait;
  const bool accepted = button.poll(false, 2240, machine);
  return accepted && machine.requests == 1 && machine.current == State::Provisioning;
}
constexpr bool bootAndInitFailure() {
  ProvisioningButton button; ButtonMachine machine; machine.current = State::Boot;
  button.poll(false, 0, machine); hold(button, machine);
  machine.current = State::FailureWait; hold(button, machine, 3000);
  return machine.requests == 0;
}
constexpr bool bootHeldMustRelease() {
  ProvisioningButton button; ButtonMachine machine;
  button.poll(true, 0, machine); button.poll(true, 30, machine);
  machine.current = State::PollWait;
  button.poll(true, 3000, machine);
  if (machine.requests) return false;
  button.poll(false, 3100, machine); button.poll(false, 3130, machine);
  return hold(button, machine, 3200) && machine.requests == 1;
}
constexpr bool failedRequestOnce() {
  ProvisioningButton button; ButtonMachine machine; arm(button, machine); machine.accept = false;
  hold(button, machine); button.poll(true, 9000, machine);
  return machine.requests == 1 && machine.current == State::PollWait;
}
constexpr bool faultStop() {
  ProvisioningButton button; ButtonMachine machine; arm(button, machine);
  machine.current = State::FaultStop; hold(button, machine);
  return machine.requests == 0 && machine.current == State::FaultStop;
}
constexpr bool releaseBounceDoesNotRearm() {
  ProvisioningButton button; ButtonMachine machine; arm(button, machine); hold(button, machine);
  machine.current = State::PollWait;
  button.poll(false, 2200, machine); button.poll(true, 2210, machine);
  button.poll(true, 2240, machine); button.poll(true, 9000, machine);
  return machine.requests == 1;
}

static_assert(noPress(), "normal no-button operation does not request provisioning");
static_assert(shortPress(), "less than deliberate hold never triggers");
static_assert(bounce(), "short raw bounces never trigger");
static_assert(accepted(State::PollWait), "PollWait accepts one valid gesture");
static_assert(accepted(State::FailureWait), "initialized FailureWait accepts one valid gesture");
static_assert(heldDoesNotRepeat(), "continuous hold is latched after one request");
static_assert(secondPress(), "stable release permits the next deliberate hold");
static_assert(pendingAt(State::WifiConnect), "Wi-Fi connection is not interrupted");
static_assert(pendingAt(State::HostResolve), "discovery is not interrupted");
static_assert(pendingAt(State::HttpConnect), "HTTP connect is not interrupted");
static_assert(pendingAt(State::FrameReceive), "frame receive is not interrupted");
static_assert(pendingAt(State::DisplayPending), "display preparation is not interrupted");
static_assert(pendingAt(State::DisplayUpdate), "display update is not interrupted");
static_assert(pendingAt(State::DeviceReport), "device report is not interrupted");
static_assert(pendingAt(State::Provisioning), "candidate session is not interrupted");
static_assert(bootAndInitFailure(), "boot and uninitialized failure cannot trigger");
static_assert(bootHeldMustRelease(), "held-across-boot input must first be released");
static_assert(failedRequestOnce(), "rejected request is not retried during the same hold");
static_assert(faultStop(), "FaultStop remains unchanged");
static_assert(releaseBounceDoesNotRearm(), "release must be stable to rearm");
