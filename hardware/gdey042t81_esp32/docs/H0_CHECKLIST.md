# H0 实机验收清单（待执行）

STEP-009 建立；STEP-013 更新 / 2026-09-09。仅有证据支持的资料与构建项目勾选；源码提交、Python 测试或 Serial 提交日志
都不能代替实物验收。当前仅可开始材料核对，尚不具备实机通电、烧录验收条件。

当前状态：P1 软件 STABLE；P1.5 SCAFFOLD COMPLETE；IMPLEMENTED=YES、
COMPILE VERIFIED=YES（STEP-012 example esp32dev历史）、REAL BOARD IDENTIFIED=YES（ESP32-M1/WROOM-32D）、HARDWARE VERIFIED=NO。
7 组 C++ 测试为 BLOCKED / NOT RUN。隔离环境已安装 PlatformIO Core 6.1.19，Arduino CLI 仍未发现；证据见
[环境报告](../../../docs/H0_ENVIRONMENT_REPORT.md) 第 7 节。未烧录或打开串口。
STEP-010/011 检查与文档完成，STEP-012 示例编译通过；ESP32-M1 受保护配置编译通过，实机条件仍未完成，
STEP-013 实物已到，H0 PRE-FLIGHT=NO-GO；新构建结果见 [统一审查](STEP013_HARDWARE_AUDIT.md)。

## 一、H0 材料与断电核对

按 [WIRING](WIRING.md) 逐项确认。先断开 USB 与外部供电，再接线或插拔 FPC；
型号、电压或连接方向有疑问时停止，不用示例 GPIO 代替实物确认。

- [ ] 屏幕实物与标签照片确认型号为 GDEY042T81，目标为 400×300、SSD1683。
- [x] 照片和官方资料确认 ESP32-M1 / ESP32-WROOM-32D；实物板修订号仍UNKNOWN。
- [x] 板载电子纸驱动及P5已由原理图确认；标准屏SKU和实际RESE档位待确认。
- [ ] 确认屏幕/接口供电与逻辑信号为 3.3V，并核对公共 GND、极性、供电能力及无短路。
- [ ] 确认 24-pin FPC、触点方向与锁扣，断电检查插入深度、对齐及无损伤。
- [x] 原理图确认六个GPIO与P5对应；主路线板载连接，不要求新增杜邦线。
- [x] 厂商P5显示面朝上/压下黑色锁扣规则及电气Pin1=NC已登记。
- [x] RESE目标2.2Ω及Type-C DC5V输入路径已登记（图纸证据，未测量）。
- [ ] 实物P4当前档位可辨识，确认与2.2Ω匹配。
- [ ] 实物Pin1、FPC触点、锁扣状态及保护膜保留情况完成当前近照核对。
- [ ] 实物核对通过后，才另行准备被忽略的 display_config.local.h；本步骤不创建或填写它。

下一步需要P4/RESE、P5/FPC正反面近照及销售型号证据。
尚未接线则注明“未接线”，不为补齐照片而接线。
以上未确认前，不放行接屏通电或烧录验收。

## 二、H0 软件与工具链（条件齐备后再执行）

命令、工作目录和日志要求见 [BUILD_GUIDE](BUILD_GUIDE.md)，实机操作顺序见
[BRINGUP](BRINGUP.md)。本清单不是自动安装、构建或烧录授权。

- [x] 用户批准并完成独立 `.venv-hw` 中的 PlatformIO Core 6.1.19 安装，安装退出码 0、pip check 通过；Arduino CLI 不是必需工具。
- [x] 说明书WEMOS LOLIN32对应本地平台lolin32定义；实物容量/运行适配未验证。
- [x] PROJECT ESP32-M1 profile实际构建成功，保存退出码、日志和产物哈希。
- [x] VENDOR REFERENCE样例编译 PASS 已记录；不能代替项目或实物验收。
- [x] GxEPD2 1.6.9 / de82887、GFX 1.12.6、BusIO 1.17.4 成功解析；固定提交、框架及工具版本与日志见环境报告第 7 节。
- [ ] 运行并记录 7 组主机 C++ 核心测试结果；当前为 BLOCKED / NOT RUN，缺少可调用的主机 C++17 编译器，不能由 Python 测试替代。
- [x] 获准后运行隔离环境的 `pio run -e esp32dev`，示例配置构建成功，退出码 0；日志为 `artifacts/step012-20260903-1256/build-attempt-01.log`，命令、产物哈希和资源占用见环境报告。本项仅验收历史示例构建；本轮 generic 回归也通过，ESP32-M1 编译证据见统一审查，实机适配未验收。
- [ ] 确认私有接线配置已核对，H0 stage=0、刷新演示关闭、网络保持禁用。
- [ ] 目标板与串口唯一明确，按操作说明上传成功；不猜串口、不批量烧录。
- [ ] Serial 输出正常，保留日志，确认本地测试源、FrameFetcher 禁用、Wi-Fi 关闭。

## 三、H0 显示验收（接线与软件条件全部通过后）

- [ ] 显示初始化完成，无 BUSY 超时、持续忙信号或异常复位。
- [ ] 实物出现 E-INK TEST、400x300、GDEY042T81 及实心/空心矩形、横线、外框。
- [ ] 首次普通 FULL 刷新正常；这是 H0 全刷，不是 PARTIAL 或 FAST_FULL 演示。
- [ ] 测试图方向、边框、黑白极性正确，画面保持且不循环闪烁；保存实物照片。
- [ ] 人工确认 H0 通过，记录日期、板型、私有接线记录位置、固件版本和 Serial/照片证据。

`SUBMITTED_NOT_VISUALLY_VERIFIED` 只说明提交调用返回，不能据此勾选显示成功。
出现 BUSY 异常、复位或画面不符时停止，不反复刷新掩盖问题。

## 四、H0 通过后的 H1 验收（当前禁止提前执行）

本节不属于 H0 点亮验收，必须先人工确认 H0 通过，再按 BRINGUP 单独启用 H1。

- [ ] 本地 400×300、1-bit、15,000 字节 raw 帧显示正常：逐行、MSB-first、0 黑/1 白。
- [ ] 全幅帧四边、非对称角标、单像素边界与方向正确，确认像素 1:1。
- [ ] 手动启用有限演示后 PARTIAL 正常；保持默认至少 5 秒间隔，不进行高频刷新。
- [ ] 验证 FULL → PARTIAL × 5 → 普通 FULL → DEMO FINISHED，并核对清零与停止行为。
- [ ] 检查局刷后与普通全刷后的残影，保存对比照片和环境记录。
- [ ] 完成记录并关闭有限演示；H1 结果不能自动放行 H2/H3。

本清单不涉及 Frame API、Wi-Fi/HTTP 拉帧、事件同步、WebSocket/MQTT、OTA、
Deep Sleep、电池或外壳。H2/H3 仍需单独批准。
