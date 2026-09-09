# Hardware Identification

STEP-013 / 2026-09-09。Status: COMPLETE / H0 PRE-FLIGHT GO（证据级）。
ESP32-M1、模组、屏幕营销型号、P4 档位及 FPC 外观证据已收口；电气与运行验证尚未开始。
证据、页码、照片标识与哈希见 [统一审查](STEP013_HARDWARE_AUDIT.md) 和
[证据清单](STEP013_EVIDENCE_MANIFEST.md)。

## Display

Model: GDEY042T81

Resolution: 400x300

Driver: SSD1683

Specification status: CONFIRMED BY SELLER EVIDENCE AND OFFICIAL SPEC CROSS-CHECK

Physical back label: 042BN-T81-D2（OBSERVED）

Marketing SKU confirmed: YES（卖家针对本次购买的规格图 + 官方资料交叉核对）

Physical model confirmed: YES for H0 identity gate；不声称背标与营销型号存在官方一一映射表

FPC: P5 24-pin / 0.5mm documented；未观察到额外触摸/前置光排线，变体未最终排除

FPC contacts: VISUAL CONDITION PASS；未见明显撕裂、严重折痕、分层或烧损

Physical Pin 1: UNKNOWN；厂商安装规则为显示面朝上、插好后压下黑色锁扣

Photos: 标签、屏幕/FPC正反面、接触端及P5已查看；FPC尚未插入P5

## Driver Board

Model: Good Display ESP32-M1（板载电子纸驱动电路）

Revision: UNKNOWN

Display compatibility: 官方目标为 24-pin SPI 屏；SSD1683 需要 RESE=2.2Ω，实物滑块视觉确认在2.2档

Photos: 正反面、P4 与 P5 局部均已查看；P5当前为空

Schematic / seller documentation: ESP32-M1-SCH-20260307.pdf 与 ESP32-M1 V1.0.pdf，见统一审查

## ESP32 Board

Model: Good Display ESP32-M1

Chip/module: ESP32-WROOM-32D（照片与原理图一致）

Revision: UNKNOWN

USB: Type-C DC5V + data；原理图 USB bridge 为 CH340C

GPIO: SCHEMATIC CONFIRMED，见下表

Photos: 正反面及 ESP32-WROOM-32D 标识已查看

PlatformIO board mapping: lolin32（官方说明书 WEMOS LOLIN32；本地平台已有定义）

历史 esp32dev 继续保留为 generic 示例。lolin32 参数不是实测容量、时钟或运行结果。

## Power

Logic Voltage: 3.3V

Confirmed: SCHEMATIC ONLY / NOT MEASURED

Driver board supply requirement: Type-C DC5V 输入；板载 U2 输出3.3V

Power source / available current: 未来 PC USB；实际能力 UNKNOWN（原理图稳压段标注500mA MAX）

Common ground: 原理图 P5 pin17=GND；实物未测量

Evidence: 原理图 POWER / E-PAPER DRIVER 分区；RESE ACTUAL=2.2Ω VISUAL，MATCH=YES，NOT MEASURED

3.3V 是目标约束，并非测量记录；不得用开发板 USB 输入电压代替屏幕接口电压判断。

## Wiring Evidence

Wiring state: 已查看整体照片中 USB/FPC 未连接；本步骤未操作硬件

Photos: 当前证据显示 USB/FPC 未连接；STEP-014 连接后的断电检查尚未执行

| Signal | Actual ESP32 GPIO | Driver board label | Confirmed |
| --- | --- | --- | --- |
| SCK | 18 | P5 pin13 | SCHEMATIC |
| MOSI | 23 | P5 pin14 | SCHEMATIC |
| CS | 27 | P5 pin12 | SCHEMATIC |
| DC | 14 | P5 pin11 | SCHEMATIC |
| RST | 12 | P5 pin10 | SCHEMATIC |
| BUSY | 13 | P5 pin9 | SCHEMATIC |

图纸网络已确认，物理安装未确认。本步骤不创建 display_config.local.h、不设置确认位为1。

## Review

Evidence supplied by: 用户照片与官方PDF

Reviewed by / date: Codex / 2026-09-09

Hardware identification: BOARD AND DISPLAY IDENTITY CONFIRMED / ELECTRICAL MEASUREMENT NOT RUN

COMPILE VERIFIED: YES — STEP-013 generic esp32dev 与 ESP32-M1/lolin32 受保护配置；非实物验收

REAL BOARD IDENTIFIED: YES（仅 ESP32-M1 / WROOM-32D）

HARDWARE VERIFIED: NO

H0 PRE-FLIGHT: GO（证据级；仅表示可另行规划STEP-014）

READY FOR STEP-014: YES

本卡本身不授权通电或烧录。STEP-013 已完成板级受保护配置编译；资料确认后，仍需验证最终私有配置和
[H0_CHECKLIST](H0_CHECKLIST.md) 的断电、电气和物理条件；当前不执行 STEP-014 或 H0/H1/H2/H3。
