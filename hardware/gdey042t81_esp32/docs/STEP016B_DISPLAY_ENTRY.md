# STEP016B — ESP32 Display Entry

状态：INTERFACE FROZEN / IMPLEMENTATION NOT RUN / TESTS NOT RUN。
基线：`dbd7b8c2956513f74e623cb6321e0d59c4eb16a7`；不修改 [冻结 H1 适配器](../src/h1/atomic_display.h) 或 main/pattern/config。

## 输入

输入仅为 [Render 接口](STEP016B_RENDER_INTERFACE.md) 的构建时嵌入完整传输帧，不从网络、串口、SD 或文件系统获取。
调用适配器前必须具有有效、存活至刷新返回的 RAM 缓冲，长度15000、x=0、y=0、w=400、h=300；保持 invert=false、mirror_y=true、pgm=false。
若生成数组放在 Flash/PROGMEM，必须经已审查的加载方式复制到完整 RAM 缓冲；不得仅凭长度就把未经审查的 Flash 指针当作 pgm=false 输入。具体数组存储形式后续实现评审，本规范不添加头文件。

## 一次执行流程

```text
准备/检查完整 RAM 帧（仅 MCU 内存，无显示命令）
  → coldInit(initial=true)
  → selectFastFullUpdate(false)（已有 coldInit 内执行，不额外复制）
  → prepareColdStartFullFrame
  → previous RAM 0x26，随后 current RAM 0x24
  → refreshOnce / 原版 refresh(false)，普通 FULL 0x22=0xF7 → 0x20
  → 只读耗时/BUSY、记录软件结果
  → delay 停驻
```

正常路径一次启动仅一次标准 FULL；非法输入或准备拒绝时不进入刷新。参数拒绝不得改变初始写入责任；沿用现有适配器的约束，不使用 initial=false 伪装保电唤醒。
准备完整双 RAM 是源代码调用证明，不是 SPI ACK、硬件读回或掉电原子性。
refresh 返回后 EPD COMMAND COUNT=0，成功、超时或不明结果均相同；禁止 powerOff、hibernate、补写、clearScreen、重复 refresh 或重试。不得调用包含后续 EPD 操作的完整演示封装。
BUSY 仍 HIGH 或无符号计时差达到现有 10000000 微秒阈值，仅判 TIMEOUT_OR_UNKNOWN；否则也只称软件返回条件满足，不称物理显示 PASS。未观察运行日志时不得推断某个分支确实执行。
本设计不证明库内部所有阶段超时后立即停止命令；验收边界是最终 refresh 返回后零显示命令，BUSY 故障注入仍未执行。
停驻不是 Deep Sleep，也不证明控制器断电；重新启动可能再次 FULL，不是跨重启一生一次。

## 构建隔离

未来采用独立专用入口/环境，唯一业务输入为冻结 frame。复用 H1 适配器且保留其专用宏/私有配置约束，不改默认 esp32dev、esp32-m1 或已冻结 esp32-m1-h1 的入口。
必须验证正确屏类、固定工具链、GPIO、私有配置缺失/错误时失败、默认环境保护不变。不能静默回退，也不能因本文件而直接解除保护。
不引入网络取帧、JSON 解析、UI 生成、刷新策略轮询、Partial/Fast Refresh。当前不创建新环境、源码或配置。
冻结的是执行与输入契约，未来专用文件/环境命名由后续实现计划确定；本次无可执行上传指引。

## 验证边界

[H1 已有 limited-scope PASS](STEP015C_H1_PHYSICAL_AUDIT.md) 不自动等于新业务页验证通过。方向组合见 [布局](STEP016B_PAGE_LAYOUT.md)，所有新增测试见 [测试计划](STEP016B_TEST_PLAN.md)，状态均 NOT RUN。
