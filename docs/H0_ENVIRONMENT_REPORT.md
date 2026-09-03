# Development Environment

STEP-010 / STEP-011，Phase 4 P1.5 Hardware Bring-up Preparation。
检查日期：2026-09-03，Asia/Shanghai；STEP-010 首次本机工具版本探测为 12:13，
STEP-011 于 12:30 再次只读核验。

Status: **READY FOR HARDWARE IDENTIFICATION**。
这表示资料核对可以开始，不表示环境已可编译，更不是允许接线、通电或烧录。

| 项目状态 | 结果 |
| --- | --- |
| STEP-009 | COMPLETED：两次本地提交及骨架标签已核验 |
| STEP-010 | 检查与文档完成，环境准备尚未完成 |
| STEP-011 | COMPLETE：文档准备完成，环境与硬件验证仍未完成 |
| Hardware scaffold | COMPLETE |
| Environment preparation | IN PROGRESS |
| H0 | BLOCKED BY HARDWARE IDENTIFICATION |
| COMPILE VERIFIED / HARDWARE VERIFIED | NO / NO |

## 1. 本机工具与检测范围

| 工具 | 版本 / 状态 | 本次证据 |
| --- | --- | --- |
| 项目 Python | 3.12.13 | `.venv/Scripts/python.exe --version` |
| pytest | 8.4.1 | 项目虚拟环境运行 `-m pytest --version` |
| Git | 2.53.0.windows.2 | `git --version` |
| PlatformIO | installed: NO；NOT INSTALLED（当前检测范围内未发现） | `platformio`、`pio` 不在 PATH；项目虚拟环境无 platformio 模块；常用安装目录不存在 |
| Arduino CLI | installed: NO；NOT INSTALLED（当前检测范围内未发现） | `arduino-cli` 不在 PATH |
| ESP32 toolchain | available: NO（当前检测范围内未发现） | Xtensa ESP32/ESP32-S3、RISC-V 编译器及 `idf.py` 不在 PATH；常用工具链目录不存在 |
| Host C++ compiler | available: NO（当前会话）；测试 BLOCKED / NOT RUN | `g++`、`clang++`、`cl` 均不在 PATH，没有可调用的主机 C++17 编译器 |

只检查当前 PATH、项目虚拟环境与常用 PlatformIO、Arduino15、Espressif 工具目录，
没有扫描全盘或所有自定义安装位置。因此 NO 不代表已经证明整台机器绝无离线安装。
具体目录探测：用户目录下 `.platformio/penv/Scripts/platformio.exe`、`.platformio/packages`、
`AppData/Local/Arduino15/packages/esp32`、`.espressif/tools`，以及 `C:/Espressif/tools`；均未发现。
如果工具安装在其他位置，需要用户提供路径后再做只读核验。
PATH 的 `python` 指向另一个 Python 安装目录；本次始终使用项目 Python 3.12，不混用环境。
没有安装、升级、下载构建依赖、编译 C++/ESP32、连接串口或烧录；下列上游静态证据沿用 STEP-010 的只读核验。

## 2. 仓库与目录完整性

- 分支：`main`；STEP-010 检查开始时工作区干净；STEP-011 开始时保留 STEP-010 的 5 份未提交文档改动。
- A：`5490ad0fc7ba12d96e95cf4665cf9857d1ef963e`，纯 P1 软件基线。
- B / HEAD：`fbfd478e284cacee6c8da63eff44d1678f2ad507`，硬件骨架基线。
- `v0.4.1-phase4-hardware-scaffold` 是 annotated tag，指向 B；Phase 3 标签保持不变。
- STEP-010 Python 回归：`125 passed in 0.86s`；当时 `git diff --check` 通过。STEP-011 的回归与文档检查结果见 [progress](../progress.md)。
- 未提交、未打新标签、未修改 remote 或推送；本次产物是待用户审阅的文档修改。

硬件基线的 20 个文件全部存在，没有需要重建的缺失项：

| 分组 | 检查结果 |
| --- | --- |
| README / platformio.ini | 齐全；INI 可解析 |
| src | `main.cpp`、`display_driver.h/.cpp`、`refresh_policy.h/.cpp`、`frame.h`、`frame_fetcher.h`、`test_frame.h` 齐全 |
| include | `display_config.example.h`、`hardware_config.h` 齐全 |
| docs | BRINGUP、WIRING、FRAME_PROTOCOL、TROUBLESHOOTING、H0_CHECKLIST 齐全 |
| assets / tests | 位图说明、测试说明及 `test_core.cpp` 齐全 |

STEP-010 新增 [Hardware Identification](../hardware/gdey042t81_esp32/docs/HARDWARE_ID_CARD.md)，硬件目录变为 21 个文件；
STEP-011 新增 [BUILD_GUIDE](../hardware/gdey042t81_esp32/docs/BUILD_GUIDE.md) 后为 22 个文件。
复用原有唯一 H0_CHECKLIST，不另建根目录同名清单。
`display_config.local.h` 不存在且已被 Git 忽略；这不是骨架缺失，
本次不创建它，不复制示例 GPIO 为真实接线。

## 3. PlatformIO 配置分析（只读）

本地依据：[platformio.ini](../hardware/gdey042t81_esp32/platformio.ini)、
[display_driver.cpp](../hardware/gdey042t81_esp32/src/display_driver.cpp)。

| 配置项 | 当前值 | 判断 |
| --- | --- | --- |
| platform | `espressif32@6.12.0` | 已固定平台版本，不代表本机已安装 |
| default_envs / board | `esp32dev` | 明确的通用经典 ESP32 编译目标；ASSUMPTION，不是实物型号 |
| framework | `arduino` | 已明确；使用框架不等于必须安装 Arduino CLI |
| C++ 标准 | 去除 `gnu++11`，加入 `gnu++17` | 与骨架 inline constexpr、嵌套 namespace 等用法一致 |
| GxEPD2 | Git 提交 `de82887e77a78528ea386e68bba2cb0291d2c319` | 固定源码版本；不是已经完成依赖解析 |
| Adafruit GFX | `1.12.6` | 直接依赖固定；传递依赖尚未在本机解析 |
| monitor_speed | `115200` | 与本地串口配置一致；未打开串口验证 |

上游只读核验：平台 6.12.0 声明 PlatformIO Core 6 系列要求和 Arduino 框架，
`esp32dev` 的 MCU 是 `esp32`，名称为 Espressif ESP32 Dev Module。
它不是自动识别出的开发板，也不能直接当作 ESP32-S2/S3/C3 的配置。
依据：[固定平台清单](https://github.com/platformio/platform-espressif32/blob/v6.12.0/platform.json)、
[固定板型定义](https://github.com/platformio/platform-espressif32/blob/v6.12.0/boards/esp32dev.json)。

固定 GxEPD2 源码版本为 1.6.9；`GxEPD2_BW.h` 包含目标屏头文件，
目标类 `GxEPD2_420_GDEY042T81` 定义 400×300、SSD1683 目标，并提供骨架使用的
`writeImageForFullRefresh`、`writeImageAgain`、`selectFastFullUpdate` 等接口；BW 包装类也有
接收 SPI 实例与 SPISettings 的 init 重载。
依据：[库版本](https://github.com/ZinggJM/GxEPD2/blob/de82887e77a78528ea386e68bba2cb0291d2c319/library.properties)、
[BW 包装类](https://github.com/ZinggJM/GxEPD2/blob/de82887e77a78528ea386e68bba2cb0291d2c319/src/GxEPD2_BW.h)、
[目标屏驱动头文件](https://github.com/ZinggJM/GxEPD2/blob/de82887e77a78528ea386e68bba2cb0291d2c319/src/gdey/GxEPD2_420_GDEY042T81.h)。

结论：**静态检查未发现目标类缺失或明显配置冲突，存在可进行首次编译的源码路径；
不能据此保证构建成功。COMPILE VERIFIED 仍为 NO。**
Adafruit GFX 1.12.6 还声明 Adafruit BusIO 依赖；首次获准构建时应记录解析结果、编译日志和
内存报告，不在本步骤擅自换版本或补依赖。
依据：[GFX 1.12.6 依赖声明](https://github.com/adafruit/Adafruit-GFX-Library/blob/1.12.6/library.properties)。

修改建议仅限将来：实物型号若不匹配 esp32dev，应先提出准确的 board/配置变更供确认；
当前没有足够实物证据支持修改 platform、board、GPIO、驱动或依赖，因此均保持原样。

## 4. ASSUMPTION 登记：不是实物事实

扫描范围：根 README、docs、hardware 的说明、INI 和源码。保留全部既有内容；
已有 EXAMPLE ONLY 标记在此统一登记为 ASSUMPTION，不通过修改固件来做标记。

| 位置 / 已有值 | 标记 | 待确认内容 |
| --- | --- | --- |
| platformio.ini 第 1–8 行；硬件 README 的 esp32dev 示例 | ASSUMPTION | 用户的 ESP32 芯片、开发板型号、版本和构建目标是否匹配 |
| display_config.example.h 第 7–12 行；WIRING 示例表 | ASSUMPTION | 现有示例 CS=5、DC=17、RST=16、BUSY=4、SCK=18、MOSI=23，不是接线建议；真实 GPIO 全为 UNKNOWN |
| 根 README 的通用 esp32dev/GPIO 说明 | ASSUMPTION（已有示例警告） | 不能从文档中的示例反推实物已确认 |
| 硬件 README / WIRING / H0_CHECKLIST 的屏幕与 FPC 要求 | ASSUMPTION（作为用户实物的身份判断） | GDEY042T81 是软件目标；实物标签、排线、触点方向与接口兼容性尚未确认，FPC=UNKNOWN |
| 3.3V 供电与逻辑要求 | TARGET REQUIREMENT；实物符合性为 ASSUMPTION | 驱动板电路、供电能力、信号电压、公共地未核验；Confirmed=NO |
| 驱动板 / 转接板 | UNKNOWN | 没有证据确认具体型号或兼容性；未发现把某一具体驱动板型号强制当成用户实物的实现 |
| tests/README 的无私有配置默认构建路径（STEP-011 已限定措辞） | ASSUMPTION / 设计意图 | 只确认源码存在受保护的默认配置路径；尚无首次构建记录，不能解读为编译已通过 |

3.3V 要求也见上述目标屏驱动头文件；ESP32 开发板的 USB 供电与屏幕逻辑电压不是同一概念。
模板中的 Model、Resolution、Driver 是目标规格；未收到照片前，不将它们升级为实物确认结果。

## 5. 七组 C++ 测试与运行条件

来源：[test_core.cpp](../hardware/gdey042t81_esp32/tests/test_core.cpp)。
这不是 7 个测试文件或 7 次硬件测试，而是一个主机可执行程序依次调用 7 个测试函数。

| 函数（当前行号） | 检查内容 | 本次结果 |
| --- | --- | --- |
| firstFrameAndFailure（13） | 首帧 FULL；未记录成功或记录 None 不推进状态 | BLOCKED / NOT RUN |
| unchangedAndThrottled（22） | 同帧保持；最小刷新间隔及其边界 | BLOCKED / NOT RUN |
| fivePartialThenFull（30） | 连续 5 次 PARTIAL 后下次变更 FULL，并清零计数 | BLOCKED / NOT RUN |
| fastFullAndZeroLimit（45） | FAST_FULL 分支与禁用快速更新 | BLOCKED / NOT RUN |
| millisWraparound（57） | uint32 毫秒计时回绕 | BLOCKED / NOT RUN |
| frameValidationAndLayout（64） | 空指针、15,000 字节边界、黑白极性、MSB-first 及 A/B 差异 | BLOCKED / NOT RUN |
| disabledFetcherPreservesBuffer（80） | 禁用 fetcher 返回 0 字节且不写目标缓冲 | BLOCKED / NOT RUN |

运行条件：已安装且可调用的主机 C++17 编译器及标准库，include/src 头文件搜索路径，
共同编译 `tests/test_core.cpp` 和 `src/refresh_policy.cpp`，不能定义 NDEBUG 关闭断言。
当前阻塞原因是没有可调用的主机 C++17 编译器，并非必须等实物到位；本步骤也未授权 C++ 构建或执行。
本地配置应保持缺省/未创建，避免把个人板卡设置混入默认逻辑测试。
不需要 Arduino、GxEPD2、SPI、ESP32 交叉编译器、网络或实物。
已有示例命令见 [tests/README](../hardware/gdey042t81_esp32/tests/README.md)，本次未执行。
将来即使这 7 组通过，也不能据此把 ESP32 固件编译或 H0 标为通过。

## 6. 硬件身份与停止条件

| Hardware | 当前记录 |
| --- | --- |
| ESP32 | UNKNOWN |
| Driver board | UNKNOWN |
| Display | GDEY042T81（目标；实物未确认） |
| FPC / GPIO / USB | UNKNOWN |
| Logic voltage | 3.3V（目标要求）；Confirmed=NO |

下一步由用户提供：ESP32 芯片/开发板完整型号及正反面照片、驱动板型号及正反面照片、
屏幕背面标签和 FPC/接口近照，以及已有接线的断电照片/接线表。
若尚未接线，填写“未接线”即可，不为拍照而接线或通电；未知项继续填 UNKNOWN。
如有卖家板卡资料、原理图和供电说明，也请一并提供。

将证据登记到硬件身份卡后，先完成型号与接口核对，再由用户单独批准工具链准备和首次编译。
本步骤停在资料核对：不进入 H0/H1/H2/H3，不安装工具，不修改 GPIO/驱动，不写 Wi-Fi、HTTP 或 Frame API。
