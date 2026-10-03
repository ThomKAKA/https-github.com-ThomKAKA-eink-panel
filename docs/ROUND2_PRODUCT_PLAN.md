# Round 2 North Star

LAN-first Personal E-Ink Terminal

保留 STEP016/STEP017 已验证链路。最终用户无需重新编译固件、无需 USB、
无需命令行、无需知道 PC IP，只用手机或电脑浏览器即可找到并识别自己的设备，
查看连接与软件状态，编辑 Progress，查看真实 400×300 预览，发布并查看实际阶段结果。

# Frozen Product Kernel

以下能力不得因 Round 2 随意重写：

- 400×300 monochrome frame：1-bit、15000 字节、stride 50、MSB-first、0 黑 1 白。
- Host-side rendering：复用现有 Python ProgressPanel/Pillow；浏览器/PWA 调用 Host
  实际渲染能力，不另建前端像素渲染器。保留 L → T → P 的既有方向契约。
- Progress physical product scope：实体产品范围继续仅为 Progress；既有物理验收边界不扩大。
- Existing event → frame chain：复用 FastAPI、事件/快照与完整帧发布 API。
- ESP32 pull model：保留 HTTP pull 与既有轮询模型。
- Existing frame validation：保留完整长度、格式、SHA-256、ETag 与 200/304 校验。
- Standard FULL display：复用 GDEY042T81 既有 H1 初始化、完整帧准备与标准 FULL 显示链。
- Last-valid-frame behavior：Host 渲染失败保留有效发布；设备网络/候选帧失败不请求显示，
  保留已接受身份与现有画面；显示拒绝或结果不明继续进入既有 FaultStop。

当前状态及验证证据以 [PROJECT_STATE.md](../PROJECT_STATE.md) 最新章节为权威来源；
本文件只定义 Round 2 产品契约与阶段顺序。既有协议和显示契约继续以 STEP016/STEP017
冻结文档、当前实现及已记录的验收修订为准。

# Round 2 User Loop

Browser/PWA
→ edit Progress
→ Host preview
→ publish
→ versioned frame
→ ESP32 fetch
→ validate
→ display
→ status

预览必须对应待发布的最终单色帧。状态必须区分 Host 发布、设备获取/校验和显示软件结果；
软件返回条件满足不能自动标为实体屏已验证。版本与阶段状态的具体契约留到 R1。

# Planned Stages

| Stage | Scope |
| --- | --- |
| R0 | Baseline freeze |
| R1 | Software observability / publication status |
| R2 | Host discovery |
| R3 | Wi-Fi provisioning |
| R4 | Local Web management |
| R5 | Mobile PWA |
| R6 | LAN OTA |
| R7 | Remote/cloud |
| R8 | Native App / BLE only if required |

阶段按顺序单独放行。R0 仅冻结基线和契约，不实现新功能；R1 是 R0 PASS 后的下一允许阶段，
本次不启动 R1 或任何后续阶段。

# Explicit Non-goals Now

- Cloud implementation
- Vercel deployment
- Native App
- BLE
- OTA implementation
- Stats/Flow physical productization
- Driver replacement
- Display redesign
- Partial refresh
- Speculative multi-device architecture

# Engineering Rule

Every stage must end with:

implementation
+ automated regression
+ build when relevant
+ runtime/physical evidence when relevant
+ PROJECT_STATE update

R0 的交付是基线与契约文档，不包含产品功能实现。复用当前 FastAPI、Python renderer、
event/frame API 与 PlatformIO 工程；只解决当前阶段问题，不做预测性抽象、大规模重构、
generic retry/fallback framework 或没有当前验收需求的兼容层，不因项目 Star 数替换工作组件。

No PASS may be inferred from code existence.

# R1A Software Observability Contract

现有事实：事件/快照已有 `event_id`；发布帧已有 SHA-256 strong ETag；R0 固件没有
版本声明或稳定设备身份，Host 没有设备状态接口。R1A 只补充以下单设备、单进程契约。

| Fact | Authoritative source / meaning |
| --- | --- |
| `publish_id` | 当前配置的 Progress source 最新已接受快照的 `event_id`；调用方沿用事件 ID 约定，不另建 sequence/UUID |
| `frame_version` | 现有 T 帧 ETag 去掉 HTTP 双引号后的 64 位小写 SHA-256；不增加 frame revision |
| `HOST_ACCEPTED` | 现有 EventStateStore 已接受当前 Progress 快照 |
| `FRAME_READY` | 现有发布器已为该快照真正生成并安装完整帧 |
| `DEVICE_FRAME_ACCEPTED` | 设备完成现有长度/格式/SHA/ETag/完整响应校验后的新帧观察 |
| `DEVICE_REFRESH_FLOW_COMPLETE` | 对应帧的既有标准 FULL 显示流程满足软件返回条件；不是物理显示确认 |

`GET /api/panels/progress/status` 返回 `publish_id`、`frame_version`、`host_stage`
以及 `device` 的 `last_seen`、`firmware_version`、`accepted_frame_version`、`refresh_stage`。
初始未知字段为 null。查询只读取事实，不触发渲染；渲染仍由原有 frame GET 按需触发。
新快照渲染失败时，状态保持 HOST_ACCEPTED、当前发布的 frame_version 为 null，
旧有效帧仍按 STEP017 提供；保留的设备观察不能算作新发布的完成证据。

`POST /api/panels/progress/device-report` 接受 `frame_version`、`firmware_version`
和 `refresh_stage`。固件版本声明为 `round2-r1a-1`，不代表该版本已部署。
Host 使用自身收件 UTC 时间记录 last_seen，不接受设备墙钟字段。
软件阶段报告只接受当前实际提供帧的哈希；完成报告必须已有同帧接受记录。
旧/未知帧或缺少接受记录返回 409；非法结构返回 422。重复报告不降低已完成阶段。
过时报告可以证明通信发生，但不能覆盖较新的 accepted_frame_version/refresh_stage。

设备对合法改变帧先报告 DEVICE_FRAME_ACCEPTED，再调用原有显示路径，只有正常软件返回
才报告 DEVICE_REFRESH_FLOW_COMPLETE。Host accepted_frame_version 表示设备报告的合法候选帧；
MCU 的既有 last-accepted ETag 仍只在显示软件条件满足后推进，两者不能混淆。
显示拒绝/结果不明保留既有 FaultStop，不报告完成。截断、坏 SHA、错误格式等拒绝路径不报告
帧接受/流程完成，也不推进既有 MCU accepted identity。

合法 304 或同身份 200 只发送 refresh_stage=null 的通信报告，更新 last_seen/固件版本；
不更新 Host accepted_frame_version/refresh_stage，不创建新接受或完成阶段，不调用显示。
frame GET 本身不充当设备确认。不同 publish_id 产生相同像素时沿用同一帧哈希和已有观察，
不能宣称该次发布引起了一次新的 FULL。

报告使用既有独占 socket owner，帧 HTTP 关闭后串行执行，每次最多一个 POST、总预算 3 秒。
普通报告失败不改变帧/显示资格，不补造 Host 成功状态，不重试或补发；完成报告缺失时保持未知。
socket 所有权/关闭失败仍按现有内部不变量进入 FaultStop。报告完成/失败后开始原有轮询等待，
报告耗时不缩短轮询间隔。没有新队列、event bus、数据库、retry/fallback framework。

状态随 Host 进程重启清空；只保留当前 source/当前设备观察，没有发布历史、配对或设备注册。
继续使用既有可信 LAN HTTP 边界；报告不是身份认证或独立物理证据。
Host/设备断联及报告丢失可导致阶段不完整，R1A 不承诺可靠投递或自动追补。
本阶段验证为进程内 API 自动测试与目标固件构建；真实 LAN/设备报告和实物证据留到 R1B。
physical display evidence = NOT RUN；R1B = NOT RUN；R2 = NOT STARTED。
