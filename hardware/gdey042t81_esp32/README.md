# GDEY042T81 + ESP32：Phase 4 P1.5 硬件预备层

这是独立的 bring-up scaffold，不是已通过硬件验收的稳定固件。目标是先拆开并验证
SPI 显示与本地位图，不把 Wi-Fi、HTTP、事件模型和显示故障混在一起。

截至 STEP-013 编译验收 / 2026-09-09：

| 状态 | 结果 |
| --- | --- |
| P1 软件 | STABLE：独立的软件基线，不依赖本硬件目录 |
| P1.5 骨架 | SCAFFOLD COMPLETE：不是硬件验收通过 |
| IMPLEMENTED | YES：H0/H1 源码路径、刷新策略、禁用网络接口和文档 |
| COMPILE VERIFIED | YES：generic esp32dev 与 ESP32-M1/lolin32 均退出码 0；默认 H0、无私有配置；不证明实物运行 |
| REAL BOARD IDENTIFIED | YES：ESP32-M1/WROOM-32D照片与图纸一致；屏幕SKU仍PROVISIONAL |
| HARDWARE VERIFIED | NO：没有执行烧录、接线或物理显示验收 |
| Python 回归 | 125 passed；硬件目录不是 Python 运行或测试依赖 |

## 责任边界

现有软件实际路径是 `POST /api/events → 语义验证 → 内存快照`，调用方可以取出
`snapshot.data` 再提交给现有 Panel 渲染接口。当前还没有自动连接快照与物理屏。

未来的完整链路（未实现的部分标在括号中）：

```text
Event → State → Python Panel/Renderer → [Frame endpoint → ESP32 polling] → Display
                                             H2/H3，未实现
```

ESP32 只接收像素，不理解 Progress/Stats/Flow、Panel JSON、`panel.update`、字体或布局。
中文也由 Python 先渲染成像素。目录可独立移出而不影响 Python；本次没有实际删除它来验证。
服务器、现有 PNG/BMP 和事件 API、前端 UI 均不依赖此目录。

## 分阶段启用

| 阶段 | 问题 | 本次交付 | 放行条件 |
| --- | --- | --- | --- |
| H0 | SPI/转接板/屏幕能否显示？ | 默认 ASCII、实心矩形、空心矩形、横线测试图 | 用户在实物上确认正确 |
| H1 | 全幅 1-bit 帧是否 1:1？ | 编译期本地测试帧和有限刷新演示，默认不启用 | H0 通过后，核对边框/方向/极性/残影 |
| H2 | 能否安全获取一帧？ | 仅 FrameFetcher 禁用桩与协议草案 | 另行批准与实现，不能因有头文件就视为已完成 |
| H3 | 事件能否到达物理屏？ | 仅边界说明 | H2 通过后另行批准 |

默认数据源始终为 `LOCAL_TEST_FRAME`；H0 使用本地绘图测试，H1 才读取 raw bitmap。
不启动 Wi-Fi，不需要服务器在线。无 WebSocket/MQTT/数据库/插件/Agent/OTA/Deep Sleep。

## 目标与依赖选择

目标屏是 GDEY042T81：400×300 黑白、SSD1683、SPI、3.3V、24-pin 0.5 mm FPC。
这些是屏幕规格，不代表任意卖家的转接板、接线或 ESP32 型号已确认。
厂商在 25°C 标称全刷/快刷/局刷约 2/1.5/0.3 秒，工作温度 0–50°C；实际时间需实测。
厂商建议每连续 5 次快刷或局刷后全刷以减少残影。
见 [Good Display 官方产品参数](https://www.good-display.com/product/386.html)。

使用 GxEPD2 的既有 `GxEPD2_420_GDEY042T81` 驱动，而不是重写 SSD1683 波形或复制驱动。
它提供全幅位图、差分前后缓冲同步和刷新接口，契合“ESP32 只显示像素”的边界。
源码核验固定在 [GxEPD2 1.6.9 提交](https://github.com/ZinggJM/GxEPD2/commit/de82887e77a78528ea386e68bba2cb0291d2c319)。

`platformio.ini` 使用 `espressif32@6.12.0`、Arduino、`board = esp32dev`、C++17，
直接依赖固定为上述 GxEPD2 提交和 Adafruit GFX 1.12.6。通用 esp32dev 是用户选择的
**编译示例目标，不是实物型号确认**；不适用于未经调整的 ESP32-S2/S3/C3。
STEP-012 已解析并构建上述固定依赖，BusIO 实际为 1.17.4；完整工具版本与产物证据见环境报告。
这不是所有传递依赖的锁文件，恢复环境后仍需重新验证。
参考 [PlatformIO esp32dev](https://docs.platformio.org/en/stable/boards/espressif32/esp32dev.html)、
[固定平台清单](https://github.com/platformio/platform-espressif32/blob/v6.12.0/platform.json)。

STEP-013 新增 `esp32-m1` 环境，继承固定依赖并使用 `board=lolin32`。
厂商 ESP32epdx 1.0.9 仅隔离参考编译 PASS，不迁移驱动；详细版本、资源和哈希见统一审查。

## 安全默认值与配置

`include/display_config.example.h` 的 GPIO 全部是 **EXAMPLE ONLY**。
选择顺序为 local → `EINK_BOARD_ESP32_M1` 对应 `display_config.esp32_m1.h` → generic example。
跟踪的板级头文件确认位固定 0；只有 local 文件可使确认条件成立。
真正配置放在忽略的 `include/display_config.local.h` 中；还必须把本地文件中的
`EPD_WIRING_CONFIRMED` 改为 `1`，程序才会驱动显示 GPIO。设计允许无私有配置的默认构建，
该无私有配置路径已完成示例编译验证；源码中缺少本地确认时的运行路径只输出 `CONFIG_UNCONFIRMED`，
不会显示测试图，尚未在实体板验证这一运行行为。

| 配置 | 默认 | 含义 |
| --- | --- | --- |
| `EPD_BRINGUP_STAGE` | `0` | H0 测试图；实物通过后手动改为 `1` 进入 H1 |
| `EPD_RUN_REFRESH_DEMO` | `0` | H1 有限刷新演示，需手动启用 |
| `EPD_MAX_FAST_UPDATES` | `5` | 最多连续 5 次 PARTIAL/FAST_FULL，下次变更为 FULL |
| `EPD_MIN_REFRESH_INTERVAL_MS` | `5000` | 从上次驱动调用完成起等待，非 0.3 秒循环 |
| `EPD_PREFER_FAST_FULL` | `0` | 优先全屏局刷；设 `1` 才改用快速全刷波形 |
| `EPD_SPI_HZ` | `4000000` | SPI 起步频率，上限受骨架配置约束 |

几何、串口与默认常量集中在 `include/`。Wi-Fi 字段为空的预留占位，当前没有代码读取它们；
不要提交 SSID、密码、Token、真实服务器凭据或私有配置文件。

## 刷新与错误语义

首次成功提交为普通 `FULL`。之后内容不变或间隔未到时 `HOLD`；内容变化时优先
全屏 `PARTIAL`，不计算 dirty rectangles。5 次成功的快速更新后，下一次变更使用 `FULL`。
计数/时间只在驱动返回 `Submitted` 后推进；短时间更新不会清空最后画面。

`FAST_FULL` 是 GxEPD2 的快速全刷波形开关，不等于普通清残影全刷。
驱动的首次/清残影 `FULL` 显式调用 `selectFastFullUpdate(false)`；局刷后同步前后 RAM。
依据 [GxEPD2 目标屏驱动](https://github.com/ZinggJM/GxEPD2/blob/de82887e77a78528ea386e68bba2cb0291d2c319/src/gdey/GxEPD2_420_GDEY042T81.cpp)。

GxEPD2 的硬件调用返回 `void`，没有像素读回确认。本骨架的 `Submitted` 只表示调用返回、
BUSY 未持续为高，Serial 明确输出 `SUBMITTED_NOT_VISUALLY_VERIFIED`。BUSY 卡住时停止
后续更新；不自动清屏或反复重试。断开的 BUSY 若错误地读为低也可能绕过检测，必须实物检查。
`powerOff()` 仅关闭屏幕驱动电压，不是 ESP32 Deep Sleep。

## 使用与验收入口

STEP-010 检查与文档完成，环境准备尚未完成。先填写 [HARDWARE_ID_CARD](docs/HARDWARE_ID_CARD.md)，
环境与 ASSUMPTION 登记见 [H0_ENVIRONMENT_REPORT](../../docs/H0_ENVIRONMENT_REPORT.md)。
STEP-011 文档准备 COMPLETE，不代表环境或硬件验证完成；构建、上传、串口命令的工作目录和前置条件见
[BUILD_GUIDE](docs/BUILD_GUIDE.md)。STEP-012 已获准并完成隔离工具链下的示例构建，未执行上传或串口监视。
STEP-013 的实物证据与GPIO图纸已核对，详见 [统一审查](docs/STEP013_HARDWARE_AUDIT.md)。
当前RESE档位、实物FPC细节及屏幕SKU仍需确认，H0 PRE-FLIGHT=NO-GO。

先用 [H0_CHECKLIST](docs/H0_CHECKLIST.md) 收集材料并记录验收证据。
按 [WIRING](docs/WIRING.md) 核实实物，条件齐备后再严格按 [BRINGUP](docs/BRINGUP.md) 操作。
当前只可开始材料核对，尚不具备实机通电、烧录验收条件。
PARTIAL、连续局刷后的 FULL 和残影测试明确属于 H0 通过后的 H1，不提前执行。
故障排查见 [TROUBLESHOOTING](docs/TROUBLESHOOTING.md)，
raw 帧候选协议见 [FRAME_PROTOCOL](docs/FRAME_PROTOCOL.md)，测试命令见 [tests](tests/README.md)。
不要直接烧录未经确认的示例引脚，不要在本步骤开启网络或修改服务器绑定地址。

## 硬件目录文件（25个，不含忽略产物）

STEP-008 建立 19 个文件；STEP-009 增加 H0_CHECKLIST；STEP-010 增加 HARDWARE_ID_CARD。
STEP-011 增加 BUILD_GUIDE，并复用唯一 H0 清单，不新增根目录同名清单。
STEP-012 增加 requirements-hw.txt，只固定实际安装的 PlatformIO Core 6.1.19；未修改固件或帧协议。
STEP-013 文档基线增加统一审查，另增独立ESP32-M1板级头文件；保留原generic示例。

```text
gdey042t81_esp32/
├── README.md
├── platformio.ini
├── requirements-hw.txt
├── include/
│   ├── display_config.example.h
│   ├── display_config.esp32_m1.h
│   └── hardware_config.h
├── src/
│   ├── main.cpp
│   ├── display_driver.h / display_driver.cpp
│   ├── refresh_policy.h / refresh_policy.cpp
│   ├── frame.h
│   ├── frame_fetcher.h
│   └── test_frame.h
├── assets/README.md
├── tests/
│   ├── README.md
│   └── test_core.cpp
└── docs/
    ├── WIRING.md
    ├── BRINGUP.md
    ├── BUILD_GUIDE.md
    ├── H0_CHECKLIST.md
    ├── HARDWARE_ID_CARD.md
    ├── STEP013_HARDWARE_AUDIT.md
    ├── TROUBLESHOOTING.md
    └── FRAME_PROTOCOL.md
```

骨架建立时，目录之外仅修改 `.gitignore`、根 README、`progress.md`、`RESUME.txt`。
STEP-010/011 仅完善文档及状态记录，包括目录外的 `docs/H0_ENVIRONMENT_REPORT.md`。
既有 P1 代码与测试保持不变；STEP-009 未新增 Python 端点或测试。

## 方案取舍与停点

- 上策（本次采用）：H0/H1 独立骨架 + 文档协议；定位失败层次清楚，代价是暂时看不到实时业务数据。
- 中策（保底）：仅文档；维护成本最低，但无法提前审查固件路径。
- 下策（当前不采用）：同时增加联网、帧 API 与事件联动；最快接近整链演示，但失败时混入多个未知层。

交付后停在 H0 实机确认前，不宣布 H0/H1 物理验证完成，不自动进入 H2/H3 或正式硬件阶段。
STEP-009 使用两个本地提交：A 为 `Phase 4 P1 stable baseline`（不含硬件），
哈希 `5490ad0fc7ba12d96e95cf4665cf9857d1ef963e`；B 为
`feat: add GDEY042T81 ESP32 hardware scaffold`（包含本清单与最终状态文档）。
annotated tag `v0.4.1-phase4-hardware-scaffold` 指向 B，明确编译及实物验证未完成。
提交 B 前曾因 artifacts 内的隔离快照被 pytest 重复收集而暂停；用户允许迁移至仓库外后，
仓库和纯 P1 快照均重新通过 125 项测试。没有删除文件或修改测试配置。
不修改 remote、不推送，原 Phase 3 标签不变；这只是可回退的源码基线，不能称为硬件 stable。
STEP-011 只检查工具存在性，PlatformIO、Arduino CLI 为 NOT INSTALLED（当前检测范围内未发现）；
该历史步骤未安装、编译或烧录。STEP-012 则已安装独立 PlatformIO Core 6.1.19 并完成一次示例构建，
无需源码修复；完整结果见 [环境报告第 7 节](../../docs/H0_ENVIRONMENT_REPORT.md)。
7 组 C++ 测试仍为 BLOCKED / NOT RUN，原因是没有可调用的主机 C++17 编译器。
下一步需要P4/RESE近照、P5与FPC正反面近照和GDEY042T81销售型号证据；不为补资料连接硬件。
