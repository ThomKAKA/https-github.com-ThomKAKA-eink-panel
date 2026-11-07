#pragma once
#ifndef EINK_PROGRESS_EMBEDDED_TEST
#error "Progress requires the dedicated embedded-frame environment"
#endif
// Reuse the unchanged H1 wiring/profile assertions, with a separate private path.
#include "../h1/config.h"
static_assert(PROGRESS_PRIVATE_PROFILE == 1, "Progress private profile required");
