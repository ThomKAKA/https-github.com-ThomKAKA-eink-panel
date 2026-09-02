# NekoPaw 架构对标评估

> 评估性质：Phase 4 前置研究，不代表 Phase 4 已启动
> 当前项目基线：Phase 3 Stable，111 项测试通过；STEP-006 已完成，纯基线由 `v0.3.0-phase3-stable` 锁定
> 参考快照：[`TruElysia02/NekoPaw@5df589d`](https://github.com/TruElysia02/NekoPaw/tree/5df589d7534b81e81208dbbab836454797f45f6b)
> 许可：参考项目使用 [MIT License](https://github.com/TruElysia02/NekoPaw/blob/5df589d7534b81e81208dbbab836454797f45f6b/LICENSE)。本评估只借鉴设计思想，不复制代码或 UI。

## 1. 结论先行

NekoPaw 不是通用 AI Agent、插件或长期记忆框架。按本次固定快照，它的核心是：让 AI 通过轻量 HTTP Bridge 发现并控制 ESP32 设备能力，并通过独立渲染 Skill 将 Markdown 或 scene JSON 转成预览图和 1bpp 位图。

当前项目则是一个 400×300 的数据驱动墨水屏信息终端：数据通过 DataAdapter 和 RefreshManager 进入固定 Panel schema，再由统一渲染链生成 PNG/BMP。双方解决的是相邻但不同的问题：NekoPaw 更接近设备控制与交互桥，本项目更擅长稳定的数据归一化、状态回退和信息面板渲染。

最值得吸收的不是一套“大而全”的 Agent 架构，而是五项边界清晰的能力：

1. 先发现能力，再选择命令。
2. 预览优先，并在发送位图前做尺寸预检。
3. 将渲染与设备通信分离。
4. 用有限状态机表达需要用户确认的交互。
5. 用轻量 watch/poll 接口处理设备事件，不把它误扩展成复杂消息总线。

因此，推荐的 Phase 4 方向是保留现有 `DataAdapter → RefreshManager → Panel` 主链，只在真实需求出现后增加轻量推送入口和单进程状态快照。现阶段不建设通用插件系统、复杂 Event Bus、数据库或完整 Agent/记忆层。

## 2. 项目定位与数据流

### 当前项目

```text
Mock / Local JSON / HTTP JSON
              ↓
          DataAdapter
              ↓
        RefreshManager
    semantic validation + LKG
              ↓
  Progress / Stats / Flow Panel
              ↓
      400×300 PNG / 1-bit BMP
              ↓
        Browser Simulator
```

当前架构把数据获取、错误恢复、Panel 语义检查和绘制职责分开。HTTP 断线或数据无效时，Last Known Good 可保持旧画面并标记 OFFLINE/STALE；同源刷新串行、跨源刷新并行，浏览器还会忽略过期响应。

### NekoPaw

```text
AI / CLI
   ├─ Render Skill: Markdown / scene JSON → preview → 1bpp bitmap
   └─ Bridge Skill: capability discovery → HTTP Bridge → ESP32 providers
                                                    ├─ display
                                                    ├─ sensor / input events
                                                    └─ LED / buzzer outputs
```

NekoPaw 的控制 Skill 要求先执行 `device info` 并读取 `data.capabilities`，再决定是否调用 display、sensor、event 或 output 命令；渲染 Skill 则明确要求先生成预览，再转换为 1bpp 位图。相关依据见 [控制 Skill](https://github.com/TruElysia02/NekoPaw/blob/5df589d7534b81e81208dbbab836454797f45f6b/skill/SKILL.md) 和 [渲染 Skill](https://github.com/TruElysia02/NekoPaw/blob/5df589d7534b81e81208dbbab836454797f45f6b/skill/render/SKILL.md)。

## 3. 能力对标

| 能力 | NekoPaw 固定快照 | 当前项目 | 结论 |
| --- | --- | --- | --- |
| 产品中心 | ESP32 设备能力与 HTTP 控制桥 | 400×300 信息面板模拟与图片输出 | 定位互补，不互相替代 |
| 输入数据 | CLI/HTTP 命令、Markdown、scene JSON | Mock、Local JSON、HTTP JSON | 保留现有 Adapter；未来推送也必须走语义验证 |
| 数据归一化 | 以设备命令和渲染输入为中心 | 统一 Panel schema 与 `normalize()` | 当前项目更适合稳定信息终端 |
| 能力发现 | `device info` 返回 capabilities 后再选命令 | 数据源配置已知，尚无设备能力描述 | 值得在接硬件前吸收 |
| 渲染链 | 预览 PNG → 黑白预览/1bpp raw bitmap | Panel → 400×300 PNG/1-bit BMP | 思路一致；本项目固定画布验证更成熟 |
| 位图预检 | CLI 按设备信息核对 raw bitmap 字节数 | API 测试固定尺寸和 BMP mode | 未来接设备时增加“目标能力驱动”的预检 |
| 状态恢复 | 有显示状态和确认会话状态 | ONLINE/OFFLINE/ERROR、LKG、STALE | 当前项目的数据恢复更完整 |
| 交互确认 | pending/confirmed/cancelled/timeout | 当前无双向确认流程 | 真实交互需求出现后可借鉴状态模型 |
| 事件机制 | 有限容量 watch + event queue + poll/drain | 以浏览器定时拉取和手动刷新为主 | 可借鉴轻量入口，不等同通用 Event Bus |
| 并发稳定性 | 本次审查未发现与当前刷新管理等价的协议 | 同源锁、跨源并行、浏览器请求代次 | 当前项目应保持现有优势 |
| 通用插件系统 | 本次审查范围内未发现通用插件契约 | 适配器工厂可扩展，但不是插件运行时 | 不应把推测当作参考项目能力 |
| 持久化记忆 | 本次审查范围内未发现长期状态存储 | LKG 为单进程内存缓存 | Phase 4 先做状态快照，不先上数据库 |
| 硬件驱动 | Arduino/ESP32 provider 抽象 | Phase 3 明确不含硬件 | 到真实设备选型确定后再评估 |

NekoPaw 的事件实现可由 [`EventManager.h`](https://github.com/TruElysia02/NekoPaw/blob/5df589d7534b81e81208dbbab836454797f45f6b/src/nekopaw/core/EventManager.h) 复核：它维护固定容量的 watch 记录和内存事件队列，并提供 drain 操作。这是适合嵌入式设备的轻量 watch/poll 机制，而不是具有持久化、重放、订阅拓扑和跨进程投递保证的通用 Event Bus。

确认状态由 [`NekoPaw.h`](https://github.com/TruElysia02/NekoPaw/blob/5df589d7534b81e81208dbbab836454797f45f6b/src/NekoPaw.h) 中的 `Idle / Pending / Confirmed / Cancelled / Timeout` 表达。scene JSON 则主要处理固定布局、图片窗口和低分辨率文字栅格化，详见 [`SCENE_JSON.md`](https://github.com/TruElysia02/NekoPaw/blob/5df589d7534b81e81208dbbab836454797f45f6b/docs/SCENE_JSON.md)。这些能力可以作为设计参考，但不需要替换当前已经统一的三种 Panel 和 Design System。

## 4. 候选设计评分

评分使用 1–5：真实需求、墨水屏收益和可延期性越高分越强；维护成本和稳定风险越高分越昂贵或危险。可延期性高意味着当前更适合推迟。

| 候选设计 | 真实需求 | 墨水屏收益 | 维护成本 | 稳定风险 | 可延期性 | 决策 |
| --- | :---: | :---: | :---: | :---: | :---: | --- |
| 设备/数据源能力描述 | 4 | 4 | 2 | 1 | 3 | 硬件或多目标输出前引入 |
| 预览优先与目标位图预检 | 5 | 5 | 1 | 1 | 2 | 保持现有验证，接设备时增强 |
| 渲染与设备桥接分离 | 5 | 5 | 2 | 1 | 2 | 作为后续硬件边界 |
| 确认状态机 | 2 | 3 | 2 | 2 | 5 | 等真实双向交互需求 |
| 轻量 push + watch/poll 入口 | 4 | 4 | 3 | 3 | 3 | 推荐作为 Phase 4 首个验证项 |
| 单进程状态快照 | 4 | 4 | 2 | 2 | 3 | 与轻量 push 一起验证 |
| 通用插件运行时 | 2 | 2 | 5 | 4 | 5 | 暂不引入 |
| 复杂 Event Bus / 消息队列 | 1 | 1 | 5 | 5 | 5 | 不引入 |
| 数据库与长期 Agent 记忆 | 2 | 2 | 5 | 4 | 5 | 需求和保留策略明确后再议 |
| ESP32/墨水屏硬件驱动 | 3 | 5 | 4 | 4 | 4 | 等设备型号、电源与刷新策略确定 |

## 5. 三条 Phase 4 路线

### 上策：稳健均衡（推荐）

保留现有 Adapter 拉取链，新增一个轻量事件输入边界和单进程状态快照。候选事件只表达来源、目标 Panel、发生时间和 Panel 数据；服务端仍使用现有 Panel `normalize()` 做语义检查，只有有效结果才能更新状态。拉取与推送在语义验证之后汇合，不建设通用插件加载器。

收益：主动更新能力可用最少的新概念完成，同时复用 Phase 3 的错误恢复与渲染稳定性。

代价：需要定义幂等、事件顺序和重启清空语义。

失败模式：若直接让事件绕开 Panel 验证，可能重新引入状态污染；若把单进程快照误当可靠消息存储，则会产生错误预期。

### 中策：保底止损

只补充能力描述、目标位图预检和确认状态模型的设计，不增加主动推送。继续由 Mock、Local JSON 和 HTTP JSON 驱动现有面板。

收益：风险和维护成本最低，最快保持稳定基线。

代价：Codex、脚本或未来设备不能主动驱动画面，只能等待下一次拉取。

失败模式：真实事件频率高于刷新间隔时，状态可能滞后或丢失中间过程。

### 下策：激进高成本

同时建设 Event Bus、插件系统、Agent Adapter、持久化记忆和硬件桥接。

收益：理论扩展上限最高。

代价：一次引入多个生命周期、错误边界和兼容协议。

失败模式：数据问题、插件问题、消息顺序、持久化、硬件刷新和 UI 问题互相叠加，难以定位回归；当前没有足够真实需求支撑该复杂度，因此不建议。

## 6. 推荐顺序

### P0：锁定 Phase 3 基线（已完成）

- 用户已核对 STEP-006 中的灾后重建清单。
- 首次提交和 `v0.3.0-phase3-stable` annotated tag 已锁定纯 Phase 3 基线。
- NekoPaw 对标研究位于标签之后，Phase 4 仍未开始。

### P1：验证轻量主动更新

- 先写一页候选事件契约和状态生命周期，不直接做插件框架。
- 用 ProgressPanel 的有限状态演示验证主动事件、重复事件、乱序事件和重启清空。
- 推送数据必须与拉取数据一样经过 Panel 语义检查；无效事件不能污染 Last Known Good 或当前状态。
- 验证成功后，再决定它应成为 HTTP push endpoint、文件 inbox，还是保持为本地调用接口。

### P2：由真实场景决定扩展

- 有多个独立第三方集成并且安装/卸载需求稳定后，再评估插件契约。
- 有跨重启保留、审计或回放需求后，再选择持久化方式。
- 设备型号、分辨率、局刷能力、电源预算和输入硬件确定后，再设计设备桥接和位图预检。
- 只有出现跨进程投递、可靠重放或大量订阅者，才重新评估消息队列；否则保持轻量实现。

## 7. 边界与验收门槛

本评估不新增公开 API、数据结构、依赖或运行方式。上文事件接口和状态快照仅是候选方向，不是已冻结的 Phase 4 规格。

进入实现前必须同时满足：

- STEP-006 已由用户确认，Phase 3 已建立可回退的 Git 基线。
- 选定一个真实主动更新场景，而不是为了模仿参考项目增加功能。
- 新数据入口仍遵守 `Data Source → validation/normalization → Panel → Renderer` 的职责边界。
- 不破坏 Progress、Stats、Flow 的视觉基准和 400×300、1-bit 输出约束。
- 为乱序、重复、无效数据、断线和恢复定义可测试的结果。

在这些条件满足前，保持当前 Phase 3 Stable 架构比提前建设通用 Agent 平台更符合本产品目标。
