# Build Guide — STEP-011

本指南只准备后续操作说明。本步骤不安装工具、不执行以下命令、不编译固件或 C++ 测试，
不连接硬件、不上传、不打开串口。指南完成不代表 H0 获准开始。

## Environment

下列命令的工作目录统一为：

```text
D:\Codex\eink-panel\hardware\gdey042t81_esp32
```

需要已安装且可调用的 PlatformIO Core 6 系列，以及由平台解析的 ESP32 工具链。
当前 PlatformIO 为 **NOT INSTALLED（当前检测范围内未发现）**；检测范围和版本记录见
[H0_ENVIRONMENT_REPORT](../../../docs/H0_ENVIRONMENT_REPORT.md)。Arduino CLI 不是此构建流程的必需工具。

现有 [platformio.ini](../platformio.ini) 保持不变：

| 配置 | 固定值 / 边界 |
| --- | --- |
| 环境 / board | `esp32dev`；仅为通用经典 ESP32 示例，实物型号仍为 UNKNOWN / ASSUMPTION |
| platform | `espressif32@6.12.0` |
| framework | `arduino` |
| C++ | 移除 `-std=gnu++11`，使用 `-std=gnu++17` |
| GxEPD2 | Git 提交 `de82887e77a78528ea386e68bba2cb0291d2c319` |
| Adafruit GFX Library | `1.12.6` |
| Serial | `115200`；不是已经识别或验证的串口 |

这些是声明的配置，不是本机依赖解析或构建成功记录。GxEPD2 目标类为
`GxEPD2_420_GDEY042T81`；静态源码核对不能替代首次构建。传递依赖仍待解析并记录。
如果实物不匹配 `esp32dev`，先提出配置建议并获得确认，不套用示例、不自行改板型或 GPIO。

## Build

仅在工具链准备完成并获得单独批准后，才可在上述硬件目录执行：

```powershell
pio run -e esp32dev
```

首次构建可能下载平台、交叉编译器、框架和库，需要确认网络、磁盘空间及下载授权。
保留命令、工作目录、工具版本、实际依赖版本/提交、完整构建日志和退出结果，
并关联到 [H0_CHECKLIST](H0_CHECKLIST.md) 的依赖解析与编译检查项。
若解析或编译失败，保存错误并停止，不擅自升级依赖、修改驱动或伪造成功。

设计意图是无私有配置也有受保护的默认构建路径；**该路径尚未构建验证**。
默认配置的源码保护意图是不驱动显示 GPIO，只报告配置未确认，不意味着屏幕测试通过。
本步骤不创建 `include/display_config.local.h`，不填写真实 GPIO。
即使将来 Build 成功，仍不等于接线正确或 `HARDWARE VERIFIED=YES`。

## Upload

后续实机步骤才可执行，不属于 STEP-011。前置条件：

- 已核对 [HARDWARE_ID_CARD](HARDWARE_ID_CARD.md) 中的板型、驱动板、屏幕/FPC、供电和接线。
- 已完成对应配置的构建，保留成功日志；H0 配置和私有接线记录已经人工核对。
- 已获准进行实机操作，目标板与串口唯一明确；不猜端口、不预填 COM 编号。

以下是命令说明，**尚未执行**：

```powershell
pio run -e esp32dev -t upload
```

有多个端口或无法确认目标时停止，先确认目标，再按需使用 `--upload-port` 指定已核对的端口。
不要让工具自动选择未经确认的设备。上传可能触发构建，须同样保留日志。

## Monitor

仅在上述实机前置条件通过、上传成功且目标串口已确认后，按
[BRINGUP](BRINGUP.md) 查看日志。本步骤不连接或打开任何串口。

```powershell
pio device monitor -b 115200
```

存在端口歧义时不要运行，先核对设备，再按需用 `-p` 指定已确认的串口，不在本指南填入实际端口。
记录 Serial 日志与实物照片；`SUBMITTED_NOT_VISUALLY_VERIFIED` 不代表像素显示已验证。
H0 只验收首次初始化和普通 FULL；PARTIAL、连续局刷后的 FULL、残影检查均需 H0 通过后再进入 H1。

## 当前状态

| 项目 | 状态 |
| --- | --- |
| STEP-010 | 检查与文档完成，环境准备尚未完成 |
| STEP-011 | COMPLETE：仅文档准备，不代表环境或硬件验证完成 |
| P1 软件 / P1.5 | STABLE / SCAFFOLD COMPLETE |
| IMPLEMENTED | YES（源码骨架） |
| Build / Upload / Monitor | 尚未执行 |
| 七组主机 C++ 测试 | BLOCKED / NOT RUN；当前没有可调用的主机 C++17 编译器 |
| COMPILE VERIFIED / HARDWARE VERIFIED | NO / NO |
| H0 | BLOCKED BY HARDWARE IDENTIFICATION |

七组主机逻辑测试不依赖 Arduino、GxEPD2 或实物，详见 [tests/README](../tests/README.md)。
当前只收集硬件资料；尚未接线则注明“未接线”，不用为补资料连接硬件。本步骤不进入 H0 实机验收或 H1/H2/H3。
