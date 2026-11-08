# BUSY 引脚故障注入测试规格与判据

Date: 2026-11-08 (Asia/Shanghai)
Status: 规格草案；未执行，未改固件。
Base: `f9373c7`（R6 验收记录与清理说明已入库）。
Related: `PROJECT_STATE.md` §37、`docs/ROUND2_PRODUCT_PLAN.md`、`h1/contract.h`、
`h1/atomic_display.h`、`network_progress/main.cpp`。

## 1. 目的

用可控的电气/时序故障覆盖 BUSY 引脚的全部已定义物理异常场景，回答两个问题：

1. 当 BUSY 反馈异常时，固件是否会把“未完成的刷新”误报为完成（Host 收到
   `DEVICE_REFRESH_FLOW_COMPLETE`）？
2. 每一次实际发生的物理 FULL refresh 是否可被精确计数，并与软件调用次数对齐？

本规格只定义测试、判据和证据；**不修改固件**。任一场景失败只产出 finding，
最小修复必须另立阶段并单独授权。

## 2. 已验证的代码事实

| 事实 | 证据 |
|---|---|
| BUSY 引脚为 GPIO13 | `hardware/gdey042t81_esp32/src/h1/config.h`（`EPD_BUSY == 13`） |
| 该驱动以 **HIGH = busy** | `GxEPD2_420_GDEY042T81` 构造函数传入 `busy_level=HIGH` |
| BUSY 等待上限 10 s | 同上，`busy_timeout=10000000`；`h1/contract.h` 的 `kTimeoutUs=10000000` |
| `init()` 只把 BUSY 设为 `INPUT`，不读、不拒绝 | `GxEPD2_EPD::init()`；STEP017F 已移除 pre-init BUSY=HIGH 的早拒绝 |
| 写 RAM 后、refresh 前检查 BUSY=HIGH | `network_progress/main.cpp`：HIGH 时打印 `NETWORK_DISPLAY_BUSY_POST_PREPARE_HIGH` 并返回 false |
| `refresh(false)` 内先发刷新命令，再等待 BUSY 变低 | `GxEPD2_420_GDEY042T81::_Update_Full()` → `_waitWhileBusy()` |
| 超时打印 `Busy Timeout!`，但等待函数不返回失败 | `GxEPD2_EPD::_waitWhileBusy()` |
| 刷新后立即读 BUSY，判据为 `invoked && !(busy || elapsed>=10s)` | `network_progress/main.cpp` + `timedOutOrUnknown()` |
| 失败路径 | `machine.h` `DisplayUpdate`：`display()` 返回 false → `fault(Failure::DisplayInvariantFailure)`（FaultStop）；不推进 accepted ETag、不发完成报告 |
| 成功路径 | 打印 `NETWORK_SOFTWARE_RETURN_CONDITIONS_MET_NOT_PHYSICAL_PASS`，推进 accepted ETag，Host 可收到 `DEVICE_REFRESH_FLOW_COMPLETE` |
| BUSY 故障注入 | **从未执行**（PROJECT_STATE 多次记录 `BUSY_FAULT_INJECTION = NOT RUN`） |

关键推论（待测试证实）：

- BUSY 持续为 **LOW** 时，`_waitWhileBusy()` 立即返回，刷新后读到的也是 LOW，
  固件会把它当作成功。当前代码没有“必须观察到 BUSY 拉高”这一判据。
- BUSY 过早释放（早于真实刷新完成）同样会被当作成功。
- BUSY 持续为 HIGH 时，10 s 后超时，固件进入 FaultStop，属安全失败。
- 现有 `DEVICE_REFRESH_FLOW_COMPLETE` 的契约只是“软件返回条件”，不是物理确认；
  本测试要区分“软件契约内”与“目标 1 要求的物理安全”。

## 3. 故障模型

只覆盖 BUSY 反馈链路，不覆盖面板电源、SPI、RST 或过压/ESD 破坏性测试。

| ID | 故障 | 注入方式（ESP32 侧） | 预期物理含义 |
|---|---|---|---|
| F1 | 常低（0 V） | 1 kΩ 下拉到 GND | 面板永不让 BUSY 拉高；反馈失效或面板无响应 |
| F2 | 常高（3.3 V） | 1 kΩ 上拉到 3V3 | BUSY 永不释放 |
| F3 | 延迟释放 | 刷新命令后拉高，>10 s 后释放 | 面板忙时间超出固件预算 |
| F4 | 过早释放 | 刷新命令后拉高，100 ms 后释放 | 面板仍忙，固件提前认为完成 |
| F5 | 毛刺/抖动 | 刷新期间 10 ms 脉冲串，最终低 | 噪声耦合、接触不良 |
| F6 | 开路/悬空 | 断开注入源，ESP32 输入浮空 | 断线、虚焊；输入电平未定义 |
| F7 | 开路 + 下拉 | 悬空 + 外部 100 kΩ 下拉 | 断线且有弱下拉，稳定为 LOW |
| F8 | 对 GND 短路 | 1 kΩ 限流短接 GND | 与 F1 类似的硬故障 |
| F9 | 对 3V3 短路 | 1 kΩ 限流短接 3V3 | 与 F2 类似的硬故障 |
| F10 | 刷新期间反复拉高/低 | 100 Hz、50% 占空比，最终低 | 面板/走线噪声，边界抖动 |

不在本规格内：5 V 注入、直接短接无 1 kΩ 限流、ESD 枪、过压、热插拔、面板排线
弯折、Partial/Fast refresh、Deep Sleep、长期老化。

## 4. 测试夹具与安全

### 4.1 夹具要求

1. BUSY 网络必须可断开：在面板 BUSY 与 GPIO13 之间加可拔跳线/排针；
   不要直接剪断排线。
2. **双通道观察**：
   - 通道 A：面板侧 BUSY（隔离点之前），代表真实面板忙闲；
   - 通道 B：ESP32 侧 BUSY（隔离点之后），代表固件看到的电平。
   逻辑分析仪同时采样 A/B + SPI CS（或刷新命令触发），用于对齐注入时刻。
3. 注入源只驱动 ESP32 侧：3.3 V 逻辑、开漏/MOSFET 或手动开关 + 1 kΩ 串联。
   不得与面板输出直接对拉。
4. 共地；注入前用万用表/示波器确认电平与限流；电源使用现有 USB 供电，
   不额外引入 5 V。
5. 面板其余连线保持原状；面板 BUSY 断开不影响面板自身刷新，因此可以保留
   “真实刷新”与“固件看到的值”两条独立证据。

### 4.2 安全

- 改线前断电；不得带电插拔跳线。
- ESD 防护；不触碰排线金手指。
- 任何过流、发热、面板异常、复位循环立即中止并恢复原状。
- 不擦 NVS、不做 OTA、不改分区表、不发布新固件。
- 物理改线与断电上电属于独立确认项；本规格不构成执行授权。

## 5. 阶段与时序

| 阶段 | 固件行为 | 可注入点 |
|---|---|---|
| P0 启动/初始化 | `coldInit()`；BUSY 仅设为 INPUT，不读 | 上电即保持故障电平（F1/F2/F6/F7/F8/F9） |
| P1 prepare 后、refresh 前 | 读 BUSY；HIGH → 立即失败 | F2/F9 可在此被捕获 |
| P2 refresh 命令后、等待中 | `_waitWhileBusy()` 等 BUSY 变低，上限 10 s | F3/F4/F5/F10 的时序注入 |
| P3 刷新后判定 | 再读 BUSY + elapsed 判据 | F4/F5/F10 的最终电平决定结果 |
| P4 空闲轮询 | 不读 BUSY；无中断 | 仅验证不会误触发（可选） |

时序注入以逻辑分析仪触发 SPI CS 或 BUSY 上升沿为准；手工开关只用于常低/常高，
不用于 100 ms 级时序。

## 6. 测试矩阵与判据

每个用例都以“断电上电 → 设备取到 200 帧 → 触发一次 display”为一次完整尝试。
上电清除 RAM 中的 accepted ETag，因此同一帧也会返回 200 并触发一次显示尝试；
若出现 304，该用例无效，需重新上电。

| 用例 | 故障/阶段 | 期望的安全行为（目标 1） | 当前代码预测 | 判定 |
|---|---|---|---|---|
| B0 | 无故障基线 | 1 次软件调用 = 1 次物理刷新；Host 完成 | 成功；`_Update_Full : ~2.2s` | PASS 的基准 |
| B1 | F1 常低（P0 起） | 不得报告完成；FaultStop 或显式 UNKNOWN | **预测误报成功**（等待立即返回，post-read LOW） | 预测 FAIL → finding |
| B2 | F2 常高（P0 起） | P1 捕获；FaultStop；不调用 refresh | `NETWORK_DISPLAY_BUSY_POST_PREPARE_HIGH`，FaultStop | 预测 PASS |
| B3 | F2 常高（P2 起，保持 >10 s） | 超时；FaultStop；不报告完成 | `Busy Timeout!` + `NETWORK_DISPLAY_TIMEOUT_OR_UNKNOWN` | 预测 PASS（物理可能已刷新，需记录） |
| B4 | F3 延迟释放 11 s | 同 B3 | 同 B3 | 预测 PASS |
| B5 | F4 100 ms 释放 | 不得在面板仍忙时报告完成 | **预测误报成功** | 预测 FAIL → finding |
| B6 | F5 毛刺，最终低 | 最终低且 <10 s 时不得误判完成 | **预测误报成功** | 预测 FAIL → finding |
| B7 | F6 悬空 | 不得误报完成；不得崩溃；结果可重复 | 输入未定义，可能成功或超时 | 需 10 次重复；任一次误报即 FAIL |
| B8 | F7 悬空+下拉 | 同 F1 | 预测误报成功 | 预测 FAIL → finding |
| B9 | F8 对 GND 短路 | 同 F1 | 预测误报成功 | 预测 FAIL → finding |
| B10 | F9 对 3V3 短路 | 同 B2/B3 | 超时/FaultStop | 预测 PASS |
| B11 | F10 反复抖动，最终低 | 最终低且 <10 s 时不得误判完成 | 预测误报成功 | 预测 FAIL → finding |

判定口径：

- **PASS**：该用例满足“期望的安全行为”，且无崩溃、无 NVS/OTA/网络副作用，
  刷新计数与物理证据一致。
- **FAIL**：Host 收到 `DEVICE_REFRESH_FLOW_COMPLETE`，但逻辑分析仪/可见变化
  不能证明面板在该次调用中完成了一次真实 FULL refresh；或出现崩溃/复位循环。
- **UNOBSERVABLE**：缺少标记、夹具无法隔离、或 Host 不可达，无法判定；
  不得用“看起来正常”替代。
- B1/B5/B6/B7/B8/B9/B11 的预测 FAIL 是**基于代码审查的假设**，必须由实测证实或推翻；
  若实测误报，目标 1 不通过，进入最小修复阶段。

### 6.1 软件契约与物理目标的区分

- 现有契约中 `DEVICE_REFRESH_FLOW_COMPLETE` 只表示“软件返回条件满足”，
  页面也标注“不代表物理屏幕已人工确认”。因此 B1/B5 的误报在**旧契约内**
  可能不算回归，但**不满足目标 1**。
- 测试报告必须同时给出两列：`software_contract`（旧契约是否被违反）与
  `physical_safety`（目标 1 是否满足），不得用前者替后者。

## 7. 物理 FULL refresh 计数口径

当前没有持久计数器；串口 `_Update_Full : N` 是驱动等待耗时，不是物理次数。
本测试定义：

| 计数 | 定义 | 采集方式 |
|---|---|---|
| `software_invocations` | `refreshOnce()` / `_Update_Full` 被调用次数 | 串口 `_Update_Full` 行数 + 代码路径 |
| `physical_refreshes` | 面板侧 BUSY 出现一次完整 HIGH→LOW，且屏幕内容发生可见变化 | 逻辑分析仪通道 A + 照片/目视 |
| `host_completions` | Host 收到 `DEVICE_REFRESH_FLOW_COMPLETE` 的次数 | Host 日志/状态 |

B0 基线要求三者均为 1。故障用例分别记录，任何 `host_completions > physical_refreshes`
即为误报证据。

仅比较次数还不够：**Host 完成报告必须晚于面板侧 BUSY 落低**。若完成报告早于面板
BUSY 的下降沿（B5/B6/B11 的典型情形），即使次数相等，也判为误报。若无法接入
逻辑分析仪，`physical_refreshes` 标记为 `VISUAL_ONLY`，并降低结论强度。

## 8. 前置条件

- 设备为 `round2-r6-2`，NVS 凭据保留；不执行 OTA、不擦 NVS。
- Host 可被设备访问；当前 Host 已停止。恢复方式二选一，且属于独立决定：
  (a) 给项目 venv 的 `python.exe` 加入 Windows 入站允许规则；
  (b) 重新安装隔离依赖并用被允许的解释器启动。
  不得在本测试中顺手改防火墙或安装依赖。
- Host 提供一帧已知内容（可用已记录的 R4 帧）；每次上电后 200 触发显示。
- 逻辑分析仪/示波器、可断开的 BUSY 跳线、1 kΩ/100 kΩ 电阻、3.3 V 注入源。
- 器材型号、数量、预算与接线核对见 [BUSY 器材采购表](../../BUSY-HARDWARE-BOM.md)；
  分 A/B/C 三组，A 组即可解锁 B1/B2/B9/B10。
- 物理改线、断电上电、Host 启动均需单独确认。

## 9. 执行流程（每个用例）

1. 断电，按用例接入 BUSY 跳线/注入源；确认无限流错误。
2. 上电，确认设备启动并取帧（串口状态、Host 200）。
3. 在指定阶段注入故障（P1 手动；P2/P3 用分析仪触发）。
4. 记录：串口全部标记、`NETWORK_STATE`、`_Update_Full`、Host 状态/完成报告、
   分析仪 A/B 波形、屏幕照片、时间戳。
5. 断电，移除故障，恢复跳线；上电确认恢复正常显示与 Host 完成。
6. 记录恢复证据；进入下一用例。
7. 任一用例出现崩溃/复位循环/面板异常，立即中止并恢复。

## 10. 证据与报告

- 串口原文（含 `Busy Timeout!`、`NETWORK_DISPLAY_*`、`NETWORK_SOFTWARE_*`、
  `_Update_Full`）。
- Host 日志与 `status` 快照（`DEVICE_REFRESH_FLOW_COMPLETE` 是否存在）。
- 逻辑分析仪双通道波形（面板侧/ESP32 侧 BUSY + CS 触发），保存原始文件。
- 屏幕照片（每次用例前后）与夹具照片。
- 每用例一行结果：`case, phase, fault, software_invocations, physical_refreshes,
  host_completions, device_state, result(PASS/FAIL/UNOBSERVABLE), notes`。
- 不含任何 Wi-Fi 凭据、令牌或固件私有配置。

## 11. 中止条件

- 面板/驱动发热、过流、异味、可见损伤。
- 设备反复重启、panic、堆损坏、NVS/OTA 异常。
- Host 不可达或无法稳定复现 200 取帧，导致无法判定。
- 任何需要 5 V、无 1 kΩ 限流或直接对拉面板输出的操作。
- 发现物理改线超出已确认范围。

## 12. 退出标准与后续

- 全部用例有 PASS/FAIL/UNOBSERVABLE 结论；没有“应该没问题”。
- 若 B1/B5/B6/B7/B8/B9/B11 任一项 FAIL：目标 1 不通过，产出 finding，
  另立最小修复阶段。候选方向（仅记录，不决定）：
  - 刷新后要求在限定窗口内观察到 BUSY 至少一次拉高，否则判定 UNKNOWN；
  - 增加最小刷新时长下限（例如低于真实刷新时间即判 UNKNOWN）；
  - 将“未观察到忙信号”显式映射为 FaultStop，而不是成功。
- 若全部 PASS：把本规格的矩阵与结果写入 `PROJECT_STATE.md`，
  并把“物理 FULL refresh 计数口径”固定为后续测试的默认口径。
- 本阶段不修改固件、不提交产品代码；测试报告与规格可单独提交文档。

## 13. 开放问题

1. 是否有可断开的 BUSY 跳线/排针，或必须用备用面板/测试排线？
2. 是否有逻辑分析仪可同时抓面板侧与 ESP32 侧 BUSY？
3. “所有物理异常场景”是否包含 ESD/过压等破坏性测试？本规格默认排除。
4. 目标 1 的验收是否要求“BUSY 未拉高即不得报告完成”，还是接受旧契约的
   “软件条件”语义、只要求 UI 明确标注？
5. Host 恢复采用防火墙规则还是隔离依赖？该选择影响后续所有真机测试。
6. B7 悬空场景是否需要外部下拉作为独立用例，还是只记录未定义行为？
