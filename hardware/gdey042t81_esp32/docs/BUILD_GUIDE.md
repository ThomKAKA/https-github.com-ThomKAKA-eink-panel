# Build Guide — STEP-011 / STEP-012 / STEP-013

STEP-011 完成了文档准备；STEP-012 已获准安装隔离工具链并验证示例配置构建。
STEP-013 已识别ESP32-M1/WROOM-32D并获准板级配置与双路线编译，结果见
[统一审查](STEP013_HARDWARE_AUDIT.md)。文档基线时新增构建尚未执行。
本轮仍不连接硬件、不上传、不打开串口、不执行 H1。指南或构建完成不代表 H0 获准开始。

## Environment

下列命令的工作目录统一为：

```text
D:\Codex\eink-panel\hardware\gdey042t81_esp32
```

STEP-012 已将 PlatformIO Core **6.1.19** 安装到项目独立的 `.venv-hw`（Python 3.12.13）；
版本、完整依赖快照和构建结果见 [H0_ENVIRONMENT_REPORT](../../../docs/H0_ENVIRONMENT_REPORT.md) 第 7 节。
Arduino CLI 不是此流程的必需工具；不要向服务端 `.venv` 或系统 Python 安装 PlatformIO。

以后需要恢复环境时，仅在 `.venv-hw` 不存在时执行第一条命令；不要覆盖已有环境：

```powershell
& 'D:\Codex\eink-panel\.venv\Scripts\python.exe' -m venv 'D:\Codex\eink-panel\.venv-hw'
& 'D:\Codex\eink-panel\.venv-hw\Scripts\python.exe' -m pip --isolated install --index-url https://pypi.org/simple --no-cache-dir -r 'D:\Codex\eink-panel\hardware\gdey042t81_esp32\requirements-hw.txt'
& 'D:\Codex\eink-panel\.venv-hw\Scripts\python.exe' -m pip check
```

`requirements-hw.txt` 固定实际验证的 Core 版本，不完整锁定 Python 或平台的传递依赖。
恢复时应重新记录依赖与构建结果。以下使用绝对路径，不需要激活环境或更改执行策略。

STEP-012 历史 [platformio.ini](../platformio.ini) 基线：

| 配置 | 固定值 / 边界 |
| --- | --- |
| 环境 / board | `esp32dev`；历史通用经典 ESP32 示例 |
| platform | `espressif32@6.12.0` |
| framework | `arduino` |
| C++ | 移除 `-std=gnu++11`，使用 `-std=gnu++17` |
| GxEPD2 | Git 提交 `de82887e77a78528ea386e68bba2cb0291d2c319` |
| Adafruit GFX Library | `1.12.6` |
| Serial | `115200`；不是已经识别或验证的串口 |

这些是声明的配置；本轮实际解析与构建证据另见环境报告，不能由配置表推断成功。GxEPD2 目标类为
`GxEPD2_420_GDEY042T81`，静态源码核对不能替代真实构建。
STEP-013 的 `esp32-m1` 环境将使用 `board=lolin32`，保留上述generic环境及固定平台/依赖。
本地board定义的4MB/40MHz/DIO是构建配置，不作为实物测量结果；不是说明书Core3.1.1的复现。

## Build

STEP-012 已获准以下示例构建。以后在 Windows PowerShell 中使用相同隔离目录：

```powershell
$env:PLATFORMIO_CORE_DIR = 'D:\Codex\eink-panel\.venv-hw\pio-core'
$env:PLATFORMIO_SETTING_ENABLE_TELEMETRY = 'false'
$env:PLATFORMIO_DISABLE_UPGRADE_CHECK = 'true'
Set-Location -LiteralPath 'D:\Codex\eink-panel\hardware\gdey042t81_esp32'
& 'D:\Codex\eink-panel\.venv-hw\Scripts\pio.exe' --version
& 'D:\Codex\eink-panel\.venv-hw\Scripts\pio.exe' project config
& 'D:\Codex\eink-panel\.venv-hw\Scripts\pio.exe' run -e esp32dev
```

首次构建可能下载平台、交叉编译器、框架和库，需要确认网络、磁盘空间及下载授权。
上述环境变量只影响当前 PowerShell 进程及其子进程；不要使用 `setx` 或修改全局 PATH。
core_dir 存放平台、工具链与缓存，硬件目录的 `.pio` 存放构建结果，两者均被忽略。
保留命令、工作目录、工具版本、实际依赖版本/提交、完整构建日志和退出结果，
并关联到 [H0_CHECKLIST](H0_CHECKLIST.md) 的依赖解析与编译检查项。
若解析或编译失败，保存错误并停止，不擅自升级依赖、修改驱动或伪造成功。

STEP-012 已真实验证无私有配置的默认构建路径，退出码为 0；**仅为 example esp32dev profile 编译验证**。
默认配置的源码保护意图是不驱动显示 GPIO，只报告配置未确认，不意味着屏幕测试通过。
本步骤不创建 `include/display_config.local.h`，不填写真实 GPIO；运行路径保持配置未确认的保护状态。
即使将来 Build 成功，仍不等于接线正确或 `HARDWARE VERIFIED=YES`。

## Upload

后续实机步骤才可执行，不属于 STEP-012。**DO NOT RUN UNTIL HARDWARE ID IS CONFIRMED**。
硬件身份确认也不代表自动获准上传，还需下列条件全部满足：

- 已核对 [HARDWARE_ID_CARD](HARDWARE_ID_CARD.md) 中的板型、驱动板、屏幕/FPC、供电和接线。
- 已完成对应配置的构建，保留成功日志；H0 配置和私有接线记录已经人工核对。
- 已获准进行实机操作，目标板与串口唯一明确；不猜端口、不预填 COM 编号。

以下是命令说明，**尚未执行**：

```powershell
& 'D:\Codex\eink-panel\.venv-hw\Scripts\pio.exe' run -e esp32dev -t upload
```

有多个端口或无法确认目标时停止，先确认目标，再按需使用 `--upload-port` 指定已核对的端口。
不要让工具自动选择未经确认的设备。上传可能触发构建，须同样保留日志。

## Monitor

仅在上述实机前置条件通过、上传成功且目标串口已确认后，按
[BRINGUP](BRINGUP.md) 查看日志。本步骤不连接或打开任何串口。

```powershell
& 'D:\Codex\eink-panel\.venv-hw\Scripts\pio.exe' device monitor -b 115200
```

存在端口歧义时不要运行，先核对设备，再按需用 `-p` 指定已确认的串口，不在本指南填入实际端口。
记录 Serial 日志与实物照片；`SUBMITTED_NOT_VISUALLY_VERIFIED` 不代表像素显示已验证。
H0 只验收首次初始化和普通 FULL；PARTIAL、连续局刷后的 FULL、残影检查均需 H0 通过后再进入 H1。

## 当前状态

| 项目 | 状态 |
| --- | --- |
| STEP-010 | 检查与文档完成，环境准备尚未完成 |
| STEP-011 | COMPLETE：仅文档准备，不代表硬件验证完成 |
| STEP-012 | COMPILE VERIFIED：example esp32dev profile only，退出码 0 |
| P1 软件 / P1.5 | STABLE / SCAFFOLD COMPLETE |
| IMPLEMENTED | YES（源码骨架） |
| Build / Upload / Monitor | Build 成功；Upload / Monitor 尚未执行 |
| 七组主机 C++ 测试 | BLOCKED / NOT RUN；当前没有可调用的主机 C++17 编译器 |
| COMPILE VERIFIED | YES — example esp32dev profile only |
| REAL BOARD IDENTIFIED / HARDWARE VERIFIED | YES（ESP32-M1/WROOM-32D） / NO |
| H0 | NO-GO，实物RESE/FPC/SKU尚未确认 |

七组主机逻辑测试不依赖 Arduino、GxEPD2 或实物，详见 [tests/README](../tests/README.md)。
实机下一步仍只收集硬件资料；尚未接线则注明“未接线”，不用为补资料连接硬件。本步骤不进入 H0 实机验收或 H1/H2/H3。
