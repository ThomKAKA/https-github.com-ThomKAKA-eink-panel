# STEP016D — Display Flow

状态：DESIGN FROZEN；新入口实现、编译及实机验证均 NOT RUN。
基线：`45ca1dcc0e9043639299621229a223c7f0eca7de`。
承接 [B Display Entry](STEP016B_DISPLAY_ENTRY.md)，复用 [H1适配器](../src/h1/atomic_display.h) 和 [固定契约](../src/h1/contract.h)，不修改它们。

## 输入与执行顺序

输入为 [嵌入决策](STEP016D_FRAME_EMBED_DECISION.md) 中已校验的完整帧，不是PNG文件。

```text
检查嵌入帧长度、加载完整静态RAM缓冲（仅MCU内存）
  → SPI初始化
  → coldInit：initial=true，内部selectFastFullUpdate(false)
  → prepareColdStartFullFrame：15000字节，x=0,y=0,w=400,h=300
  → 原版writeImageForFullRefresh：previous RAM 0x26，随后current RAM 0x24
  → refreshOnce：原版refresh(false)，标准FULL，0x22=0xF7 → 0x20
  → 只读耗时/BUSY并记录软件结果
  → MCU delay停驻
```

保持 `invert=false, mirror_y=true, pgm=false`。不绕过适配器直接调用宽泛的writeImage/display封装，不用initial=false规避冷启动准备。
正常路径一次启动仅一次标准FULL；参数或准备拒绝时不刷新。双RAM完整准备是源码性质，不是控制器读回、SPI确认或掉电原子性。
适配器coldInit已禁用fast-full，调用方不复制寄存器初始化序列。方向责任见 [Orientation Rule](STEP016D_ORIENTATION_RULE.md)。

## 失败与停止

最终refresh返回后，无论成功、超时或结果不明，EPD COMMAND COUNT=0。
禁止writeImageAgain、writeScreenBuffer、clearScreen、再refresh、powerOff、hibernate、重试或任何partial/fast命令。
使用无符号回绕安全时间差；BUSY为HIGH或耗时达到10000000微秒，标记TIMEOUT_OR_UNKNOWN；其余仅标记软件返回条件满足，不能叫显示实测PASS。
该边界不证明库内部所有前置等待超时后立即禁止命令；BUSY故障注入仍未验证。
停驻不是Deep Sleep，也不证明控制器已断电；重新启动可能再次FULL，不是跨重启永久一次。

## 专用入口隔离与非目标

未来创建独立专用入口/环境，只纳入新入口而不同时编译演示main或冻结H1 main。
复用H1适配器及其宏/私有配置约束；不改变默认esp32dev、esp32-m1及冻结esp32-m1-h1的入口、GPIO保护或依赖版本。
私有配置与完整帧缺失/不匹配必须失败，不静默回退。具体新增环境和源文件在后续实现计划中确定，本轮不创建。
不设计JSON解析、字体/UI生成、网络取帧、HTTP、WiFi、刷新循环、Partial/Fast Refresh或Deep Sleep。

H0 PASS和H1 limited-scope PASS不自动覆盖本业务页入口。未来放行依据 [测试计划](STEP016D_DISPLAY_TEST_PLAN.md)，本文件不是上传授权。
