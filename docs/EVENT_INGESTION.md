# Phase 4 P1 Event Ingestion

Phase 4 P1 为外部脚本增加一个轻量、同步的 Panel 更新入口。它不是通用 Event Bus：
没有订阅者、后台队列、消息重放、数据库、插件加载或跨进程状态共享。

```text
External client
      ↓ POST /api/events
PanelUpdateEvent
      ↓ Panel normalize()
EventStateStore
      ↓ latest snapshot per panel + source
GET /api/events/snapshots/{panel}/{source}
      ↓
Existing Panel Renderer
```

## Event contract

`POST /api/events`

```json
{
  "event_id": "codex-build-001",
  "type": "panel.update",
  "source": "codex",
  "panel": "progress",
  "occurred_at": "2026-09-02T12:00:00Z",
  "data": {
    "title": "CODING",
    "progress": 72,
    "status": "RUNNING"
  }
}
```

- `event_id`：当前 source 流中的幂等标识，只允许字母、数字、点、下划线和连字符。
- `type`：P1 只接受固定值 `panel.update`。
- `source`：状态流标识；快照按 `panel + source` 隔离。
- `panel`：`progress`、`stats` 或 `flow`。
- `occurred_at`：必须包含时区的 ISO 8601 时间，用于拒绝乱序覆盖。
- `data`：原有 Panel 数据对象，写入前必须通过对应 Panel 的 `normalize()` 语义检查。

如果 `data` 没有 `source` 或 `updated_at`，服务端分别使用事件信封的 `source` 和
`occurred_at` 补齐；信封不会覆盖调用方显式提供的 Panel 字段。

成功写入返回 HTTP 200、`accepted=true` 和当前快照。重复发送当前 `event_id` 返回
HTTP 200、`accepted=false`、`reason=duplicate`，并保持旧快照。不同事件 ID 的时间戳
早于或等于当前快照时返回 HTTP 409、`reason=out_of_order`。

请求结构错误、无时区时间或未知事件类型由 FastAPI 返回 HTTP 422。可解析但不能形成
Panel `ok` 状态的数据返回 HTTP 422，且不会创建或替换快照。

## Reading a snapshot

`GET /api/events/snapshots/{panel}/{source}`

存在时返回最新事件及 `received_at`；不存在时返回 HTTP 404。返回的 `data` 可以直接提交给
现有 `/api/panels/{panel}/render` 接口。P1 不会让浏览器模拟器自动切换到该快照，也不包含
WebSocket 或 Server-Sent Events。

## PowerShell example

```powershell
$body = @{
  event_id = "codex-build-001"
  type = "panel.update"
  source = "codex"
  panel = "progress"
  occurred_at = (Get-Date).ToUniversalTime().ToString("o")
  data = @{
    title = "CODING"
    progress = 72
    status = "RUNNING"
  }
} | ConvertTo-Json -Depth 4

Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/events" `
  -ContentType "application/json" `
  -Body $body
```

## State lifecycle and safety

- 每个 Python 进程拥有自己的内存快照；进程重启后全部清空。
- P1 不支持多 worker 共享状态、持久化、审计历史或可靠消息投递。
- 日志只记录 panel、source、event ID 或错误类别，不记录完整 Panel 数据。
- 当前接口没有认证。保持默认 `127.0.0.1` 绑定；不要直接暴露到不可信网络。
- 事件入口不会修改 RefreshManager 的 Last Known Good，两条状态链保持独立。
