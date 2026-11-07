# Phase 2 Design System

All three panels use the same compact, monochrome, industrial terminal profile.

| Token | Value |
| --- | ---: |
| `FONT_XS` | 8 |
| `FONT_SM` | 10 |
| `FONT_MD` | 13 |
| `FONT_LG` | 18 |
| `FONT_XL` | 24 |
| `FONT_NUMBER` | 64 |
| `SPACE_1` | 3 |
| `SPACE_2` | 6 |
| `SPACE_3` | 9 |
| `SPACE_4` | 12 |
| `PANEL_PADDING` | 10 |
| `BORDER_THIN` | 1 |
| `TAG_HEIGHT` | 20 |

Additional geometry: 8px column gap, 38% left column, 14px progress bar. Shapes use
square corners, no shadows, no gradients, and no motion. Normal Preview retains font
antialiasing; E-Ink Preview uses a threshold of 192 to preserve small metadata while
producing a true 1-bit image.

Phase 2 adds reusable geometry without changing the Phase 1 ProgressPanel layout:

| Token | Value |
| --- | ---: |
| `DIVIDER_WIDTH` | 1 |
| `STATS_BAR_HEIGHT` | 10 |
| `STATS_LEFT_COLUMN_RATIO` | 0.40 |
| `FLOW_LEFT_COLUMN_RATIO` | 0.39 |
| `FLOW_NODE_DONE` | 16 |
| `FLOW_NODE_ACTIVE` | 24 |
| `FLOW_NODE_PENDING` | 20 |

Missing timestamps use local system time formatted as `YYYY-MM-DD HH:mm`. Explicit
non-empty timestamps are preserved.

Latin text and numbers prefer Consolas. Chinese text prefers Microsoft YaHei on Windows,
with Noto/DejaVu fallbacks on other systems.
