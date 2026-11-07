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

# R2A Host Discovery Software Contract

目标：在现有 HTTP 链路之前解析 Host IPv4 + port，保留配置地址作为唯一 fallback。
本节是 R1B checkpoint `7ca5027f7d719caa4f2ecb4bf83fdeef998ad67b` 之后的 R2A 结果；
上节的 NOT RUN / NOT STARTED 是 R1A 当时的历史状态。

冻结一个 DNS-SD 服务类型 `_eink-panel._tcp.local.`，实例
`eink-panel._eink-panel._tcp.local.`，SRV target `eink-panel.local.`。
`eink-panel` 符合 [RFC 6335 service-name syntax](https://www.rfc-editor.org/rfc/rfc6335.html#section-5.1)，
名称也通过实际 zeroconf ServiceInfo 校验。仅供当前可信 LAN 单 Host 使用；服务身份不是认证。

Host 的 LAN 启动入口是 `python -m server.main --host <LAN-IPv4> --port 8000`。
明确的 IPv4 bind 和 HTTP port 同时供 Uvicorn 与 advertisement 使用，端口只有一个来源；
可更改 --port，广告 SRV port 同步。直接复用 `zeroconf==0.151.5`，只在该 IPv4 接口注册
固定实例，禁止自动改名。FastAPI lifespan 启动注册、关闭注销并释放对象；注册失败释放
资源，接口不可用或名称冲突不阻止原 HTTP 服务。advertisement 不调用 renderer 或改动
event/frame/status API。默认 loopback 启动保持 127.0.0.1:8000，不发布 LAN 广告。
直接 `uvicorn server.main:app` 未提供此入口的 bind 数据，不发布广告；不猜测 CLI 端口。

ESP32 复用当前 framework 内置 Espressif mDNS API。Wi-Fi 已连接后、每轮现有 frame
HTTP 事务开始前，只执行一次 `_eink-panel` / `_tcp` PTR 查询，预算 1000 ms。
只接受一个固定实例的合法 IPv4 + 1..65535 port；无结果、初始化/查询失败、身份不符、
无 IPv4、非法 endpoint 或多结果均使用原 `NETWORK_HOST_IPV4` / `NETWORK_HOST_PORT`。
不做多 Host 仲裁。查询结果与 mDNS 资源使用后释放，无持久化或 endpoint 历史。

resolver 返回 `ResolvedHost {address, port, source}`，source 仅有 DISCOVERED 或
CONFIGURED_FALLBACK，保留在 resolver 层，不扩充产品状态 schema。本轮选定 endpoint
供既有 SocketOwner、frame GET Host header 和 DeviceReporter POST 一起使用；报告期间
不重新 discovery。下一次原有轮询再查询，使软件可以接受变化后的地址和端口。
discovery 不消耗原 HTTP/TCP 事务预算。选定 endpoint 的 HTTP 失败沿用原 FailureWait，
不追加另一轮 HTTP fallback。Wi-Fi 配置/连接、长度/格式/SHA/ETag/200/304/LKG、
标准 FULL display 和 R1A publication 状态语义保持既有逻辑。

R2A acceptance：13 个新增 Python 契约测试 PASS，完整回归 393/393 PASS；
esp32-m1-network-progress build PASS。新增 C++ harness 覆盖两种 endpoint 来源、同一 HTTP
machine、来源切换下的 304、截断/SHA/格式/多余字节拒绝、LKG、报告 endpoint 及 resolver
无显示职责；CXX_COMPILE_CHECK = PASS，CXX_RUNTIME = NOT RUN，不将编译当执行。
所有 Python advertisement 和 listener 操作均 mock，无实际 mDNS 广告或 LAN discovery。
REAL_LAN_DISCOVERY / PHYSICAL_VALIDATION = NOT RUN；R2B = NOT STARTED；R3 = NOT STARTED。
ROUND2_R2A = PASS；NEXT_REQUIRED_STAGE = R2B，等待单独授权。本请求停止于 R2A checkpoint。


# R3A Wi-Fi Provisioning Software Contract

目标：以现有 Arduino-ESP32 2.0.17 的 WiFi、SoftAP、WebServer 和 Preferences/NVS
完成最小配网软件契约，不引入依赖。此节位于 R2B checkpoint
`a80be902e7ddddee975f7306af7dba50f6d98ef8` 之后；此前阶段状态保留为历史。

凭据优先级：有效的 persisted validated credentials → 现有 configured credentials。
启动继续使用原 WifiInit/WifiConnect 路径；连接失败沿用既有 FailureWait，
Wi-Fi、Host discovery 或 HTTP 失败均不会自动打开配网。`WiFi.persistent(false)`
保留，候选连接本身不会写入 Arduino 的 Wi-Fi 配置存储。

当前没有已验证的按钮/GPIO 入口。唯一入口为显式调用
`Machine::requestProvisioning()`，只在初始化完成且处于 PollWait/FailureWait 的
空闲 socket 边界接受；Boot、HTTP/显示/报告进行中和 FaultStop 不接受。
R3A 不绑定 GPIO、串口命令或启动条件；实际用户触发映射留到 R3B。

内部状态为 NORMAL_CONNECT、PROVISIONING、CANDIDATE_CONNECT、CONNECTED。
配网会话开启 `eink-panel-setup` 开放 SoftAP，保留 STA 能力；本地 HTTP 仅绑定
AP 的默认地址 192.168.4.1:80。GET `/` 提供 SSID/password form 和简单结果，
POST `/configure` 接收这两个字段；有效提交返回 202，非法/正在连接返回 400。
无扫描、DNS captive portal、JS framework 或产品管理 UI。

SSID 为 1..32 bytes；password 为空或 8..63 bytes，64 bytes 必须为十六进制 PSK。
提交后先断开旧关联，再发起一次候选连接。`kCandidateWifiTimeoutMs = 15000`，
从提交开始计时；无自动候选重试。成功仅要求 framework 的 WL_CONNECTED、非零
STA IP 和候选 SSID 匹配，不要求 Host、frame 或互联网在线。
固定 SDK 的 begin() 可能保留旧失败状态；未变化的旧失败状态等待有界 timeout，
不被当作本次立即失败。候选结果只分 TIMEOUT / CONNECT_FAILED；存储/AP 错误
只作为本地操作结果，不扩展 Host 状态 schema。

不变式：只有候选连接成功后才调用 Preferences 保存。仅保存当前 SSID/password
的一个 blob：namespace `eink-wifi`、key `validated`，不建历史或多网络列表。
候选失败/超时不保存、不覆盖旧有效凭据，返回 PROVISIONING，保留 SoftAP 供再次
显式提交；保存失败也不进入 R2。成功保存后关闭 AP/HTTP，进入 CONNECTED，再由
原 Machine 的 HostResolve → 原 R2 resolver → 原 HTTP/frame pipeline 接续。
关闭 AP 使用 `WiFi.enableAP(false)` 保留 STA；避开当前 SDK
softAPdisconnect(true) 对 bool 与 ESP_OK 比较造成的返回值反转。
若关闭 AP 失败，不交付 R2，显示本地错误；成功验证并保存的凭据仍为当前有效值。
下次 load/new instance 优先选取已保存候选。没有自动 reboot、NVS erase 或真实迁移。

R3A acceptance：23 项 production-controller C++17 static_assert 契约检查 PASS；
network harness 中新增显式入口/原 HostResolve/200/304/隔离断言编译 PASS，
CXX_RUNTIME = NOT RUN。完整 Python 回归 393/393 PASS，目标
esp32-m1-network-progress build PASS。软件与构建结果详见 PROJECT_STATE.md 第 28 节。
Host/render/event/frame/SHA/ETag/display/R1 report/R2 resolver 逻辑保持既有实现。
开放 AP 的 production security hardening 是未来范围，此阶段不实现安全子系统。
REAL_SOFTAP / REAL_WIFI_SWITCH / REAL_PERSISTENCE_REBOOT / PHYSICAL_VALIDATION = NOT RUN。
R3B = NOT RUN / NOT STARTED；R3C = NOT RUN / NOT STARTED。
ROUND2_R3A = PASS；NEXT_REQUIRED_STAGE = R3B，必须另行授权；本请求停止于 R3A。


# R3A.1 Physical Provisioning Trigger Binding

本节只绑定 R3A 已有 requestProvisioning()；R3A 的软件结果与此前 R3B 触发门禁
BLOCKED 记录保留为历史。基线为 `0dbbe5d4083896ee55c53278c25386cb6ca3504a`。

TRIGGER_TYPE = 当前 ESP32-M1 的板载 KEY 自定义按钮 S1。
TRIGGER_GPIO = 25；原理图 MCU 分区 S1 pin2 → KEY1 → U5 IO25 / 模组 pin10，
S1 pin1/3 接地。说明书 PDF 第5页图1条目⑦与 E13 实物照片互相印证；原始文件
SHA-256 与 STEP013_EVIDENCE_MANIFEST 一致。GPIO25 不在现有显示 12/13/14/18/23/27
或 Flash/strapping 引脚中，未被当前产品使用；不借用 BOOT/RST 或新增接线。
GPIO25 的数字输入能力见 [Espressif 模组资料](https://documentation.espressif.com/esp32-wroom-32d_esp32-wroom-32u_datasheet_en.html)
§2、§3、§4.2.1；本项目固定框架的 INPUT_PULLUP/digitalRead 直接使用 GPIO 输入，
没有 ADC2/DAC 操作。安全性结论来自线路/框架源代码，真实按键读取尚未执行。

TRIGGER_GESTURE = 初始化成功后先观察释放，再稳定长按 2000 ms。
去抖稳定窗口固定 30 ms；GPIO 使用 INPUT_PULLUP，按下 LOW。仅首次进入原
WifiConnect 后配置该输入，初始化失败不启用；跨启动持续按住必须先释放再长按。
ONE_PRESS_ONE_REQUEST = YES：同一次连续按住最多请求一次，稳定释放后重新允许
触发。原请求拒绝不自动重试；新请求仍需新的有效长按。

SAFE_STATES = 初始化完成后的 PollWait / FailureWait。其他事务状态只记一个 pending
标志，不中断 Wi-Fi、discovery、HTTP/frame、display、device-report 或候选配网。
pending 在下一允许边界清除并调用原 Machine::requestProvisioning()；没有队列。
FaultStop 不读取按钮或调度请求。无按钮时保持原启动/轮询路径。

R3A_CORE_CHANGED = NO：machine.h、credentials/NVS、SoftAP SSID/mode/routes、
15000 ms candidate timeout/validation、成功后保存/失败保留及 HostResolve 未修改。
无串口/USB/HTTP/Host/mDNS/BLE/cloud trigger 或连接失败自动触发。

R3A.1 acceptance：20 项 production-helper C++17 static_assert 检查 PASS；包含
未按/短按/抖动/有效长按/连续保持/稳定释放、两个安全状态、事务 pending、
初始化失败/跨启动保持及 FaultStop。实际 Machine 的两种安全边界集成断言编译 PASS，
未执行 native runtime；完整 Python 393/393 PASS，目标 firmware build PASS。
CXX_RUNTIME / REAL_TRIGGER_VALIDATION / REAL_SOFTAP / REAL_WIFI_SWITCH = NOT RUN。
ROUND2_R3A1 = PASS；R3B = NOT STARTED（本轮无真实验收）；R3C = NOT STARTED。
NEXT_REQUIRED_STAGE = R3B，必须以新 checkpoint 另行授权；本轮在 R3A.1 停止。
