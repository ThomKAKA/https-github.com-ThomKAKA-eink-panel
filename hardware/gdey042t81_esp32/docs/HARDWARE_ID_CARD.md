# Hardware Identification

STEP-010。Status: READY FOR HARDWARE IDENTIFICATION。
本卡尚未完成实物确认；目标规格不等于已识别出的实物型号。
未知项保留 UNKNOWN/TODO，不根据 esp32dev 或示例 GPIO 猜测填写。

## Display

Model: GDEY042T81

Resolution: 400x300

Driver: SSD1683

Specification status: TARGET / ASSUMPTION（作为实物身份尚未确认）

Physical model confirmed: NO

FPC: UNKNOWN

FPC contacts / insertion direction: UNKNOWN

Photos: TODO（屏幕标签、背面、排线与接口近照）

## Driver Board

Model: UNKNOWN

Revision: UNKNOWN

Display compatibility: UNKNOWN

Photos: TODO（正面、背面、接口标识）

Schematic / seller documentation: TODO

## ESP32 Board

Model: UNKNOWN

Chip: UNKNOWN

Revision: UNKNOWN

USB: UNKNOWN

GPIO: UNKNOWN

Photos: TODO（正面、背面、芯片或模组标识）

PlatformIO board mapping: UNKNOWN

ASSUMPTION: 当前 esp32dev 只是编译示例；不能填作实物 Model。

## Power

Logic Voltage: 3.3V

Confirmed: NO

Driver board supply requirement: UNKNOWN

Power source / available current: UNKNOWN

Common ground: UNKNOWN

Evidence: TODO

3.3V 是目标约束，并非测量记录；不得用开发板 USB 输入电压代替屏幕接口电压判断。

## Wiring Evidence

Wiring state: UNKNOWN（未接线时直接填写“未接线”）

Photos: TODO（仅提供已有接线的断电照片；不要为填卡而接线或通电）

| Signal | Actual ESP32 GPIO | Driver board label | Confirmed |
| --- | --- | --- | --- |
| SCK | UNKNOWN | UNKNOWN | NO |
| MOSI | UNKNOWN | UNKNOWN | NO |
| CS | UNKNOWN | UNKNOWN | NO |
| DC | UNKNOWN | UNKNOWN | NO |
| RST | UNKNOWN | UNKNOWN | NO |
| BUSY | UNKNOWN | UNKNOWN | NO |

ASSUMPTION: 既有示例引脚未经实物确认，不复制到本表或创建 display_config.local.h。

## Review

Evidence supplied by: TODO

Reviewed by / date: TODO

Hardware identification: INCOMPLETE

COMPILE VERIFIED: NO

HARDWARE VERIFIED: NO

H0: BLOCKED BY HARDWARE IDENTIFICATION

本卡本身不授权安装、编译、通电或烧录。资料确认后，仍需完成独立工具链/编译验证和
[H0_CHECKLIST](H0_CHECKLIST.md) 的前置条件；当前不进入 H0/H1/H2/H3。
