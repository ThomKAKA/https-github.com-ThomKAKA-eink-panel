# H0 → H1 实机验证

本说明是待执行流程，不是成功记录。每一步只改变一个变量。当前没有完成烧录或物理屏验证。
STEP-013 只获准证据与编译，H0 PRE-FLIGHT=NO-GO。当前主路线为 ESP32-M1 与目标GDEY042T81，
备用NodeMCU不参与。证据见 [STEP013_HARDWARE_AUDIT](STEP013_HARDWARE_AUDIT.md)。
当前保留保护膜，不拉扯或反复弯折FPC，不按压屏幕中央；不得为补资料连接硬件。
官方样例默认含快刷/灰度/局刷、BUSY等待无超时；其EPD_DeepSleep只休眠屏控制器，不能当作ESP32深睡。
该样例仅作隔离编译参考，未获准直接烧录作首次H0测试。
首次验证建议在室温进行；厂商的刷新时间以 25°C 为条件，不把它当作当前设备性能承诺。

## 1. 只连接显示链

只准备 ESP32、兼容驱动/转接板、GDEY042T81、连线与 USB 数据线。
不要启动 Wi-Fi、服务器、事件生产脚本或其他外设。先按 [WIRING](WIRING.md) 核对。

## 2. 断电检查并配置

核对 FPC 方向、锁扣、3.3V、公用 GND 和每个 SPI 信号。
ESP32-M1 的六个信号按原理图核对，底层目标按说明书使用 `lolin32`。P4目标2.2Ω，当前档位待近照确认。

在 `D:\Codex\eink-panel\hardware\gdey042t81_esp32` 中，将
将来获准实机配置时，从已核对的板级配置准备 `include/display_config.local.h`（STEP-013 不创建）。
只在实物电气核对通过后修改本地文件，将 `EPD_WIRING_CONFIRMED` 改为 `1`。
保持 `EPD_BRINGUP_STAGE=0`、`EPD_RUN_REFRESH_DEMO=0`，Wi-Fi 字段保持空白。

本地配置已被 Git 忽略，不需要提交；不要用 `git add -f` 强行加入。

## 3. 编译，再烧录最小固件

STEP-008 交付时未安装 PlatformIO；STEP-012 已在隔离环境完成无私有配置的 esp32dev 示例编译，
不表示以下实机流程获准执行。工具目录、绝对路径命令和日志要求见 [BUILD_GUIDE](BUILD_GUIDE.md)。
以后实物身份和配置确认、获得单独批准后，才在硬件目录重新构建对应配置：

```powershell
pio run -e esp32dev
```

编译成功只证明该配置通过工具链，不能证明接线或屏幕能工作。首次构建可能下载平台/依赖，
需要网络、空间和时间；不执行自动安装脚本。设计上无私有配置也允许编译，但运行时被保护逻辑阻止驱动显示；
STEP-012 仅验证了这一无私有配置的示例构建路径，真实板型配置仍需重新构建，运行保护与显示均未实测。

确认只连接目标板、串口无歧义、实物接线已核对后，才手动执行：

```powershell
pio run -e esp32dev -t upload
```

如果存在多个串口，先在设备管理器确定目标，再指定正确的 `--upload-port`，不要猜端口。
本次交付没有运行任何 upload 命令。

## 4. 查看 Serial

```powershell
pio device monitor -b 115200
```

必要时手动按一次复位看启动日志。预期看到 `Source=LOCAL_TEST_FRAME`、
`FrameFetcher=DISABLED`、`Wi-Fi=OFF`。`CONFIG_UNCONFIRMED` 表示保护在正常生效，
请返回第 2 步，不要删掉保护代码。

`SUBMITTED_NOT_VISUALLY_VERIFIED` 不是屏幕成功证据。
若出现 `Busy Timeout!`、`BUSY_ACTIVE_CHECK_WIRING`、异常复位，立即停止反复刷新并排查。

## 5. 检查 H0 图案

应看到 `E-INK TEST`、`400x300`、`GDEY042T81`，以及一个实心矩形、一个空心矩形、一条横线、外框。
确认整体没有镜像/倒置/缺边，白底黑字清楚，画面保持、不循环闪烁。
拍一张屏幕照片，保存板型、引脚表、库版本与 Serial 记录。只有此时才能把 H0 标为 HARDWARE VERIFIED。

## 6. H1 与完整全刷

H0 通过后，仅把本地配置 `EPD_BRINGUP_STAGE` 改为 `1`，重新编译/烧录。
默认显示 raw Frame A 一次，首次使用普通 FULL，再保持。
按 [assets 说明](../assets/README.md) 检查四边、非对称角标、单像素边界与黑白极性。
400×300 模拟器坐标与实物 1:1 的结论必须等此步实测，不由“数组长度正确”替代。

## 7. 局刷（手动启用有限演示）

H1 单帧正常后，仅把 `EPD_RUN_REFRESH_DEMO` 改为 `1`，保持
`EPD_PREFER_FAST_FULL=0`、`EPD_MAX_FAST_UPDATES=5`、`EPD_MIN_REFRESH_INTERVAL_MS=5000`。
重新编译/烧录。它只交替显示 A/B 的中央标记，不是循环动画；每次驱动完成后至少等 5 秒。

## 8. 确认 5 次局刷后的全刷

预期日志顺序为 `FULL → PARTIAL × 5 → FULL → DEMO FINISHED`，然后停止。
全刷后 `fast_count=0`；不仅看日志，还要观察波形表现与残影是否可接受。
这个全刷显式关闭快速全刷波形。不要为追求理论 0.3 秒而缩短成动画刷新。
默认策略是参数起点，实际残影、温度和屏幕批次仍需要人工验证。
完成后把 `EPD_RUN_REFRESH_DEMO` 恢复为 `0`，防止以后每次启动重新跑演示。

## 9. 停止并记录结果

记录 H0/H1、局刷和清残影各项是否通过，附照片及 Serial。
只有以上全部正常，才讨论并另行批准 H2 Wi-Fi/HTTP 拉帧。
P1.5 不提供服务器帧端点，也不把事件推送直接连到 ESP32。
