#include "../../hardware/gdey042t81_esp32/src/network_progress/firmware_validity.h"
#include <cassert>
using eink::network_progress::FirmwareValidity;

int main() {
  FirmwareValidity v;
  assert(!v.observe(0, false, true));
  assert(!v.observe(0, true, false));
  assert(!v.observe(0, true, true));
  assert(!v.observe(119999, true, true));
  assert(v.observe(120000, true, true));
  assert(!v.observe(130000, true, true));
  assert(!v.observe(130001, false, true));
  assert(!v.observe(130002, true, true));
  assert(!v.observe(130003, true, false));
  assert(!v.observe(130004, true, true));
  assert(!v.observe(250003, true, true));
  assert(v.observe(250004, true, true));
}
