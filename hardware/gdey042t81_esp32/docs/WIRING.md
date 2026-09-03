# 接线：先确认实物，再确认 GPIO

当前 ESP32 开发板与转接板型号未最终核实。下表只给逻辑信号和示例 GPIO，不是卖家实物接线保证。
先断开 USB/外部电源再接线或插拔 FPC；裸屏必须通过兼容的驱动/转接电路连接，不能把 FPC
直接随意接到 ESP32 GPIO。

## 电源与信号

GDEY042T81 是 3.3V SPI 屏。[厂商参数](https://www.good-display.com/product/386.html)
与 [GxEPD2 驱动说明](https://github.com/ZinggJM/GxEPD2/blob/de82887e77a78528ea386e68bba2cb0291d2c319/src/gdey/GxEPD2_420_GDEY042T81.h)
均支持 3.3V 基线；驱动说明特别要求电源和数据线均为 3.3V。
没有转接板原理图与型号确认时，**不要给屏幕或逻辑信号接 5V**。
ESP32 开发板 USB 输入如何供电，与屏幕接口电压是不同问题。

| 转接板逻辑标识 | 作用 | 配置名 | 通用 ESP32 示例，EXAMPLE ONLY |
| --- | --- | --- | --- |
| GND | 公共地 | — | GND |
| 3.3V | 屏幕驱动电路供电 | — | 3.3V；先确认板卡要求与供电能力 |
| SCL / SCK / CLK | SPI 时钟，不是 I²C SCL | `EPD_SCK` | 18 |
| SDI / MOSI / DIN | ESP32 → 显示的数据 | `EPD_MOSI` | 23 |
| RES / RST | 显示复位 | `EPD_RST` | 16 |
| D/C / DC | 数据/命令选择 | `EPD_DC` | 17 |
| CS | 片选 | `EPD_CS` | 5 |
| BUSY | 显示 → ESP32 忙信号 | `EPD_BUSY` | 4 |

不需要 MISO。示例控制引脚参考 [GxEPD2 ESP32 示例](https://github.com/ZinggJM/GxEPD2/blob/de82887e77a78528ea386e68bba2cb0291d2c319/examples/GxEPD2_Example/GxEPD2_display_selection_new_style.h)，
仅适用于核对后匹配的开发板；不同板可能占用相关引脚用于 Flash、PSRAM 或启动配置。
这不是裸屏 24-pin FPC 的针脚编号表。

## 通电前逐项确认

1. 屏幕标签确实写 GDEY042T81，而非外形相似的其他 4.2 英寸屏。
2. 驱动板明确支持该屏；确认板卡版本、FPC 触点朝向与锁扣方式，不凭照片猜测正反。
3. 24-pin、0.5 mm 间距与接口匹配，排线平直插到底并锁好，没有折损或偏一针。
4. 供电/地线极性正确，无短路；转接板逻辑与供电符合 3.3V 要求。
5. 按实际 ESP32 板原理图核对每根线；SCK/MOSI 是 SPI，BUSY 是输入。
6. 将确认后的 GPIO 填入本地私有配置；仅此时设置 `EPD_WIRING_CONFIRMED=1`。

不确定任何一项就停在该项，先提供屏幕/开发板/驱动板的清晰型号与接线照片，不要试探性接 5V。
