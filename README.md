# E-Ink Panel Simulator — Phase 3

这是一个面向新手的 400×300 极简终端风墨水屏模拟器。当前包含
`ProgressPanel`、`StatsPanel` 和 `FlowPanel`，不会接入账号型公网业务数据、AI、ESP32
或真实硬件。Phase 3 增加 Mock、本地 JSON、HTTP JSON 数据源以及自动刷新和断线回退。

## 当前功能

- Normal Preview 与 1-bit E-Ink Preview
- Progress、Stats、Flow 三种面板切换
- 每种面板包含默认、等待数据、错误数据示例
- Mock、Local JSON、HTTP JSON 三种 DataAdapter
- 手动刷新与可选自动刷新
- HTTP 失败时保留 Last Known Good 数据
- Refresh
- PNG 与 BMP 导出
- 缺失 `updated_at` 时显示当前系统时间

## Windows 安装与启动

### 1. 安装 Python

安装 Python 3.12，并在安装界面勾选 **Add Python to PATH**。

### 2. 打开项目文件夹

在资源管理器打开：

```text
D:\Codex\eink-panel
```

在文件夹空白处按住 Shift 并点击鼠标右键，选择“在此处打开 PowerShell”。

### 3. 创建虚拟环境

在该 PowerShell 窗口运行：

```powershell
python -m venv .venv
```

### 4. 激活虚拟环境

```powershell
.\.venv\Scripts\Activate.ps1
```

如果 PowerShell 阻止脚本执行，可先运行：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

然后再次激活虚拟环境。

### 5. 安装依赖

```powershell
python -m pip install -r requirements.txt
```

### 6. 运行测试

```powershell
python -m pytest
```

### 7. 启动测试 HTTP API（可选）

新开一个 PowerShell，激活虚拟环境后运行：

```powershell
python -m examples.http_server
```

测试服务地址是 `http://127.0.0.1:9000`，提供 `/progress`、`/stats` 和 `/flow`。

### 8. 启动模拟器

```powershell
python -m server.main
```

浏览器打开：

```text
http://127.0.0.1:8000
```

按 `Ctrl+C` 停止服务。

## 使用数据源与自动刷新

1. 选择 Progress、Stats 或 Flow。
2. 在 `DATA SOURCE` 选择 Mock、Local JSON 或 HTTP JSON。
3. 点击 Refresh 立即重新获取数据。
4. `AUTO REFRESH` 默认 OFF；开启后可选择 5 秒开发模式至 30 分钟。
5. HTTP 服务断开后，STATUS 显示 OFFLINE；已有成功数据时继续显示旧画面。

本地 JSON 文件位于 `data/local/`。其他脚本可更新这些文件，再点击 Refresh。

## 异常恢复

- HTTP 连接失败、超时或非成功状态不会让模拟器崩溃，STATUS 显示 `OFFLINE`。
- 可解析但不符合对应 Panel 语义的数据不会进入 Last Known Good，STATUS 显示 `ERROR`。
- 已有成功数据时，失败刷新继续显示旧画面并标记 `STALE DATA`；恢复成功后自动回到 `ONLINE`。
- 同一数据源的刷新在服务端按顺序执行；浏览器会合并重复刷新并忽略面板或数据源切换后的过期响应。
- Last Known Good 只保存在内存中，重启模拟器后会清空。

## Phase 3 API

- `GET /`
- `GET /api/samples/{panel_type}`
- `GET /api/data-sources/{panel_type}`
- `POST /api/data-sources/{source_id}/refresh`
- `POST /api/panels/{panel_type}/render?mode=normal|eink&format=png|bmp`

`panel_type` 可选 `progress`、`stats`、`flow`。原有 ProgressPanel URL 不变。

ProgressPanel 视觉基准保存在 `docs/reference/progress-simulator-concept.png`，设计参数见
`docs/DESIGN_SYSTEM.md`。数据与刷新架构见 `docs/DATA_ADAPTER.md` 和
`docs/REFRESH_SYSTEM.md`。
