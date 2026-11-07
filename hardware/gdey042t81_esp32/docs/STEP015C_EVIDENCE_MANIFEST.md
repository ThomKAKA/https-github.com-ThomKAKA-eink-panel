# STEP-015C — H1 evidence manifest

核对日期：2026-09-11。结论与限制见 [H1 实机审计](STEP015C_H1_PHYSICAL_AUDIT.md)。
目标：ESP32-M1 / GDEY042T81 / SSD1683 / 400×300 黑白；专用环境 `esp32-m1-h1`，用户报告设备 USB-SERIAL CH340、端口 COM11。
本地目录：`D:\Codex\eink-panel\hardware\evidence\STEP015_H1`。下列原始文件与本地清单仅本地保留，不进入 Git。

| 文件名 | 字节 | SHA-256 |
| --- | ---: | --- |
| STEP015C_before_upload.jpg | 757955 | 7268EFD7A1D8C78B0C0CADFC296A9E81F9452D900408E6FD841699BEBC6D178B |
| STEP015C_upload_COM11.txt | 314 | 6DFDC506F1A693820C6C657C079B8830D4BC0723CEE383680006ABF446A016E2 |
| STEP015C_after_display.jpg | 592428 | FDA5A96CFD608E81729AA6832DB1254081F563256ABA2893957BEBA7E0C09285 |
| STEP015C_DISPLAY_OBSERVATION.md | 357 | B81B80243B06D300859B4A4E5B5046F54DA0E58332552EE6BAB64BE5813C3A46 |

## 来源与观察

- before：用户提供的上传前照片；已有外框、十字、中央黑块及左右角标，不能当成上传后新画面的证明。
- upload：用户整理保存的成功上传摘要及人工 SOURCE / DEVICE 说明；含 H1 环境、COM11、目标 BIN、写入完成、哈希校验、自动复位与 SUCCESS。不是完整原始 transcript，不包含固件文件 SHA-256 或完整分区清单。
- after：用户提供的上传后照片；按 FPC/L/R 规范化后几何与 before 及 H1 预期相符。照片不能单独证明新刷新发生、次数或稳定时长。
- observation：用户观察记录，描述自动复位后图案稳定、无连续闪烁或异常循环、无烟雾/热异常。无记录时长，无仪器测量。

本地 `H1 evidence manifest.txt` 的三个名称/哈希映射已逐项核对正确，保留原内容；本版本控制清单补充来源、大小、观察记录及证据边界。
现用日志为 314 字节版本，不沿用旧 390 字节版本哈希或曾写在正文中的自引用旧哈希。哈希仅用于固定当前文件字节，不证明内容来源真实性。

`UPLOAD = PASS (user-preserved summary)`；`DISPLAY OBSERVATION = PASS (limited scope, user report plus photo content)`。
`H1 PHYSICAL TEST = PASS (limited scope)`：单次标准 FULL 结论依赖用户实验报告与 B1 静态执行结构，不把静态照片视为刷新次数计数器。
BUSY timeout fault injection、Deep Sleep、Partial/Fast Refresh、长时间稳定性均 NOT TESTED；PRODUCT FUNCTION VERIFIED = NO。
