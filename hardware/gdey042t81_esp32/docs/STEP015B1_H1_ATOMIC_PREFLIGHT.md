# STEP-015B1 — H1 cold-start atomic full-frame preparation

实施：2026-09-10；最终复核：2026-09-11。
基线 HEAD：`f24d0c0e3ffdf178fb05fe226e71406dd7461b30`。

## 结论和范围

`H1 PHYSICAL TEST PRE-FLIGHT = GO — compile/static preflight only`。
H0 PASS 保持原范围；`PROJECT GXEPD2 PHYSICALLY VERIFIED=NO`，`UPLOAD=NOT RUN`。
这不是实机安全认证，也不是屏幕成功刷新或休眠的证明。
[STEP-015A](STEP015A_H1_PREFLIGHT.md) 保留默认路径 NO-GO 的历史结论；默认路径本轮不修复、不解锁。

新增专用 `esp32-m1-h1` 环境；仅编译 [H1 main](../src/h1/main.cpp)，不编译原 main、display_driver、refresh_policy。
既有业务/API/UI/帧协议不变。不提交、不推送、不打标签；原始证据及 A 报告保持原有未跟踪状态。

## 适配器与冷启动责任

[H1SafeGDEY042T81](../src/h1/atomic_display.h) 私有继承准确屏类，禁止复制/移动，不向调用方暴露原版宽泛显示 API。
只提供 coldInit、prepareColdStartFullFrame、refreshOnce；不复制驱动或寄存器序列，不修改第三方库。
固定来源：GxEPD2 `de82887e77a78528ea386e68bba2cb0291d2c319`，1.6.9。

`coldInit` 使用 `initial=true`，复位时间 10 ms，SPI 4 MHz / MSB-first / MODE0，显式 `selectFastFullUpdate(false)`。
`_initial_refresh` 不由适配器赋值，最终原版 FULL 自行更新此状态。

准备前核对 state、非空指针、15,000 字节、x/y=0、w/h=400/300，以及 `_initial_write`、`_initial_refresh`。
非法输入、未初始化、重复准备或刷新后调用均在任何状态/显示命令修改前拒绝。
调用方仍须保证指针实际指向完整有效缓冲；长度参数不能证明任意指针的分配大小。实际入口使用固定 std::array。

合法请求在同一受控调用中进入 Preparing、设置 `_initial_write=false`，立即调用原版 `writeImageForFullRefresh`。
这是 H1 接管冷启动整帧 RAM 初始化责任，不是伪装保电唤醒或先前已刷新。
原版 `_writeImage` 对这组参数计算 wb=50、x1/y1=0、w1=400、h1=300；不会命中裁剪提前返回。
`_InitDisplay` 没有刷新激活；随后 0x26 和 0x24 各写 300×50 字节，跳过原版自动清屏路径。
两平面软件调用之间没有应用分支；Prepared 只在调用完成后设置。

“原子”限单一软件调用链，不保证掉电、看门狗、异常复位、并发线程或硬件 SPI 故障的事务原子性。
该入口单线程一次执行，无其他任务操作显示。RAM 完整写入结论为源码证明，不是硬件读回或 ACK。

## 单次 FULL、方向和停驻

| 静态验收项 | 结果 |
| --- | --- |
| cold init | initial=true |
| init 物理刷新激活 | 0 |
| RAM prepare 物理刷新激活 | 0 |
| 0x26 / 0x24 软件写入 | 各完整 15,000 字节 |
| 最终普通 FULL | 1，0x22=0xF7 后 0x20 |
| fast FULL | 禁用，无 0xD7 路径执行 |
| Y flip | mirror_y=true，一次 |
| refresh 返回后的 EPD 命令 | 0，所有结果相同 |
| partial / 网络 / 循环刷新 | 专用入口无此执行路径 |

`refreshOnce` 在调用原版前将状态设为 Finished；重复刷新/准备/初始化均被拒绝。
GDEY042T81 `_Update_Full` 的 BUSY wait 后只有内部状态更新，无 EPD 命令。
项目随后只读 micros/BUSY、输出日志、delay 停驻，无 writeImageAgain、powerOff、hibernate 或重试。
无论成功返回、超时或未知，都不声称 MCU/屏幕已休眠；重新启动会重新执行，并非跨复位永久一次。

上游 `_busy_timeout=10000000` 微秒，适配器初始化时核对值。
unsigned 时间差处理单次计时回绕；elapsed>=阈值或 BUSY HIGH 判为 `H1_FULL_TIMEOUT_OR_UNKNOWN`。
否则仅输出 `H1_SOFTWARE_RETURN_CONDITIONS_MET_NOT_DISPLAY_PASS`。
这是保守软件后置条件，可能将调度延迟算为异常，不能证明物理显示或精确识别所有上游超时。
停驻结构不依赖此判定是否精确：返回后均无显示命令。

[pattern.h](../src/h1/pattern.h) 复现 H0 白底、4 像素外框、十字、中心黑块、左上实心块、右上空心框。
无图形库、手工逆序或 rotation。原帧 row-major / MSB-first / 0 黑 1 白，原版写入边界唯一 mirror_y=true。
结合 GxEPD2 Y 递增寻址及既有 H0 物理坐标，静态预期 `x_panel=x_bitmap; y_panel=299-y_bitmap`，仍待该固件实物确认。
原始帧 SHA-256：`6A7A2758F0A7B6526BB9C2F6E2CD0AED4C102852B3BE68127910F4C151777581`。
交叉编译生成对象中的完整 15,000 字节与 H0 位图逐字节一致，不只是几何抽样。

## 私有配置隔离

只有专用环境添加 `.build/h1-private` 搜索路径。私有 `display_config.local.h` 不含凭据，现有忽略规则覆盖。
GPIO 与 [STEP013 审计](STEP013_HARDWARE_AUDIT.md)、H0-safe main、既有 ESP32-M1 头文件三方一致：
BUSY=13、RST=12、DC=14、CS=27、SCK=18、MOSI=23。
[config.h](../src/h1/config.h) 检查专用宏、ESP32-M1、Arduino LOLIN32、私有确认位和精确 GPIO。
缺失配置编译失败；错误 GPIO 编译失败；没有回退。
默认 esp32dev / esp32-m1 的 kWiringConfirmed=false 已分别用编译期断言核验。
默认环境编译新 main 为宏关闭的空翻译单元，不改变入口或引入私有配置。

## 构建、产物与测试

PlatformIO Core 6.1.19；espressif32 6.12.0；Arduino framework 3.20017.241212+sha.dcc1105b（2.0.17）；
Xtensa GCC 8.4.0+2021r2-patch5；GxEPD2 1.6.9+sha.de82887；GFX 1.12.6；BusIO 1.17.4；SPI 2.0.0。
新环境复制/解析同一版本依赖，无工具升级；新环境 GxEPD2 src 与原环境逐文件哈希一致。

工程：`D:\Codex\eink-panel\hardware\gdey042t81_esp32`。
工具：`D:\Codex\eink-panel\.venv-hw\Scripts\python.exe -B -m platformio run`。
进程级 Core：`D:\Codex\eink-panel\.venv-hw\pio-core`。
三环境最终联合构建退出码 0；日志：`D:\Codex\eink-panel\artifacts\step015b1\closure-builds.log`。
较早完整编译日志 `final-builds.log`、`h1-build.log`、`default-builds.log` 也保留。未访问 COM。

| env / board | RAM bytes | Flash bytes | 结果 |
| --- | ---: | ---: | --- |
| esp32dev / esp32dev | 36696 (11.2%) | 285241 (21.8%) | PASS |
| esp32-m1 / lolin32 | 36696 (11.2%) | 285241 (21.8%) | PASS |
| esp32-m1-h1 / lolin32 | 21616 (6.6%) | 294689 (22.5%) | PASS |

以下产物相对 `D:\Codex\eink-panel\hardware\gdey042t81_esp32\.pio\build\`，均忽略：

| 产物 | 字节 | SHA-256 |
| --- | ---: | --- |
| esp32dev/firmware.bin | 285600 | 603DE0A11E8809F3697AC3E98516D04D406C13EBC996CB436114E518374E5574 |
| esp32dev/firmware.elf | 7004404 | B3C597AE5497494C86F5C91C091E89F844FF5CDC04246879457091A30C81E9E0 |
| esp32-m1/firmware.bin | 285600 | AF37EF2757A3D2FFE9356EED217C41EC0C7F44F25A1CFE726D2A745FDD4AC6D6 |
| esp32-m1/firmware.elf | 7004692 | 142FD73B618AEE85CB828B47744795B3442B1CA3953D9E7D07DA4E6E1F092FFE |
| esp32-m1-h1/firmware.bin | 295056 | 4651616D92E03009B69EB260DE11BCD548D4504504EE6931BDBBCAFE7E2F8ED1 |
| esp32-m1-h1/firmware.elf | 6735708 | 3CF68337EF9173615427F44B323CF1AAC8367EFAAFEFF5AB7D75F805CBB4FECD |

[contract.h](../src/h1/contract.h) 编译期断言覆盖 null、短/长缓冲、错误几何、未初始化、重复准备/刷新拒绝、固定翻转参数、超时边界和计时回绕。
这验证 constexpr 条件，不冒充真实 SPI/运行状态机测试。
缺失配置/错误 GPIO 的负向编译退出码均 1（预期）；正确配置为 0。首个正确配置测试命令的 PowerShell 参数解析有误，改为显式绝对 include 参数后通过；未修改配置绕过。
主机 C++ 编译器当前 PATH 未发现；七组既有主机测试及新适配器主机运行测试 BLOCKED / NOT RUN，未安装编译器。
Python 3.12 项目回归：125 passed in 1.61s（最终复核），退出码 0。

477 个既有文件初次前后 SHA-256 比较中，仅获准修改的 platformio.ini 不同；包含 H0-safe 原源码/位图/产物及原 GxEPD2 src，无修改。
默认两环境最终 BIN/ELF 与 STEP-015A 哈希相同。新增文件另行检查链接、空白、敏感信息和忽略规则。

## 未来上传命令：仅展示，当前禁止执行

此命令可能重新构建；只有另行确认实机步骤后才使用。本轮未执行。

```powershell
$env:PLATFORMIO_CORE_DIR = 'D:\Codex\eink-panel\.venv-hw\pio-core'
& 'D:\Codex\eink-panel\.venv-hw\Scripts\python.exe' `
  -B -m platformio run `
  --project-dir 'D:\Codex\eink-panel\hardware\gdey042t81_esp32' `
  -e esp32-m1-h1 -t upload --upload-port COM11
```

本轮结束即停止，不自动进入实机 H1、局刷、快刷或联网验收。
