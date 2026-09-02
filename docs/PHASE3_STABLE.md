# Phase 3 Stable

Phase 3 Stable 将模拟器的数据层固定为以下流程：

```text
Data Source → DataAdapter → RefreshManager → Panel → PNG/BMP / Simulator
```

## 稳定能力

- Progress、Stats、Flow 绑定 Mock、本地 JSON 或 HTTP JSON 数据源。
- 适配器捕获文件、连接、超时、HTTP 状态与 JSON 错误。
- Panel 在数据缓存前执行语义检查，无效数据不会污染 Last Known Good。
- HTTP 失败时保留旧数据并标记 OFFLINE/STALE，恢复后更新为新数据并回到 ONLINE。
- 同一数据源的刷新顺序稳定，不同数据源可并行。
- 浏览器合并重复刷新并忽略过期响应。
- PNG 与 1-bit BMP 输出保持 400×300。

## 范围限制

- Last Known Good 是单进程内存缓存，不跨重启持久化。
- 自动刷新由浏览器调度，不包含后台任务队列。
- 不包含 ESP32、真实墨水屏、数据库、LLM、Agent、账号型 API 或新 Panel。
- 进入后续阶段前，应先完成 STEP-006 用户核对并建立 Git 基线。
