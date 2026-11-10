# E-Ink 信息屏：可持续主线（v1.1）

> 本文件是**主线目标的唯一说明**，取代已删除的 `docs/GOALS.md`。
> 每次继续执行项目，**先按要求读本文件，再读 `PROJECT_STATE.md` 的最新阶段段**，然后才动手。
> 未读本文件、未确认当前阶段，不得开工。

---

## 0. 启动清单（每次继续执行前，强制）

1. **读**：本文件全文 → `PROJECT_STATE.md` 最新章节与 `NEXT_REQUIRED_STAGE` →
   `git log --oneline -5` + `git status --porcelain`。确认当前阶段、验收门、未收口项。
2. **核对事实**：帧契约 15,000 B、SHA-256 ETag、60 s 轮询、NVS 键、数据源可用性，
   以代码、日志、真机证据为准；不以文档愿望为准。文档与事实冲突时，以
   `PROJECT_STATE.md` 最新事实段为准，并回填本文件 §12。
3. **只选一件事**：只从 §5「未完成主线」里选**一个**增量。§4 的已完成项默认冻结，
   要改必须走 §4.3 的 reopen 协议，不得"顺手改"。
4. **不防御性编程**：不加无依据的兜底分支，不搭建用不到的抽象；错误路径只保留契约
   已要求的部分（超时、LKG、409、503 帧不可用）。
5. **一个增量一收口**：完成即验证、记录、提交；不可逆操作（刷机、推送、打 tag）
   必须单独确认。

## 1. 一句话目标

在同一台 Host、同一份帧契约下，400×300 墨水屏稳定切换 8 个页面，由 PWA 管家编辑与选页；
数据源故障保留上一帧并标 stale；设备能保存并自动切换多组已配网 Wi-Fi（不重新配网、不改帧契约）；
设备端保持零业务逻辑、零本地业务数据、零动画。

## 2. 现状基线（只列已验收事实，不重复执行）

- **已验收 · 渲染**：Host 用 Pillow 生成 15,000 B `epd-t-400x300-mono1-msb-v1` T 帧；
  设备校验长度、格式、SHA-256 后整屏刷新。8 页物理验收 PASS。
- **已验收 · 轮询**：设备每 60 s 取帧，内容不变返回 304；切页后 ≤2 个轮询内完成
  一次 200 + 一次整屏刷新。
- **已验收 · 发现**：Host 以 1 Hz 重播 `_eink-panel._tcp`；设备约 1 s 监听窗口内可发现。
- **已验收 · 计数**：固件 `round2-r6-3`（及 `round2-r3d-1`）在整屏刷新完成后累加 NVS 计数并
  上报 `refresh_count`；304 不增加；每次启动首个被接受帧计一次；真机计数连续验证
  （R7A 收尾与 R3D 验收见 `PROJECT_STATE.md`）。
- **已验收 · 配网**：长按 S1/KEY1 约 2 s 进入 `eink-panel-setup`（192.168.4.1），
  `POST /configure` 试连成功才保存；R3D 起最多保存 3 组网络（`networks`，301 B），
  配网页可新增/更新/忘记，启动按上次成功优先选择（真机 PASS，见 M2 PARTIAL 收口）。
- **已验收 · 页面仓**：`data/pages/*.json`（gitignored）+ 原子写；`progress` 为事件页，
  `memo`/`course`/`takeout` 可编辑，`weather`/`calendar`/`codex`/`pet` 只读；选页持久化。
- **已验收 · 页面**：Progress、Memo、Course、Weather（四城）、Calendar、Codex、外卖、宠物。
- **已验收 · 远程**：R7A 软件 PASS（`--remote` 双监听）；Serve + HTTPS 后端 PASS；
  手机 A3 PASS（蜂窝、Serve/HTTPS、切页/保存/预览；Host 与设备在手机热点内，外网穿越未测）；
  HTTPS 源 PWA 安装 PASS（2026-11-10，见 M6）；非 tailnet 外网穿越未测，部署仍 PARTIAL。
- **已验收 · 测试基线**：Python 697 passed、前端 62 passed（最近一次全绿；计数只能升不能降）。
- **发布收口**：`v0.5.0-round2-stable`（2026-11-10）：`origin/main` 由 `4e0e55e` 快进到发布提交，
  随后本地与远端一致；设备在线（`10.49.252.216`，`round2-r3d-ota1`，`refresh_count` 72）；
  BUSY B1–B11 仍阻塞。

## 3. 架构边界（不动的部分）

- 渲染留在 Host；设备只做「取帧—校验—显示—上报」。
- 帧契约、200/304、ETag、LKG、60 s 轮询、mDNS、OTA、配网流程不变。
- 新功能只改 Host 与 Web；任何页面都不改固件。
- 设备端时钟/本地数据/本地渲染/动画不在范围内。
- **唯一例外**：R3D「多网络接入」是当前被授权的固件增量，范围仅限 Wi-Fi 凭据存储与
  网络选择逻辑；不得借机改帧契约、OTA、显示链或引入设备端业务逻辑。
  其余任何固件改动需另立项目并重新评估架构。

## 4. 已完成基线与可修改窗口

### 4.1 已完成清单（默认冻结）

| ID | 增量 | 验收证据 | 冻结契约 |
| --- | --- | --- | --- |
| C01 | 帧渲染 + 设备显示（8 页） | `PROJECT_STATE.md` 各页 PASS 段 | 15,000 B、1-bit、MSB-first、SHA-256 ETag |
| C02 | 60 s 轮询 / 200→304 / LKG | 同上 | 轮询周期、304 语义、stale 标记 |
| C03 | mDNS `_eink-panel._tcp` 1 Hz | R1/R2 段 | 服务名、1 Hz 重播 |
| C04 | 配网（S1 长按 2 s → AP → `/configure`） | R3B 段 | AP 名、试连成功才保存 |
| C05 | 页面仓 + 原子写 + 选页持久化 | R3A/P1 段 | `data/pages/*.json`、revision |
| C06 | 天气四城（P1/P8） | `docs/WEATHER.md` | 四城集合、整点批量、失败 LKG |
| C07 | 日历（P2） | `PROJECT_STATE.md` P2 段 | 自算农历/节气、无调休数据 |
| C08 | Codex 用量（P3） | `PROJECT_STATE.md` P3 段 | 真实同步、15 min stale |
| C09 | Memo/Course 增强（P4） | `docs/MEMO-COURSE.md` | 日级语义、无 emoji、固定 5 节次 |
| C10 | 外卖（P5） | `docs/TAKEOUT.md` | ≤6 单、状态只前进、自动超时 |
| C11 | PWA / WebView 壳（P6） | `docs/P6-WEBVIEW-SHELL.md` | 单地址栏壳、LAN 下 PWA 不可安装 |
| C12 | 宠物静态页（P7） | `docs/PET.md` | 每日衰减、三种互动、无动画 |
| C13 | R0–R5 主线（观测/发现/配网/本地 Web/移动入口） | `PROJECT_STATE.md` R0–R5 | 各阶段冻结契约 |
| C14 | R7A 远程访问（软件 + Serve/HTTPS + 手机 A3） | `docs/R7-REMOTE-ACCESS.md` | 双监听、仅 loopback 代理、无 Funnel；手机侧热点内直连 |
| C15 | 测试基线 697 Python / 57 前端 | 最近一次全绿输出 | 计数只升不降 |

### 4.2 不可动（改动必须先升级为新的阶段）

- 帧字节布局与 ETag 算法。
- NVS 分区表；键名 `eink-wifi` / `validated`（R3D 迁移除外，且必须向后兼容、不擦 NVS）。
- OTA 保持关闭的现状与"显示调用期间不刷写"约束。
- 设备端零业务逻辑、零本地业务数据、零动画。

### 4.3 Reopen 协议（已验收项的可修改窗口）

已完成项**默认冻结**，但保留三个正式窗口：

- **W1 文档/口径**：只改本文件或 `PROJECT_STATE.md` 的措辞、编号、指针 →
  无需真机；跑相关自动化即可。
- **W2 Host/Web 行为**：改代码或渲染 → 必须 TDD；`/manage` 预览 PNG 与设备帧
  SHA-256 一致；真机 200→304；内容变化时计数恰好 +1；`PROJECT_STATE.md` 追加一段。
- **W3 固件/帧契约/NVS**：先写 spec + plan（`docs/superpowers/`），列明回滚镜像
  与"不擦 NVS"约束，单独授权刷机；禁止与其它增量同批。

每次重开在 §12 追加一行：`REOPENED Cxx — 原因 — 影响测试/证据 — 结论`。
禁止在别的增量里"顺手改"已验收项。

## 5. 未完成主线（只列未完成项，按顺序单独立项）

| 阶段 | 范围 | 退出条件 | 依赖 |
| --- | --- | --- | --- |
| **M1**（已完成 2026-11-09） | 恢复设备可达 + R7B 手机蜂窝验收 + 手机端"读取中"诊断 | 设备回到 Host 同网并 200→304；手机蜂窝打开 `/manage` 出现 `/api` 请求、可切页/存 Memo、预览一致、`remote-manage.png` 落盘 | 需恢复网络（热点或重新配网） |
| **M2**（2026-11-10 以 PARTIAL 收口） | **R3D 多网络接入**（唯一固件例外，见 §6） | 已真机 PASS：迁移、保存 ≥2 组、同 SSID 更新、启动选择、`200 → 304` 与计数、忘记后回落并恢复轮询、日志无口令、NVS/RAM 预算。仍开放：关闭当前 AP 的实时切换（**BLOCKED**：无第二个可控 AP）、409 满存（**NOT RUN**：只有两组网络）、旧镜像回滚（**NOT RUN**：需单独刷机授权） | 设备在线；spec+plan 已批准；刷机已单独授权 |
| **M3**（2026-11-10 完成） | R6 残余：物理故障注入/回滚（含 `round2-r6-3` 回滚镜像）、OTA 后 Android 壳检查、CXX_RUNTIME 口径、单次刷新耗时实测 | 单次刷新 **PASS**（2.184 s）；OTA 端到端 **PASS**；坏镜像与传输中断 **PASS**；CXX_RUNTIME 口径已记录（NOT RUN）；OTA 后手机壳 **PASS**；`round2-r6-3` 回滚 **PASS**（USB 刷入后 200→304，计数 71；再用 OTA 恢复 `round2-r3d-ota1`，计数 72） | 设备在线；已授权刷机 |
| **M4** | BUSY B1–B11（B0 已 PASS） | 按 `docs/BUSY-HARDWARE-BOM.md` 采购到位后逐项注入 | 器材依赖，允许长期阻塞 |
| **M5**（2026-11-10 完成） | 发布收口：本地提交与 `origin/main` 对齐、版本标记 | 推送 / 打 tag（**已单独授权**）：`origin/main` 由 `4e0e55e` 快进到发布提交，annotated tag `v0.5.0-round2-stable` | 明确授权 |
| **M6** | 可选/待裁定：横屏/输入法、旧文档"本地时间"口径核对；非 Progress 页时身份卡显示 `未通信` 的口径修正（**2026-11-10 完成**）；PWA 在 HTTPS 源安装（**2026-11-10 完成**）；页面边界态的无帧/无源口径（**2026-11-10 完成**） | 每项独立小增量，各自验收 | 用户点选 |

### M1 执行顺序

1. **恢复 Host 网络**：确认当前 WLAN IPv4（现为 `192.168.0.200`）；重启 Host 时显式
   指定该地址并加 `--remote`，确认两个监听都在且 PID 一致（旧进程仍绑定已消失的
   `10.127.70.75`）。
2. **设备回到可达**：优先重开热点（设备已存热点凭据，无需配网）；否则长按 S1 →
   `eink-panel-setup` → `/configure` 保存当前 WLAN。记录设备新 IP 与刷新计数基线。
3. **LAN 验证**：`/manage` 200；帧 200 → 304；计数只 +1。
4. **手机 A3**：关 Wi-Fi，蜂窝打开 `https://<host>.<tailnet>.ts.net/manage`。
   - 若仍停在"读取中"：按 `superpowers:systematic-debugging` 定位（静态资源路径 /
     ES module / 浏览器 JS 限制 / API base），留一次最小证据（控制台错误、请求列表）。
   - 前端缺陷 → TDD 修复，前端测试全绿后重跑 A3；浏览器限制 → 换 Chrome 复测，
     并在 runbook 写清"支持的浏览器"。
5. **收口**：证据写入 `D:/Codex/round2-r7-20261108/acceptance/`（新增
   `remote-manage.png`），`PROJECT_STATE.md` 追加 A3 手机侧结果，
   `NEXT_REQUIRED_STAGE = R3D`。

## 6. R3D 多网络接入（目标约束，不是实现规格）

**要什么**

- 保存 N 组（建议 N=3）已试连成功的凭据；开机/断线时按"上次成功优先，其次存储顺序"
  自动尝试；每组沿用 15 s 超时，总尝试预算 ≤45 s，之后保留 LKG 画面。
- 配网页支持"新增/更新一组"并列出已存网络；不覆盖其它组。
- 兼容旧数据：把既有 `validated` 读取为第 1 组，键名可读；不擦 NVS、不改分区。

**不要什么**

- 不同时运行 AP+STA；不做云端同步；不改帧契约、OTA、显示链。
- 不在日志中输出口令；证据中 SSID 打码；配网页不回显口令。

**约束**

- 单 blob 改为定长数组，无动态分配；候选连接前 `server_.stop()` 的既有顺序不得回退。
- 同一时刻只有一个活动网络。

**验收**

- 两组网络实测切换；ETag/200→304/计数正常；NVS、free heap、flash 数字入档；
  旧镜像可回滚；`tests/cpp` 的 static_assert / 选择顺序 / 迁移测试全绿。

## 7. 统一验收门（每项增量同一张清单）

1. 模型 `extra="forbid"` 且有明确上限；同输入渲染字节确定（无隐藏时间/随机）。
2. `/manage` 可编辑、可预览；预览 PNG 与设备帧 SHA-256 一致。
3. 真机：切页后 ≤2 个轮询内 `200` + 15,000 B + 固定格式 + ETag=SHA-256；下一轮 `304`；
   内容变化计数只 +1；旧 ETag 返回 409。
4. 数据源失败：返回 LKG 帧并标 stale，不发布残缺帧。
5. Python 与前端测试全绿；证据与 `PROJECT_STATE.md` 追加。
6. 无凭据入日志；不改 NVS/分区；页面开发不刷机。
7. **固件增量附加**：两套 env 均编译（`esp32-m1-network-progress`、`-ota`）；
   刷机前确认凭据不入库；刷机后先验 200→304 再验新功能；失败可回滚；记录 RAM/NVS 占用。

## 8. 可持续规则

- 一次一项；一个提交集只含一项，可整体 revert。
- 内容变化 ≤1 次/分钟；不做动画或分钟级倒计时（FULL 刷新约 2.2 s，计数 +1）。
- 每项以「预览 + 真机 + 证据文档」结束；超过 2 个会话就砍范围或拆分。
- 外部依赖失败不阻塞主线：LKG + stale 是页面的一等状态。
- 已完成项默认冻结（§4.3）；任何网络/固件变更后必须重新验证"设备 200→304 + 计数"。

## 9. 成功指标（v1.1 完成定义）

- 8 页均可选、均在真机出现 `200→304`，切页 ≤2 个轮询。
- 天气断网保留上一帧并标 stale；日历 3 个含节气/节假日日期正确。
- Codex 数字来自真实同步。
- **两组 Wi-Fi 自动切换实测通过**，不重新配网。
- 两套测试全绿；每项在 `PROJECT_STATE.md` 有 PASS 段；本地与 `origin/main` 一致（经授权）。

## 10. 风险与对策

| 风险 | 对策 |
| --- | --- |
| 天气源变更/证书问题 | 单一源 + 超时 + LKG；失败只标 stale |
| 农历/节气算法错误 | 固定测试日期（春节、闰月、节气、中秋/除夕） |
| Codex 数据源不可用 | 同步失败保留上一帧；15 min 未更新标 STALE |
| e-ink 刷新代价被低估 | 频率上限写进验收门；拒绝动画/分钟级倒计时 |
| 范围膨胀 | 一次一项；超 2 个会话即拆分 |
| 多网络凭据撑爆 NVS / 堆 | N=3 定长、先算预算、静态分配、记录 free heap |
| 新增凭据泄露到日志/截图 | 口令永不落日志；证据中 SSID 打码；配网页不回显口令 |
| 网络切换失败导致设备"消失" | 总尝试预算 + LKG + 保留旧凭据；验收必须含回滚镜像 |
| 设备端功能期待 | §3 即答复：R3D 之外不改固件 |

## 11. 下一个动作

**M2 — R3D 多网络接入：2026-11-10 以 PARTIAL 收口。** spec、plan 与实现均已落地
（`b619271` spec、`df8ffb4` plan、代码 `df8ffb4..95848a2`）；构建标识 `round2-r3d-1`，
两套 env 编译 exit 0（RAM 71,576 B，flash 875,357 / 875,193 B），4 个 C++ harness
`-fsyntax-only` exit 0，Python 697 passed，前端 57 pass / 0 fail。经单独授权刷机后，真机
**PASS**：旧 `validated` 迁移、新增第二组网络（2 行）、同 SSID 原位更新（仍 1 行）、
启动按上次成功选择（5 次重启）、`200 → 304`、计数仅在内容变化与每次启动首帧 +1
（57 → 59 → 60 → 61 → 62 → 63）、忘记后重置并回到剩余网络继续轮询、串口/Host 日志无口令、
`NETWORK_WIFI_STORE=301` 与 NVS 预算入档。**仍开放**：关闭当前 AP 的实时切换记为
**BLOCKED**（没有第二个可控 AP；第二组是移动 Wi-Fi，Host 到其客户端不可达，而第一组是
Host 自己的上行）；409 满存 **NOT RUN**（只有两组网络）；`round2-r6-3` 回滚 **NOT RUN**
（需单独刷机授权，见 M3）。证据：`D:/Codex/round2-r3d-20261109/acceptance/`，操作手册
`docs/R3D-MULTI-NETWORK.md`。当前设备 `10.49.252.216`、`refresh_count` 63。

**下一步 = M3（R6 残余）**：物理故障注入/回滚（含 `round2-r6-3` 回滚镜像）、OTA 后
Android 壳检查、CXX_RUNTIME 口径、单次刷新耗时实测。2026-11-10 在授权范围内完成：单次整屏
刷新 **2.184 s**（两次一致；HTTP 连接→流程完成 3 s）、CXX_RUNTIME 口径（无宿主编译器，
运行时断言 **NOT RUN**）、OTA 端到端 **PASS**（10 s 传输、120 s 后 VALIDATED、NVS 凭据保留）、
坏镜像 **PASS**（`FAILURE=10`，不重启、不刷新）、传输中断 **PASS**（Host 在 0.5 s 处被杀，
4 s 后 `FAILURE=10`，保留原镜像）、OTA 后手机壳 **PASS**（`/manage` 与全部静态资源 200，
经壳切到备忘录再切回外卖，设备计数 68 → 70）、`round2-r6-3` 回滚 **PASS**（`9636407` 构建、
USB 刷入后 200→304，计数 71；再用 OTA 恢复 `round2-r3d-ota1`，计数 72，VALIDATED）。
设备现为 `round2-r3d-ota1`。**M3 完成。** 下一步：M4（BUSY B1–B11）受器材阻塞；M5
（本地与 `origin/main` 对齐、打 tag）需明确推送授权。证据：`D:/Codex/round2-m3-20261110/`。

**M6 已完成一项（2026-11-10）**：`/manage` 身份卡此前读的是 Progress 专用状态，切到
memo/course/takeout 等页后设备字段显示 `未通信`；现改读 `/api/pages/status`（当前页的
`source`、`frame_format`、`device.firmware_version`、`device.last_seen`），读取失败统一显示
`UNKNOWN`。前端 60 pass / 0 fail（新增 3 条 `identityFields` 用例）；以真机当前页 takeout
的实时响应核对字段。浏览器可视化复检 **NOT RUN**（本会话没有可用的浏览器连接器），
以单元测试 + 实时接口返回值代替。

**M6 再完成一项（2026-11-10）**：HTTPS 源 PWA 安装 **PASS**。Tailscale Serve（443 →
loopback，tailnet 内）下所有 PWA 端点 200 且 MIME 正确；无头 Chrome 的
`Page.getInstallabilityErrors` 返回空数组，manifest 无解析错误，Service Worker 已
`activated` 且 scope `/`；手机在 HTTPS 源上看到“安装到主屏”按钮**自动出现**并完成安装
（`beforeinstallprompt`，操作者确认），Host 访问日志出现对应的 `/manage`、manifest、图标与
`/sw.js` 请求。安装后的独立/离线启动未单独观测；非 tailnet 外网路径仍未测。

**M6 再完成一项（2026-11-10）**：页面边界态（无帧/无源）的口径修正。此前当前页卡在没有帧时
一律显示“等待设备取帧”，Progress 未配置发布源时也一样；现区分
`active` / `pending` / `no-frame` / `unknown`，并按页给出
“Host 已提供当前帧”“等待切换”“该页暂无帧”“未配置发布源，暂无帧”（错误色）与
“等待发布事件”。前端 62 pass / 0 fail，Python 697 passed；设备未切换。M6 其余可选项
（横屏/输入法、旧文档口径）仍未点选。

**M5 完成（2026-11-10）**：按单独授权把本地 `main` 从 `4e0e55e` 快进推送到 `origin/main`，
并以 annotated tag `v0.5.0-round2-stable` 标记本轮收口。发布内容 = R7A/R7B + 八页 + PWA +
R3D 多网络 + LAN OTA + M3 残余；软件门 Python 697、前端 60、4 个 C++ harness
`-fsyntax-only` 与两套固件 env 的构建记录见 `PROJECT_STATE.md`。已知开放项：M2 failover
BLOCKED、设备端 409 与 M4 BUSY B1–B11 未运行/阻塞、HTTPS 源 PWA 安装当时未验证（后于
2026-11-10 完成，见 M6）。标签消息见 §12 的 M5 变更记录。

M1 结果：热点恢复后 Host 与设备重新同网（`10.127.70.75` / `10.127.70.216`），设备计数
51 → 56；手机在 Wi-Fi 关闭、蜂窝、Tailscale 在线的情况下经 Serve/HTTPS 完成
天气 → 备忘录 → 天气的切页、保存与草稿预览，A3 手机侧 PASS。备忘录已恢复为测试前内容。
证据在 `D:/Codex/round2-r7-20261108/acceptance/`（含打码截图与 `remote-phone.txt`）。

边界：Host 与设备当时都挂在手机热点下，Serve 路径为热点内直连，因此**外网穿越仍 NOT RUN**；
HTTPS 源上的 PWA 安装也未验证，故 DEPLOYMENT = PARTIAL。R3D 真机验收确认：设备只在
**关联失败**时切换网络；若已关联但 Host 不在该网，设备会留在该槽位并每 ≤60 s 重试
（2026-11-10 17:52–18:06 观测）。因此“Host 换网、设备自动跟随”不是现有行为；真正的跨网
验收需要可关闭的第二个 AP，或重新配网。

## 12. 变更记录

- `2026-11-09` 建立本文件，取代并删除 `docs/GOALS.md`；旧文件的 P1–P8 / R0–R7A
  内容转入 §4 冻结基线，旧 §11 的已完成日志不再作为主线依据。
- `2026-11-09` M1 关闭：热点恢复后设备重新轮询（计数 51 → 56），手机 A3 手机侧 PASS
  （Wi-Fi 关、蜂窝、Serve/HTTPS；热点内直连，外网穿越 NOT RUN）；备忘录已恢复；
  下一步为 M2 / R3D，需先写 spec 与 plan。
- `2026-11-09` 新增 M2 / R3D「多网络接入」：设备可保存并自动切换多组 Wi-Fi，
  作为唯一被授权的固件增量（§3、§6）。
- `2026-11-09` R3D 多网络软件部分完成（`df8ffb4..95848a2`，10 个提交，6 个文件）：三槽
  301 B 存储、上次成功优先的选择顺序、`validated` 一次性迁移、配网页新增/忘记、409 满存、
  `WifiConnect` 内三次 15 s 尝试（≤45 s）。软件门 PASS：两套 env 编译 exit 0、RAM 71,576 B、
  flash 875,357 / 875,193 B、4 个 harness `-fsyntax-only` exit 0、Python 697、前端 57。
  **未刷机**：设备验收全部 NOT RUN，M2 在拿到真机证据前保持未完成；DEPLOYMENT 仍为 PARTIAL。
- `2026-11-09` R3D 文档交接修正：构建标识改为 `round2-r3d-1`（此前镜像会回报过期默认
  `round2-r6-1`），RAM/flash 数字重测后不变；运行手册修正 `/api/pages/status` 的字段范围、
  `refresh_count` 语义（每次启动首个被接受帧必刷新一次）、忘记后的停留状态、Host 可达前置
  条件、迁移与失败路径措辞、409 后的重开页面，以及回滚镜像 `round2-r6-3`（`9636407`）
  的获取方式；deferred minors 计数 20 → 29。
- `2026-11-10` M2 / R3D 以 **PARTIAL** 收口：经单独授权刷机 `round2-r3d-1` 后，真机 PASS
  迁移、两组网络新增/原位更新、启动选择、`200 → 304` 与计数语义、忘记后回到剩余网络并恢复
  轮询、预算与无口令日志；关闭当前 AP 的实时切换记为 BLOCKED，409 满存与回滚镜像 NOT RUN。
  同次验收确认“已关联但 Host 不可达不会触发换网”的设计行为（17:52–18:06），并记录
  `stopSoftAP()` 失败会停在配网态的运维注意项。证据
  `D:/Codex/round2-r3d-20261109/acceptance/`；下一步为 M3。
- `2026-11-10` M3 已做两项：单次整屏刷新 2.184 s（两次整数一致，HTTP 连接→流程完成 3 s，
  切页在下一轮轮询生效，304 不刷新），以及 CXX_RUNTIME 口径（无宿主编译器；编译期
  `static_assert` 执行，运行时断言 NOT RUN）。故障注入、OTA 后 Android 壳检查与
  `round2-r6-3` 回滚仍需单独刷机授权；证据 `D:/Codex/round2-m3-20261110/`。
- `2026-11-10` M3 授权范围内 OTA 验收完成：OTA 端到端 PASS（`round2-r3d-ota1`，10 s 传输、
  120 s 后 VALIDATED、NVS 凭据保留）、坏镜像 PASS（`FAILURE=10`，保留原镜像与画面）、
  传输中断 PASS（Host 0.5 s 处被杀，4 s 后 `FAILURE=10`，无重启）。设备现为
  `round2-r3d-ota1`。手机侧 Android 壳检查（NOT RUN）与 `round2-r6-3` 回滚（未授权）仍开放。
- `2026-11-10` M3 手机壳检查 PASS：P6 壳从手机加载 `/manage` 与全部静态资源（200），经壳切到
  备忘录再切回外卖，两次预览均 200，设备取到两帧 200，计数 68 → 70。M3 只剩
  `round2-r6-3` 回滚刷机（未授权）。
- `2026-11-10` M3 完成：`round2-r6-3` 在 `9636407` 构建并 USB 刷入，启动保留计数 70，重新配网
  到 net-a 后 200→304（计数 71）；随后用 OTA 恢复 `round2-r3d-ota1`（计数 72，120 s 后
  VALIDATED）。发现的边界：旧镜像的 `validated` 是“最后配网成功”的网络，不是“最后可用”；
  若该网络已被忘记且 Host 不可加入（net-b 对 Windows 不可见），回滚后必须先重新配网。
- 备注：`docs/superpowers/plans/2026-11-08-r7-remote-access.md` 与
  `docs/superpowers/specs/2026-11-08-r7-remote-access-design.md` 中引用的
  `docs/GOALS.md` 属历史归档，不再维护，也不改写过往提交。
- `2026-11-10` M6 小项完成：`/manage` 身份卡改读 `/api/pages/status`，非 Progress 页不再误显
  `未通信`；新增 3 条前端用例（共 60 pass / 0 fail）。浏览器可视化复检 NOT RUN（无浏览器
  连接器），以实时接口返回值核对。
- `2026-11-10` M5 完成：经单独授权把 `origin/main` 从 `4e0e55e` 快进到发布提交，并打
  annotated tag `v0.5.0-round2-stable`；发布前复跑 Python 697 passed、前端 60 pass。标签
  覆盖 R7A/R7B、八页、PWA、R3D 多网络、LAN OTA 与 M3 残余；开放项 M2 failover BLOCKED、
  设备端 409 NOT RUN、M4 BUSY 阻塞、HTTPS 源 PWA 安装 NOT RUN。
- `2026-11-10` M6 HTTPS 源 PWA 安装 **PASS**：Tailscale Serve（443 → loopback）下
  `/manage`、manifest、`/sw.js`、两枚图标与状态 API 均 200 且 MIME 正确；无头 Chrome 的
  `Page.getInstallabilityErrors` 为空、manifest 无解析错误、SW 已 `activated` 且控制页面；
  手机在 HTTPS 源上看到“安装到主屏”按钮自动出现并完成安装（操作者确认），Host 访问日志
  出现对应请求。安装后的独立/离线启动未单独观测；非 tailnet 外网路径未测。
- `2026-11-10` M6 页面边界态（无帧/无源）完成：当前页卡不再一律显示“等待设备取帧”，改为
  `active` / `pending` / `no-frame` / `unknown` 四态，并按页区分“该页暂无帧”“未配置发布源，
  暂无帧”（错误色）与“等待发布事件”；样式选择器同步为 `data-state="no-frame"`。前端 62
  pass、Python 697 passed；设备未切换，浏览器截图 NOT RUN（无连接器）。
