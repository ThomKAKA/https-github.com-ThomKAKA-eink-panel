# 项目进度记录（灾后重建版）

> 重建时间：2026-09-01 12:15
> 重建方式：基于文件系统痕迹推断，非原始保存
> 整体进度：Phase 3 100%，Phase 4 P1 软件 STABLE，P1.5 SCAFFOLD COMPLETE
> 当前执行到：STEP-009（本地基线与 H0 验收准备完成）
> 项目状态：IMPLEMENTED=YES / COMPILE VERIFIED=NO / HARDWARE VERIFIED=NO；停在 H0 材料核对
> 本文档完整性：<!-- PROGRESS_COMPLETE -->

<!-- LOCKED:START -->
## 🔒 不可变更区

### 项目核心目标
开发一个 400×300 黑白极简终端风墨水屏信息面板模拟器，并为未来真实设备保留稳定的图片输出接口。

### 技术方案及原因
使用 Python 3.12、FastAPI、Pillow 和原生 HTML/CSS/JavaScript：依赖少、Windows 上容易启动，Pillow 能直接生成未来墨水屏可使用的 PNG/BMP 和 1-bit 图像。

### 关键决策及原因
- Panel 只负责结构化数据渲染，数据获取统一经过 DataAdapter，避免界面与具体数据源耦合。
- RefreshManager 统一管理刷新状态和 Last Known Good，使 HTTP 断线时仍能显示上一次成功数据。
- Progress、Stats、Flow 共用 400×300 画布和 Design System，保持实体终端视觉一致。

### 不可偏离的约束
1. 当前不接入 ESP32、真实硬件、AI Agent 或账号型公网 API。
2. 不新增面板，不破坏已经确认的三面板视觉基准。
3. 数据源必须通过 DataAdapter，Panel 不直接访问 HTTP 或文件。
<!-- LOCKED:END -->

## 📋 项目规划（里程碑拆解）
| 里程碑 | 内容 | 状态 | 置信度 |
|---|---|---|---|
| M1 | ProgressPanel、Design System、基础模拟器 | ✅完成 | 高 |
| M2 | StatsPanel、FlowPanel、三面板切换与导出 | ✅完成 | 高 |
| M3 | Mock/Local/HTTP DataAdapter、自动刷新、断线回退 | ✅完成 | 高 |
| M4 | 对抗性审查与连续刷新验证 | ✅完成 | 高 |
| M5 | Phase 4 P1 轻量事件入口与单进程状态快照 | 软件 STABLE | 高 |
| P1.5 预备层 | 隔离的 GDEY042T81 ESP32 H0/H1 骨架与协议文档 | SCAFFOLD COMPLETE；编译/实物未验证 | 源码高、实物未知 |

## ✅ 已完成清单（推断）
### M1：ProgressPanel 与视觉基线
- 完成内容：400×300 ProgressPanel、统一字体/间距/边框、Normal/E-Ink 预览。
- 证据：`panels/progress.py`、`panels/design_system.py`、`docs/DESIGN_SYSTEM.md` 及通过的测试。
- 置信度：高
- 验证状态：已验证

### M2：三面板统一模拟器
- 完成内容：StatsPanel、FlowPanel、面板切换、PNG/BMP 导出。
- 证据：`panels/stats.py`、`panels/flow.py`、Web 控制界面及浏览器运行探针。
- 置信度：高
- 验证状态：已验证

### M3：真实数据接入基础层
- 完成内容：Mock、本地 JSON、HTTP JSON、自动刷新、状态显示、Last Known Good 回退。
- 证据：`adapters/`、`services/refresh_manager.py`、Phase 3 API、说明文档及 77 项通过测试。
- 置信度：高
- 验证状态：已验证

## 📁 文件变更日志（含状态标签）
| 文件路径 | 操作 | 状态 | 变更摘要（推断） | 回退命令 |
|---|---|---|---|---|
| `panels/` | 新增 | ✅ | 三种面板及共享绘制系统 | `v0.3.0-phase3-stable` |
| `adapters/` | 新增 | ✅ | 三种统一数据适配器 | `v0.3.0-phase3-stable` |
| `services/refresh_manager.py` | 新增 | ✅ | 刷新、状态与断线缓存 | `v0.3.0-phase3-stable` |
| `server/main.py` | 新增/修改 | ✅ | Phase 3 API 与图片渲染 | `v0.3.0-phase3-stable` |
| `web/` | 新增/修改 | ✅ | 三面板、数据源及自动刷新控制 | `v0.3.0-phase3-stable` |
| `tests/` | 新增 | ✅ | 111 项面板、Adapter、刷新、并发和 API 测试 | `v0.3.0-phase3-stable` |
| `README.md`、`docs/` | 新增/修改 | ✅ | Phase 3 使用与架构说明 | `v0.3.0-phase3-stable` |
| `examples/http_server.py` | 修改 | ✅ | Progress、Stats、Flow HTTP 模拟值按固定序列变化并在终值保持 | `v0.3.0-phase3-stable` |
| `tests/test_example_http_server.py` | 新增 | ✅ | 验证三个面板动态序列及终值保持规则 | `v0.3.0-phase3-stable` |

## 📝 待办队列（STEP编号）
### STEP-004（已完成）
- 动作：用 StatsPanel 连续模拟 TODAY TOKEN 为 258.42M、260.11M、264.73M。
- 预期产出：三次刷新按固定顺序更新同一 StatsPanel，其余字段和视觉保持不变。
- 验证方式：自动测试、API 响应检查、浏览器逐次刷新截图或可见数值检查。
- 前置条件：无半成品文件；先复测当前 77 项基线。
- 状态：✅ 已完成
- 验证结果：78 项测试通过；浏览器三次画面依次显示 258.42M、260.11M、264.73M；HTTP 状态保持 ONLINE，控制台无错误。

### STEP-005（已完成）
- 动作：继续执行 Phase 3 对抗性审查，检查异常 JSON、HTTP 失败、刷新竞争和回退状态。
- 预期产出：问题清单、修复结果和新增回归测试。
- 验证方式：完整测试集和浏览器关键流程检查。
- 已完成子步骤：FlowPanel 连续模拟“准备 → 执行 → 完成”，节点依次为“实心/空心/空心 → 实心/实心/空心 → 全部实心”。
- 子步骤验证：79 项测试通过；浏览器三次画面正确，HTTP 状态 ONLINE，控制台无错误；完成后保持全实心状态。
- 已完成子步骤：ProgressPanel 使用 Codex 开发进度连续模拟“72% → 73% → 81% → 等待确认 → 100%”。等待确认阶段保持 81%，完成后保持 100%。
- 子步骤验证：80 项测试通过；浏览器五次画面正确，HTTP 状态 ONLINE，控制台无错误。
- 状态：✅ 已完成
- 对抗性验证：异常 JSON、HTTP 失败、语义无效数据、Last Known Good、同源/跨源刷新竞争、三面板各 100 次刷新和渲染均已覆盖。
- 最终验证：111 项测试通过；浏览器验证首次断线等待态、缓存回退 OFFLINE/STALE、恢复 ONLINE、5 秒自动刷新、重复手动刷新和面板切换，控制台无错误。
- 产出：`docs/PHASE3_ADVERSARIAL_AUDIT.md`、`docs/PHASE3_STABLE.md`、`docs/GIT_BASELINE_PLAN.md`。

### STEP-006（已完成）
- 动作：完成 M4 后由用户核对灾后重建的已完成清单。
- 预期产出：确认后的真实项目基线。
- 验证方式：用户确认。
- 状态：✅ 已完成
- 确认结果：用户已确认 Phase 3 Stable 灾后重建基线；完整测试保持 111 项通过。
- 基线：首次提交使用 `Phase 3 stable baseline`，并以 annotated tag `v0.3.0-phase3-stable` 锁定。
- 下一步：等待用户批准 Phase 4 P1；当前不实施主动推送、状态快照、Agent 或硬件能力。

### STEP-007（已完成）
- 动作：实现轻量 `panel.update` HTTP 入口与按 Panel、source 分区的单进程状态快照。
- 产出：`services/event_store.py`、事件写入/快照 API、`docs/EVENT_INGESTION.md`。
- 边界：不引入 Event Bus、插件、数据库、消息队列、WebSocket、Agent 直连或硬件。
- 验证：完整测试 125 项通过；有效更新、重复幂等、乱序拒绝、无效数据不污染、并发顺序、source 隔离和重启清空均有自动测试。
- 运行探针：72% → 81% 更新成功，重复事件保持 81%，旧事件返回 409，快照可继续渲染为 400×300 PNG。
- 状态：✅ 已完成
- 下一步：由用户决定是否把快照接入模拟器数据源，或继续保持 API-only。

### STEP-008（预备骨架已实现，非硬件验收完成）
- 动作：按用户选择建立通用 `esp32dev` 示例环境，仅定义未来帧协议，不新增 FastAPI endpoint。
- 产出：`hardware/gdey042t81_esp32/`；H0 本地英文图案、H1 编译期 raw bitmap、RefreshPolicy、禁用 FrameFetcher、接线/bring-up/故障隔离文档。
- 安全边界：未确认的本地引脚配置不驱动显示 GPIO；不接服务器、不理解 Panel JSON，不改现有 UI、事件 API 或 PNG/BMP。
- `IMPLEMENTED: YES`：指源代码与文档骨架，不表示物理显示已成功。
- `COMPILE VERIFIED: NO`：PlatformIO、Arduino CLI 及主机 C++ 编译器不可用，未安装工具链；已写 7 组 C++ 核心测试但未执行。
- `HARDWARE VERIFIED: NO`：未烧录、未接线、未进行屏幕/BUSY/刷新/残影实测。
- Python 回归：125 项通过；未新增 Python 硬件依赖或帧端点。
- 刷新策略：首次普通 FULL，同帧保持，默认间隔 5 秒，连续 5 次 PARTIAL/FAST_FULL 后下一次变更为普通 FULL；仅提供手动启用的有限演示。
- 状态：Phase 4 P1.5 scaffold 已交付，未宣称硬件 stable；2026-09-03。
- 下一步：用户确认具体板型、驱动板、3.3V/FPC/接线，按 BRINGUP 先做 H0。H2/H3 和正式硬件集成未开始，需另行批准。
- Git（STEP-008 当时）：保留原有 P1 未提交改动；该步骤未提交、未打标签、未推送。后续基线见 STEP-009。

### STEP-009（本地基线与 H0 验收准备完成）

- 动作：按用户确认的边界，分别保存纯 P1 软件与 P1.5 硬件骨架，不改业务代码、固件、API、依赖、帧协议或 UI。
- 提交 A：`5490ad0fc7ba12d96e95cf4665cf9857d1ef963e` / `Phase 4 P1 stable baseline`；仅事件入口、状态快照、测试及 P1 文档，不包含硬件目录或 P1.5 状态。
- 提交 B：`feat: add GDEY042T81 ESP32 hardware scaffold`；硬件骨架、H0 清单、硬件忽略规则及完整状态记录。
- 恢复点：annotated tag `v0.4.1-phase4-hardware-scaffold` 指向 B，明确编译及实物验证尚未完成；既有 `v0.3.0-phase3-stable` 保持不变。沿用 Git 身份，不初始化、不修改 remote、不推送。
- 配置：沿用 `display_config.example.h / display_config.local.h`；私有配置被忽略，本次未创建私有配置或填写真实 GPIO。
- 验证：开始时工作区 125 项通过；提交 A 的暂存快照独立运行 125 项通过（0.91s）。迁移快照后，仓库及纯 P1 快照再次分别通过 125 项测试（均 0.89s），各 32 个 Python 文件语法检查通过；暂存 diff 检查通过。
- 暂停记录：最初将隔离快照放在 artifacts 内，提交 B 前默认 `pytest -q` 同时收集快照与根目录测试，产生 12 个 import file mismatch 收集错误（0.35s）；当时按停止条件暂停，未创建 B 或标签。
- 恢复记录：用户明确允许后，将本次快照移至仓库外 `D:\Codex\step009-p1-snapshot-557d93d74cf0487e899b996ddd6c84d6`，108 个文件逐一校验一致，无文件删除；未修改测试配置、业务代码或固件。默认测试重新通过后恢复提交流程。
- 审查：提交前核对实际文件清单、敏感信息模式、异常大文件与生成物；模式扫描无命中，不等同于完整安全审计。缓存、虚拟环境、私有配置与构建产物不入库。
- 骨架：`SCAFFOLD COMPLETE`；`IMPLEMENTED=YES`、`COMPILE VERIFIED=NO`、`HARDWARE VERIFIED=NO`。7 组 C++ 测试未运行。
- 环境：本次只检查工具是否存在；PlatformIO、Arduino CLI 未发现，没有安装、固件编译、烧录或实物验收。
- 清单：新增 `hardware/gdey042t81_esp32/docs/H0_CHECKLIST.md`，初始全部未勾选；PARTIAL、连续局刷后 FULL 与残影检查单列为 H0 通过后的 H1 验收。
- 状态：✅ 已完成两次本地提交与骨架标签、H0 验收准备；不表示 H0/H1 已通过。
- 下一步：仅开始 H0 材料核对；需要 ESP32 具体型号、驱动板照片、接线照片和屏幕实物照片。目前不具备实机通电、烧录验收条件；不进入 H2/H3。

## ⚠️ 已知问题与风险
- 灾后重建清单已经用户确认；原始进度记录缺失的历史限制仍然存在。
- Phase 3 纯基线由 `v0.3.0-phase3-stable` 标识；后续研究或实现应从标签之后独立演进。
- Last Known Good 仅保存在内存中，重启服务后会清空，这是 Phase 3 的既定范围。
- 刷新锁与 Last Known Good 仅协调单个 Python 进程；Phase 3 不支持多 worker 共享状态。
- EventStateStore 同样只存在于单个 Python 进程，重启即清空，并且不与 Last Known Good 合并。
- 事件 API 当前没有认证，只应使用默认本机绑定；P1 不包含浏览器实时通知。
- 硬件配置仅为通用示例，真实板型/转接电路/引脚未确认；不可直接照抄接线。
- 硬件骨架尚未通过 ESP32 编译或实物验收；GxEPD2 无像素读回，Serial Submitted 不等于显示成功。

## 📎 扩展区
### 重建说明
- 本文件由灾后重建生成，非原始进度保存。
- 推断依据：文件修改时间 + Git 状态 + 语法检查 + 运行探针。
- STEP-006 已完成用户核对；用户已批准并完成 Phase 4 P1，后续扩展仍需单独确认。
