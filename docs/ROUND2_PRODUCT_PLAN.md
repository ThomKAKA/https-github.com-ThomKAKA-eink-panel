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
