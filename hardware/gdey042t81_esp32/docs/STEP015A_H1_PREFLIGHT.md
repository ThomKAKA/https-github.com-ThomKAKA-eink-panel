# STEP-015A — Project GxEPD2 H1 Pre-Flight

日期：2026-09-10。范围：现有配置静态审计、增量编译和 Python 回归；不修改驱动、配置或第三方库，不操作硬件。

## 结论与基线

- `H1 PHYSICAL TEST PRE-FLIGHT = NO-GO`。
- 起始 HEAD：`f24d0c0e3ffdf178fb05fe226e71406dd7461b30`；暂存区为空，原始 `hardware/evidence/` 未跟踪，保持不处理。
- [H0 审计](STEP014_H0_AUDIT.md) 的 H0 PASS 不变，仅限厂商 H0-safe 显示链路及八种几何方向验收。
- `PROJECT GXEPD2 PHYSICALLY VERIFIED = NO`；逐像素、休眠、局刷、快刷、联网未获得本轮实机验证。
- 未创建 H1-safe 入口，未解除接线保护，不提供上传命令。

## 实际调用链与配置

[main.cpp](../src/main.cpp) 的 `setup → DisplayDriver::begin` 首先检查私有配置确认位。
当前 `include/display_config.local.h` 不存在；两个配置均返回 `CONFIG_UNCONFIRMED`，不会执行显示 GPIO 初始化或刷新。
受版本控制的配置默认 `EPD_BRINGUP_STAGE=0`、`EPD_RUN_REFRESH_DEMO=0`。

如果未来另行授权并确认配置，stage 0 进入 `showTestPattern → display.display(false)`；stage 1 进入 `submit(frameA, policy.decide) → displayFrame`。
stage 1 目前仍依赖刷新策略，不是独立 H1 单帧验收入口。循环演示默认禁用；FrameFetcher 禁用，无 Wi-Fi/HTTP 路径启动。

[display_driver.cpp](../src/display_driver.cpp) 使用全高缓冲对象 `GxEPD2_BW<GxEPD2_420_GDEY042T81, HEIGHT>`，准确屏类为 `GxEPD2_420_GDEY042T81`，400×300。
[platformio.ini](../platformio.ini) 固定 GxEPD2 提交 `de82887e77a78528ea386e68bba2cb0291d2c319`（1.6.9），GFX 1.12.6，espressif32 6.12.0。

| 信号 | H0 已验证 | esp32-m1 | generic esp32dev |
| --- | ---: | ---: | ---: |
| BUSY | 13 | 13 MATCH | 4 MISMATCH |
| RST | 12 | 12 MATCH | 16 MISMATCH |
| DC | 14 | 14 MATCH | 17 MISMATCH |
| CS | 27 | 27 MATCH | 5 MISMATCH |
| SCK | 18 | 18 MATCH | 18 MATCH |
| MOSI | 23 | 23 MATCH | 23 MATCH |

generic 是历史示例，不改成实物板型。项目 SPI 为 4 MHz / MSB-first / MODE0，H0-safe 为 10 MHz / MSB-first / MODE0；频率差异明确保留，并非本轮实物时序验证。

## 阻塞一：首次 FULL 隐含双刷新

证据来自本机固定版本 `hardware/gdey042t81_esp32/.pio/libdeps/esp32-m1/GxEPD2/src/gdey/GxEPD2_420_GDEY042T81.cpp`，以及 `GxEPD2_EPD.cpp`、`GxEPD2_BW.h`。

`begin` 传入 `init(..., initial=true, ...)`，设置 `_initial_write=true`。
首次 `writeImageForFullRefresh → _writeImage → writeScreenBuffer → clearScreen → refresh(false)` 先产生清白 FULL，然后调用方 `refresh(false)` 再产生测试帧 FULL。
两次均使用关闭 fast-full 后的普通 `0x22=0xF7; 0x20` 更新。

因此：当前受保护路径物理刷新触发数为 0；假定解除保护后的首次正常 FULL 路径静态触发数为 2，而非 1。stage 0 的 `display(false)` 也经同一初始写入链。
这里统计的是更新激活，不是两个 RAM 平面、分页传输或肉眼闪烁次数。
`fillScreen` 只清绘图缓冲，本身不是上述额外物理刷新来源。

## 阻塞二：有限 BUSY 超时不等于错误传播

屏类向基类传入 `busy_timeout=10000000` 微秒（约 10 秒）。`_waitWhileBusy` 使用无符号 `micros()-start`、短延时/yield，并在超时打印 `Busy Timeout!` 后 break。
函数返回 void，不传播失败；调用方仍会继续设置内部状态或发送后续命令。
例如隐含清屏的等待超时后，写图和第二次刷新仍可继续。

项目在显式刷新返回后检查 BUSY HIGH 并使 driver 失效，但无法追溯此前已发生、随后 BUSY 恢复 LOW 的超时，也无法阻止库内部已继续执行的命令。
这不是无限等待问题，本轮不额外实现第二套超时或修改库。
`powerOff()` 不等同于 ESP32 深度睡眠；现有 `displayFrame` 也未调用 `hibernate()`。任何休眠实测结论均不成立。

## 方向与测试图

[test_frame.h](../src/test_frame.h) 为 400×300、每行 50 字节、15,000 字节，逐行 MSB-first、0 黑/1 白；`blackPixel` 索引为 `y*50+x/8`。
当前 frameA 含 1 像素外框、四角非对称标记、对角线和字节边界探针，与 H0 的 4 像素框、十字、中心块、实心/空心角块不是同一图；本轮不转换或替换。

| 项目 | H0-safe | 当前 GxEPD2 原始帧路径 |
| --- | --- | --- |
| Data Entry | 0x01，X 增/Y 减 | 0x03，X 增/Y 增 |
| X 范围/初值 | 0→49 / 0 | 0→49 / 0 |
| Y 范围/初值 | 299→0 / 299 | 0→299 / 0 |
| 数据顺序 | 原数组顺序 | mirror_y 默认 false，原数组顺序 |
| 平面顺序 | 0x24 后 0x26 | 全刷写入 0x26 后 0x24 |

GxEPD2 原始 `epd2.writeImageForFullRefresh` 不经过 Adafruit_GFX 的 rotation；`setRotation(0)` 不能替该接口实施坐标转换。
在 H0 已冻结的物理坐标下，结合相同 MUX 配置，当前项目路径静态预期为 identity，而非 H0 的 `x_panel=x_bitmap; y_panel=299-y_bitmap`。
这是由代码及既有 H0 证据推导的预期，不是 GxEPD2 实物方向已验证。目标 Y MIRROR 与当前寻址不一致；本轮不叠加 flip、修改寄存器或改变目标。

## 构建证据

使用 `D:\Codex\eink-panel\.venv-hw\Scripts\python.exe -B -m platformio run`，工程目录为 `D:\Codex\eink-panel\hardware\gdey042t81_esp32`，分别指定 `-e esp32dev` 与 `-e esp32-m1`。
仅命令进程设置 `PLATFORMIO_CORE_DIR=D:\Codex\eink-panel\.venv-hw\pio-core`，没有更改持久环境、安装或升级包。
这是现有缓存的增量构建，不宣称 clean rebuild 或受保护分支之外的实机入口已验收。

工具：PlatformIO Core 6.1.19；Arduino framework 包 3.20017.241212+sha.dcc1105b（Arduino 2.0.17）；Xtensa GCC 8.4.0+2021r2-patch5；esptool 包 2.40900.250804（4.9.0）；GxEPD2 1.6.9+sha.de82887；GFX 1.12.6；SPI 2.0.0。

| 环境 / board | 构建 | RAM | Flash |
| --- | --- | --- | --- |
| esp32dev / esp32dev | exit 0 / SUCCESS | 36,696 / 327,680（11.2%） | 285,241 / 1,310,720（21.8%） |
| esp32-m1 / lolin32 | exit 0 / SUCCESS | 36,696 / 327,680（11.2%） | 285,241 / 1,310,720（21.8%） |

完整日志位于本地忽略目录 `D:\Codex\eink-panel\artifacts\step015a-preflight\`：`esp32dev-build.log`、`esp32-m1-build.log`。
产物根目录：`D:\Codex\eink-panel\hardware\gdey042t81_esp32\.pio\build\`；下表路径均相对此根目录。

| 产物 | 字节 | SHA-256 |
| --- | ---: | --- |
| esp32dev/firmware.bin | 285600 | 603DE0A11E8809F3697AC3E98516D04D406C13EBC996CB436114E518374E5574 |
| esp32dev/firmware.elf | 7004404 | B3C597AE5497494C86F5C91C091E89F844FF5CDC04246879457091A30C81E9E0 |
| esp32-m1/firmware.bin | 285600 | AF37EF2757A3D2FFE9356EED217C41EC0C7F44F25A1CFE726D2A745FDD4AC6D6 |
| esp32-m1/firmware.elf | 7004692 | 142FD73B618AEE85CB828B47744795B3442B1CA3953D9E7D07DA4E6E1F092FFE |

## 验证与后续边界

Python 3.12.14 项目环境：`python -B -m pytest -q`，125 passed in 1.21s，退出码 0。
七组 host C++ 测试仍 NOT RUN；当前 PATH 未发现 g++、clang++、cl，不安装编译器，不执行 pio test。

前后比较 91 个文件（全部已跟踪文件及 H0-safe src 文件）SHA-256 一致，包含项目源码、配置、业务/UI/测试及 H0-safe 源码和位图头文件。
文档本地链接、尾随空白和敏感信息模式检查通过，`git diff --check` 通过。日志及产物由已有忽略规则覆盖。
构建结束出现 Core 新版本提示，未执行升级。构建日志是本轮命令实际输出，不是硬件运行日志。

后续单独规划：在不绕过冷启动初始化的前提下消除隐含清屏刷新、建立可传播的超时中止行为，再设计同图单帧入口并核对方向。
这些是建议，不是本轮实现或硬件放行；私有配置仍需单独审查，禁止将构建成功作为解除保护依据。

本轮仅新增此审计文档；不暂存、提交、推送或打标签。原始证据不移动、不删除、不写入 Git。
