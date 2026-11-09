# R7 远程访问运行手册（Tailscale Serve）

日期：2026-11-08（状态更新于 2026-11-09）
依据：[R7 远程访问设计规格](superpowers/specs/2026-11-08-r7-remote-access-design.md)；
Host 侧 `--remote` 已实现并通过回归（697 Python / 57 前端）。
当前状态：**部署部分完成（PARTIAL）**。2026-11-09 已装 Tailscale 1.104.5 并以单台 Host
登录，管理台已开启 MagicDNS 与 HTTPS 证书，Serve 已按
`tailscale serve --bg --https=443 127.0.0.1:8000` 配置；从 Host 本机访问
`https://<host>.<tailnet>.ts.net/manage` 返回 200，证书校验通过（`ssl_verify_result 0`），
`/api/pages` 亦为 200。**A1/A2 已带真机验证 PASS**：设备本次地址 `10.127.70.216`
（旧 `10.21.98.216`，随 DHCP 变动），固件 round2-r6-3；默认启动（PID 19540）只有 LAN 监听，
`--remote`（PID 27876）双监听，设备取帧 200 后回 304，刷新计数 45→49。
**Serve/HTTPS 后端 PASS**：从 Host 经 HTTPS 完成切页、预览与 Memo 保存恢复。
**手机蜂窝 A3 NOT RUN**：本次没有第二台 tailnet 设备加入，`remote-manage.png` 未生成。
本文仍是操作步骤，不是 A3 的证据；只有第 9 节要求的证据文件真正生成后，才能声称远端验收通过。

目标：手机在蜂窝网络下打开 `https://<host>.<tailnet>.ts.net/manage` 管理同一台 Host。
设备（本次 `10.127.70.216`，旧 `10.21.98.216`）不装 Tailscale、不改固件，继续走 LAN。

## 1. 前提与审批

- 需要两次单独安装，各自取得操作者同意：Windows Host 一次、手机一次。
- 只允许这两个安装动作，以及管理台里打开 MagicDNS 与 HTTPS 证书。
- 不改防火墙：安装时 Windows 若弹出防火墙询问，先停手问清楚，不要顺手放行。
- 不碰公司 VPN：不卸载、不断开、不改路由或策略。冲突时按第 7 节停手。
- tailnet 名称、账号、设备名、认证凭据、真实 URL 一律不写进仓库、日志与证据。
  文档和证据里只出现占位符 `<host>.<tailnet>.ts.net`。
- 远端能管理不等于有应用登录：tailnet 成员就是身份，详见第 6 节。

## 2. 安装与开启

1. 在 Host 上安装 Tailscale（官网 Windows 下载页），登录操作者自己的 tailnet。
   登录走浏览器授权，不生成、不保存、不提交认证密钥。
2. 用同一账号在手机安装 Tailscale 应用并登录，确认和 Host 在同一个 tailnet。
3. 打开 tailnet 管理台，开启 **MagicDNS** 与 **HTTPS certificates**（DNS 页面）。
   若管理台拒绝开启 HTTPS，先记录原因，不要改用 Funnel。
4. 在 Host 上确认本机域名，只记在本地：

   ```
   tailscale status
   ```

   输出中的 `<host>.<tailnet>.ts.net` 就是后续要用的名字。不要把它贴进提交内容。
5. 检查版本与参数写法：`tailscale version`、`tailscale serve --help`。
   不同 CLI 版本参数可能不同，后续以本机 `--help` 为准。

## 3. 启动 Host

先停掉当前正在跑的 Host（设备会保留最后一帧，不会黑屏）。用 Git Bash 进入本 worktree 再运行
（下面保留 `10.21.98.75` 作为示例；2026-11-09 实际运行时 LAN 已变更，Host 为
`10.127.70.75`，按当次 `ipconfig` 的 LAN IPv4 替换即可）：

```
cd /c/Users/cslki/.codex/worktrees/a5b3/eink-panel
PYTHONPATH="D:/Codex/round2-multipage-20261108/host-deps" \
"C:/Users/cslki/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe" \
-m server.main --host 10.21.98.75 --port 8000 --remote
```

启动日志应只有一行监听地址、不含任何 tailnet 名：

```
Host listening on 10.21.98.75:8000, 127.0.0.1:8000
```

确认两个地址同时监听（另开一个 Git Bash）：

```
netstat -ano | findstr :8000
```

期望看到 `10.21.98.75:8000` 与 `127.0.0.1:8000` 两行 `LISTENING`，且 PID 相同。
只看到 LAN 地址说明没加 `--remote`；只看到 `127.0.0.1` 说明 `--host` 传错了。

设备侧回归（这一步必须做，不通过就停）：

- 设备照常轮询 `GET /api/panels/progress/frame`：内容变化 200，其余 304。
- 帧契约不变：400×300、15000 字节、60 s 轮询、整屏刷新。
- mDNS 仍广播 `10.21.98.75`，LAN 下 `http://10.21.98.75:8000/manage` 正常。
- `--remote` 只增加一个回环监听，不改变上述任何一项；若设备开始超时或重复整屏刷新，
  立即停手，回到不带 `--remote` 的启动方式。

## 4. 开启 Serve

只把回环监听交给 Serve，LAN 监听不受影响：

```
tailscale serve --bg --https=443 127.0.0.1:8000
tailscale serve status
```

`tailscale serve status` 必须显示 `https://<host>.<tailnet>.ts.net` 转发到
`http://127.0.0.1:8000`，且只有一个 target。

- 若本机 CLI 拒绝这组参数，先 `tailscale serve --help` 查正确写法，只调整参数形式
  （例如 HTTPS 端口的表达方式），并把**实际执行的命令**记入本文件和第 9 节证据。
- 不改用 Funnel（会把页面暴露到公网），不加第二个 target（会把 LAN 地址也代理出去）。
- Serve 失败时先看第 7 节，不要靠改防火墙或改 Host 绑定绕过。

## 5. 手机访问

1. 手机 Tailscale 已登录同一 tailnet（第 2 节第 2 步），状态显示已连接。
2. **关闭 Wi-Fi，只用蜂窝网络**，确认手机不在家庭 LAN 里。
3. 打开 `https://<host>.<tailnet>.ts.net/manage`。
4. 验收检查：
   - 页面完整加载，设备状态卡片可见。
   - 切换一次页面：设备下一次轮询 200（刷新计数 +1），再下一次回到 304。
   - 保存一条 Memo 成功；生成一次预览成功，预览版本号与响应 ETag 一致。
   - `GET /api/device/firmware/status` 为 `configured: false`，
     `POST /api/device/firmware/arm` 为 503（见第 6 节）。
5. 还原 Memo：测试前先 `GET /api/pages/memo` 记下原内容，测试完成后把它写回，
   让设备页内容与测试前一致（不要留一条测试用的 Memo）。
   还原前后的 `/api/pages/memo` 响应都记入 `remote-switch.txt`。
6. 可选：在这个 HTTPS 源上安装 PWA。它与 LAN HTTP 源各自独立缓存，属正常现象。
7. 全程都不需要关闭公司 VPN；如果必须关才能通，按第 7 节停手并上报。

## 6. 安全边界

- **没有应用登录**。任何能加入该 tailnet、且被 ACL 放行的设备都能直接管理 Host。
- 建议在管理台的 Access controls 里加一条意图为「只允许操作者自己的设备访问该主机的
  TCP 443」的规则。语法以管理台当前版本为准，本文不抄写规则 JSON，也不猜测字段。
- 不建议把 443 放给整个 tailnet 或 `autogroup:member`；先确认成员清单里只有自己的设备。
- `config/firmware.json` 保持不存在，OTA arm 固定 503。R7 不做远程 OTA；
  以后若配置固件，tailnet 设备也能 arm，必须一并纳入上面的 ACL 考虑。
- 不新增公网入口：不用 Funnel、不做端口映射、不用公网 DNS。
  Serve 只连 `127.0.0.1`，直连 `http://100.x:8000` 不可达，这是预期。
- 不改防火墙、不改公司 VPN、不改 Host 服务与注册表（Tailscale 安装器自身除外）。
- 手机或笔记本丢失：立即在管理台把该设备从 tailnet 移除，Host 不用改。

## 7. 失败处理

| 现象 | 含义 | 动作 |
| --- | --- | --- |
| 远端 URL 打不开；`tailscale status` 显示已停止或已登出 | Tailscale 客户端没在跑 | **恢复**：重新启动/登录 Tailscale，Host 不用重启；LAN `/manage` 与设备轮询本就不受影响 |
| Tailscale 正常，`tailscale serve status` 也显示 `127.0.0.1:8000`，但远端页面返回 502 或连接错误 | Host 已停止或端口变了，Serve 还指向回环 | **恢复**：用同一个端口带 `--remote` 重新启动 Host，再用 `netstat -ano \| findstr :8000` 复核两个监听；这是 Host 侧问题，不是 Tailscale 故障 |
| `tailscale serve --https` 报错，没有 TLS 名字 | tailnet 没开 HTTPS 证书 | **停手**：去管理台开启 HTTPS certificates 后重试；若坚持先验证，只能退回 tailnet 内 HTTP（不能装 PWA），并把这个降级写进证据 |
| 换了网络后 Host 的 LAN IPv4 变了 | mDNS 与直连 LAN 失效；Serve 仍指向回环，但 Host 还绑在旧 IP | **恢复**：用新的 `--host` 重启 Host，保留 `--remote`；不要改成 `0.0.0.0` |
| `--remote` 启动即退出（端口被占用） | 进程在关闭已建 socket 后以非零码退出，不会半开 | **恢复**：释放 8000 端口或换 `--port`，两个监听必须同端口；不允许悄悄少一个监听 |
| 公司 VPN 或终端策略导致远端连不上 | 可能是路由/策略冲突 | **停手**：不关闭、不重配 VPN 或防火墙，停止 R7 验证并上报，等策略明确后再试 |
| tailnet 设备丢失或疑似被控 | 等于完整管理权限外泄 | **恢复**：从 tailnet 移除该设备；Host 无需改动 |

判定口径：只要 LAN 设备回归失败（超时、重复整屏刷新、200/304 异常），无论远端是否可用，
都先停手回滚到不带 `--remote` 的启动方式。

## 8. 回滚

1. 停掉当前 Host，去掉 `--remote` 重启：

   ```
   cd /c/Users/cslki/.codex/worktrees/a5b3/eink-panel
   PYTHONPATH="D:/Codex/round2-multipage-20261108/host-deps" \
   "C:/Users/cslki/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe" \
   -m server.main --host 10.21.98.75 --port 8000
   ```

   此时只剩 LAN 监听，行为与 R7 之前完全一致。
2. 关掉 Serve（本机 CLI 为 1.104.5，关闭写法仍先用 `tailscale serve --help` 确认）：

   ```
   tailscale serve reset
   ```

   `reset` 清掉的是这台机器上的全部 serve 配置；第 4 节只建过一个 target，
   所以效果等同只关掉这一个，不会牵动别的东西。

   执行后 `tailscale serve status` 应为空，域名不再响应；LAN 与设备轮询不受影响。
3. 可选：卸载 Tailscale。不影响 `data/pages/` 页面数据、固件与设备运行。
4. 回滚不需要改任何配置文件；`config/firmware.json` 依旧保持不存在。

## 9. 证据清单

目录：`D:/Codex/round2-r7-20261108/acceptance/`（仓库外，不提交）。
文件名固定，共七个，缺一不可。2026-11-09 已生成六个：`netstat.txt`、`serve-status.txt`、
`https-check.txt`、`lan-regression.txt`、`remote-switch.txt`、`ota-503.json`，另有 `README.md`
总览；其中 `https-check.txt` 是额外补充证据。`remote-manage.png` 仍缺失，补齐前不得声称远端
验收通过。本次设备地址为 `10.127.70.216`（旧 `10.21.98.216`），Host 的当前 LAN IPv4 为
`10.127.70.75`（旧 `10.21.98.75`）。

| 文件 | 必须证明 |
| --- | --- |
| `netstat.txt` | `netstat -ano \| findstr :8000` 同时出现当前 LAN IPv4（示例 `10.21.98.75`；本次为 `10.127.70.75`）的 `:8000` 与 `127.0.0.1:8000`，同一个 PID，均为 `LISTENING` |
| `serve-status.txt` | `tailscale serve status` 显示 `https://<host>.<tailnet>.ts.net` → `http://127.0.0.1:8000`，仅一个 target；**tailnet 名打码** |
| `lan-regression.txt` | LAN 下 `/manage` 正常、mDNS 仍广播当前 LAN IPv4（示例 `10.21.98.75`；本次为 `10.127.70.75`）、设备轮询 200 后 304、帧仍为 400×300/15000 字节/60 s；本次设备 `10.127.70.216` 真机参与了 A1/A2，Host 端广告已启动且无错误，未单独跑 mDNS 客户端发现 |
| `remote-switch.txt` | 手机蜂窝下切换页面：设备一次 200（刷新计数 +1）后回 304；Memo 保存与预览成功，预览版本等于 ETag |
| `ota-503.json` | `GET /api/device/firmware/status` 为 `configured: false`；`POST /api/device/firmware/arm` 返回 503 |
| `remote-manage.png` | 手机 Wi-Fi 关闭、蜂窝网络下打开远端 `/manage` 的截图；**地址栏打码** |
| `README.md` | 证据总览：日期、设备固件版本、Host 的两个监听地址、`serve-status.txt` 的打码内容、规格 §9 的 A1–A6 各项结果，并明确列出未做项（NOT RUN）；不含 tailnet 名、不含任何凭据 |

证据纪律：

- 文本文件里不出现 tailnet 名、账号、设备名全称、认证凭据；需要区分时用 `<host>`、`<tailnet>`。
- 截图地址栏、通知栏里的账号信息一并打码。
- 若 Serve 用了与本文件不同的参数写法，在同一目录补记实际命令与 `tailscale serve --help`
  相关片段，并回头更新第 4 节。
- 证据只证明「这一次、这台机器、这个网络」；换网络或换 Host IP 后需重做第 3、5 节。
