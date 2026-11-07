# Phase 3 对抗性审查

## 环境

- 项目目录：`D:\Codex\eink-panel`
- 审查日期：2026-09-02
- Python：3.12.13（项目 `.venv`）
- pytest：8.4.1
- 审查前基线：80 passed
- Git：已初始化，`main` 尚无提交；审查前有 51 个未跟踪文件

## 测试项目

| 项目 | 状态 | 备注 |
|---|---|---|
| JSON 异常 | 通过 | 三种 Panel 覆盖空对象、缺字段、null、空数组、错误类型和 500 字符文本 |
| HTTP 异常 | 通过 | 覆盖连接失败、HTTP 500、timeout、非法 JSON 和 JSON 数组 |
| Last Known Good | 通过 | 验证成功、失败回退、语义无效回退和恢复后更新 |
| Refresh 竞争 | 通过 | 同源串行化；不同源并行；旧响应不再反向覆盖新缓存 |
| Renderer 稳定性 | 通过 | 三种 Panel 各连续渲染 100 次，无异常，尺寸保持 400×300 |
| Refresh 压力 | 通过 | 三种 Mock 数据源各连续刷新 100 次，状态保持 ONLINE |
| PNG/BMP | 通过 | 复用 API 回归测试，三种 Panel PNG 为 400×300，E-Ink BMP 为 1-bit |
| 日志与错误 | 通过 | HTTP 错误使用脱敏分类；不记录响应体、完整查询参数或凭据 |
| 浏览器恢复流程 | 通过 | 验证在线、首次断线、缓存回退、恢复、自动刷新、重复刷新和面板切换；控制台无错误 |

最终自动测试结果：`111 passed in 0.82s`。

浏览器证据截图：`phase3-flow-first-offline.png`、`phase3-progress-stale-offline.png`、
`phase3-progress-recovered-online.png`。截图保存在 Codex 本次任务的 visualization 输出目录，
未写入项目仓库。

## 压力观测

使用 `tracemalloc` 执行 300 次 Panel 渲染和 300 次 Mock 刷新，垃圾回收后的当前分配增量为
206,577 bytes，观测峰值为 259,477 bytes。该数值仅用于本次审查记录，不作为跨平台 CI
阈值；自动测试以无异常、正确状态和固定输出尺寸为稳定性门槛。

## 发现与修复

1. 同一数据源的网络获取原本在状态锁之外执行，慢速旧响应可晚于新响应提交并覆盖 Last
   Known Good。现已增加每数据源独立锁，覆盖获取、验证和提交全过程。
2. 浏览器原本用空对象表示“尚无数据”，导致真实 `{}` 响应回退显示 Mock sample。现以
   `null` 表示尚未获取，空对象会进入 Panel 等待态。
3. 手动刷新、自动刷新及面板切换可产生重叠请求。现已合并同一上下文的重复请求，并用
   generation token 忽略过期响应。
4. HTTP 异常文本可能包含完整请求 URL。现已改为连接、超时、状态码、非法 JSON 和非对象
   JSON 等稳定分类。
5. 可解析但语义无效的数据原本可以替换 Last Known Good。现已在缓存前执行 Panel 语义检查。
6. `httpx` 默认 INFO 日志会记录完整请求 URL。应用现将 `httpx` 日志级别固定为 WARNING，
   同时保留项目自身不包含 URL 或响应体的状态日志。

## 剩余风险

- Last Known Good 仅存在当前进程内，重启后清空。
- 每数据源锁只协调单个 Python 进程；Phase 3 默认单进程运行，不支持多 worker 共享状态。
- Panel 继续接受 Pydantic 可转换值，且没有新增任意文本长度限制；本阶段只保证异常文本稳定
  渲染，不改变已确认的视觉体系。
- Phase 3 不包含真实账号数据、硬件、数据库或外部秘密管理。
