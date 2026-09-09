# STEP-013 ESP32-M1 证据与编译审查

日期：2026-09-09。起点：main / `ef2ef60bad59dcf734abc422ed00975949bc2113`。
STEP-012 保持 COMPLETE，仅 example esp32dev profile 编译已验证。
本记录依据用户提供的实物照片及三份官方 PDF。PDF 中的接线、下载程序等说明是资料，
不是本步骤操作授权。实物通电、插拔 FPC、拨动开关、烧录及串口均未执行。

## 1. 文件与来源冻结

三份 PDF 保留在用户原始目录 `D:\照片`，不复制至项目。页码均为 PDF 物理页码。

| 文件 | 页数 | SHA-256 |
| --- | ---: | --- |
| ESP32-M1 V1.0.pdf | 10 | `60595f7d9aefdcd5d7257354476d9236eb83f4ff61e9d48e68d898ea0c217b7e` |
| ESP32-M1-SCH-20260307.pdf | 1 | `06baa8124052e4762e1d2bf6642f4371e2bdc620da246b8f4c704e418fd9f4bf` |
| catalog-cn.pdf | 12 | `7586e5f07ff8415e956084fdfad533c601ad42c14a6a71a2e32949d71f375c7b` |

- [开发板官方页面](https://www.good-display.cn/product/736.html)。说明书第 2 页版本 V1.0，日期 2026/05/06。
- 原理图文件名含 20260307，但图框日期为 2026/5/13；记录二者，不把文件名当实物修订号。
- 说明书第 5 页图 1 / 条目 ②：Type-C 数据及 DC5V 输入；⑤为主电源开关，⑭为电子纸匹配电阻开关。
- 第 6 页 §3.1：P4 UC=0.47Ω、SSD/四色=2.2Ω；§3.2：P5、24-pin、显示面朝上、压下黑色锁扣。
- 第 7 页：P8/SS1/P9 为前置光部分，不能混同 P4/P5；前置光口不可插入触摸屏。
- 第 9 页图 12：Arduino 选择 WEMOS LOLIN32；截图示例 COM7 不作为用户端口。
- 说明书展示 IDE 2.3.3、ESP32 Core 3.1.1；本项目平台继续固定 6.12.0 / Arduino 2.0.17，非同一验证环境。
- 目录第 4 页：GDEY042T81 4.2 英寸、400×300；第 8 页另列触摸版本，第 11 页展示的是 ESP32-L，不用它识别 ESP32-M1。

## 2. KEEP / CHANGE / UNKNOWN

KEEP：P5 24-pin 安装规则、P4 的电阻规则、Type-C DC5V 输入、既有 GxEPD2 路线及所有实机禁令。
CHANGE：六个 GPIO 已由原理图确认；采用现有 `lolin32` board 定义；官方样例只称 VENDOR REFERENCE COMPILE。
UNKNOWN：实物 RESE 档位、接触面/Pin 1 标记/锁扣状态、屏幕营销 SKU 一一对应及变体、所有运行结果。

实物证据来自本任务参考对话 `6a95751d-1fe8-83ea-bbbd-a6909252dbbc` 已查看照片：

- `1847B84769C4F0738B856831308D9591.jpg`：ESP32-M1 布局及 ESP32-WROOM-32D 标识。
- `B0E4ED40D3F17D1AEA1E1CD2FBFFAFF9.jpg`：开发板背面 Good Display 标识。
- `8155A2DE0A1A25D9C0ACAC68F23F01A0.jpg` / `427A84CB6FEEB5A6326C1554E6A806A9.jpg`：背标 `042BN-T81-D2`。
- 整体照片显示 USB/FPC 未连接；不推断照片拍摄后用户操作。未观察到额外 Touch/Front Light FPC，不等于排除全部变体。
- NodeMCU 为 BACKUP ONLY / INACTIVE；UT123D 包装照片不能证明仪表已测量验收。

REAL BOARD IDENTIFIED=YES 只指 ESP32-M1 与 WROOM-32D；实物板修订号 UNKNOWN。
DISPLAY SKU CORRELATION=STRONG / PROVISIONAL；MARKETING SKU CONFIRMED=NO。
目标型号的 SSD1683/3.3V/0.5mm 规格依据此前[官方屏幕页面](https://www.good-display.com/product/386.html)，
不声称目录或背标证明了控制器型号。屏幕专用 datasheet/SSD1683 datasheet 不在本次三份文件内。

## 3. 原理图电气证据

原理图唯一页 MCU / E-PAPER DRIVER 分区的网络连接，与官方样例相互吻合：

| 信号 | GPIO | P5 pin | 状态 |
| --- | ---: | ---: | --- |
| BUSY | 13 | 9 | SCHEMATIC CONFIRMED |
| RES / RST | 12 | 10 | SCHEMATIC CONFIRMED |
| D/C | 14 | 11 | SCHEMATIC CONFIRMED |
| CS | 27 | 12 | SCHEMATIC CONFIRMED |
| SCLK | 18 | 13 | SCHEMATIC CONFIRMED |
| MOSI / SDI | 23 | 14 | SCHEMATIC CONFIRMED |

P5 电气引脚（不是从照片判断的左右方向）：

| pin | 网络/功能 | pin | 网络/功能 |
| ---: | --- | ---: | --- |
| 1 | NC | 13 | SCLK |
| 2 | GDR | 14 | SDI / MOSI |
| 3 | RESE | 15 | VDDIO / 3.3V |
| 4 | VGL | 16 | VCI / 3.3V |
| 5 | VGH | 17 | VSS / GND |
| 6 | TSCL | 18 | VDD |
| 7 | TSDA | 19 | VPP |
| 8 | BS / GND | 20 | VSH |
| 9 | BUSY | 21 | PREVGH |
| 10 | RES | 22 | VSL |
| 11 | D/C | 23 | PREVGL |
| 12 | CS | 24 | VCOM |

连接器为 FPC24(0.5MM)。电气 Pin 1=NC 已知，实物端 Pin 1/触点/锁扣状态仍 UNKNOWN。
U2 RT9193-33GB 提供 3.3V；图中标注 500mA MAX，不代表经实测的可用负载余量。
U2 EN 接输入电源路径，未发现独立 MCU 控制的 EPD_POWER_EN。
GDR/Q2/L1/RESE 是电子纸升压与反馈电路，不新增 GPIO 去控制它们。
GPIO22 / FL_EN 属前置光路径，不能拿来当电子纸电源使能。P5 高压驱动网络不等于 3.3V 逻辑线。
首次未来路径为 PC USB → Type-C → 主开关/稳压/板载电子纸电路 → P5；本次未通电、未测电压。
RESE REQUIRED=2.2Ω（目标 SSD1683）；CURRENT=UNKNOWN；MATCH=UNKNOWN。

## 4. 构建策略与参考样例

用户选定独立板级头文件。保留 generic esp32dev 默认环境和原示例 GPIO；
新增 esp32-m1 环境使用平台现有 `lolin32` 定义，不创建 custom board JSON。
本地平台两种 board 都声明 ESP32 / 240MHz / 4MB / DIO / Flash 40MHz，但 variant 不同。
这些是构建参数，不是实测 Flash、时钟或容量。
配置选择为 local → EINK_BOARD_ESP32_M1 板级头文件 → generic example；
`EINK_HAS_LOCAL_CONFIG && EPD_WIRING_CONFIRMED == 1` 保持为唯一放行条件。
本次不创建 local，受跟踪配置确认位均为 0。未运行固件验证保护效果。

厂商参考：[ESP32epdx 固定提交](https://github.com/gooddisplayshare/ESP32epdx/tree/d5ed3b777bedb9b407ccff09dc810a9248eb7926)。
样例路径：`examples/2-Colors (BW)/4.2/GDEY042T81/`。
先前核对 LICENSE 内容为空，授权条款 UNKNOWN；源码只留忽略的临时构建目录。
官方样例默认含快刷、四灰阶和局刷，并非最小 H0 程序；BUSY 等待无超时。
`EPD_DeepSleep()` 向屏控制器发送休眠命令，不表示 ESP32 深度睡眠或板级断电。
样例编译 PASS 不能区分或排除实物故障；产品继续固定 GxEPD2，不移植厂商驱动。

## 5. 编译与回归结果

文档基线阶段：VENDOR REFERENCE COMPILE=NOT RUN；PROJECT ESP32-M1 COMPILE=NOT RUN。
本步骤构建结果将在实际完成后追加；STEP-012 历史 generic PASS 不充当本次重测。
7 组 host C++ tests=BLOCKED / NOT RUN，不新增 native 环境、不安装主机编译器。

## 6. H0 Gate

STEP-013=IN PROGRESS / PHYSICAL EVIDENCE RECEIVED。
PHYSICAL ESP32-M1 IDENTIFIED=YES；ESP32 MODULE IDENTIFIED=YES；GPIO SCHEMATIC CONFIRMED=YES。
DISPLAY SKU CORRELATION=STRONG / PROVISIONAL；RESE CURRENT=UNKNOWN。
ELECTRICAL CONFIGURATION FROZEN=NO（板级图纸明确，实物预检未完成）。
HARDWARE VERIFIED=NO；DISPLAY VERIFIED=NO；H0 PHYSICAL TEST=NOT RUN；H0 PRE-FLIGHT=NO-GO。

下一步材料：断电的 P4/RESE 近照、P5 与屏幕 FPC 正反面近照、标明 GDEY042T81 的订单或卖家确认。
本步骤不自动开始 STEP-014，不要求为了照片而接线或拨动开关。唯一清单见 [H0_CHECKLIST](H0_CHECKLIST.md)。
