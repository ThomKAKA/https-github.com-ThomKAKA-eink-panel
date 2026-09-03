#pragma once

#include "frame.h"
#include "refresh_policy.h"

namespace eink {

// Submitted means driver calls returned, NOT that the physical pixels were read back.
enum class DisplayResult {
  Submitted,
  ConfigUnconfirmed,
  NotInitialized,
  InvalidFrame,
  InvalidRefreshMode,
  BusyActive
};

class DisplayDriver {
 public:
  DisplayResult begin();
  DisplayResult showTestPattern();
  DisplayResult displayFrame(FrameView frame, RefreshMode mode);

 private:
  bool initialized_ = false;
  bool has_frame_ = false;
  DisplayResult finishRefresh();
};

const char* displayResultName(DisplayResult result);

}  // namespace eink
