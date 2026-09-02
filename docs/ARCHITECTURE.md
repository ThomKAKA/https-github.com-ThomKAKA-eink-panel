# Architecture

## Phase 3 data flow

```text
Mock / Local JSON / HTTP JSON
            ↓
        DataAdapter
            ↓
      RefreshManager
   Last Known Good fallback
            ↓
  Progress / Stats / Flow panel
   validate → normalize → render
            ↓
    Pillow renderer
            ↓
  PNG/BMP HTTP response
            ↓
     Browser simulator
```

`BasePanel` defines the stable panel contract. The factory registers ProgressPanel,
StatsPanel, and FlowPanel. Display dimensions are loaded from `config/config.json`.
The renderer is intentionally independent from the simulator page so a future device can
consume the same generated image without changing panel layout logic.

Shared drawing helpers own frame, terminal mark, metadata, text fitting, timestamp, and
1-bit conversion behavior. The project does not contain databases, LLM clients, account-backed
data connectors, or hardware drivers in this phase. Browser timers only trigger refresh calls;
all fetching and fallback decisions stay in the server-side RefreshManager.
