# 天气页（四城切换）

天气页在 Host 上渲染 400×300 的 1-bit T 帧，设备只负责取帧、校验、整屏刷新。
2026-11-08 起从「单城长沙」升级为「天津 / 桂林 / 长沙 / 南京」四城，可随时切换。

## 数据流

1. `config/weather.json` 的 `cities` 是唯一城市清单（`id`、`name`、经纬度），
   `default_city` 决定首次写入的当前城市。
2. `WeatherSource` 每小时用**一次** Open-Meteo 批量请求取四城：经纬度用逗号拼接，
   上游按顺序返回四个对象；返回数量与配置不一致直接判失败。
3. 每城解析成 8 小时（从当前整点起）与 3 天预报，写入 `data/pages/weather.json`
   的 `cities[id]`。整份文档约 2.5 KB，远低于 16 KiB 上限。
4. 设备帧只画 `current_city` 指向的城市；切换城市只是改这一个字段并把 revision +1，
   因此下一轮轮询取到新帧（200），再下一轮 304。

## 文档结构

```json
{
  "current_city": "changsha",
  "cities": {
    "changsha": {
      "name": "长沙",
      "current_temp": 14,
      "current_label": "阴",
      "hourly": [{"hour": 21, "temp": 14, "label": "阴"}],
      "daily": [{"date": "11-08", "weekday": "周日", "high": 16, "low": 14, "label": "阴"}]
    }
  },
  "stale": false,
  "source": "open-meteo"
}
```

- `hourly` 固定最多 8 条，`daily` 固定 3 条；`cities` 允许为空（还没抓到数据时显示「等待天气数据」）。
- `current_city` 必须存在于 `cities`（`cities` 为空时除外），否则文档校验失败、不出帧。

## HTTP

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/pages/weather` | 只读文档（含 revision、updated_at） |
| `GET` | `/api/pages/weather/cities` | 选城按钮的数据源：配置里的四城 + 当前选中 |
| `POST` | `/api/pages/weather/select-city` | `{"city": "guilin"}`；未知城市 422，并发冲突 409，同城不涨 revision |
| `POST` | `/api/pages/weather/refresh` | 立即批量抓取；失败保留上一版并标 stale |
| `POST` | `/api/pages/weather/preview` | 用仓内文档 + 当天 `day_key` 生成 PNG 预览 |
| `PUT` | `/api/pages/weather` | 400，天气页只读 |

## 失败与跨天

- 抓取失败：文档 `stale=true`，画面页脚标 `OPEN-METEO STALE`，设备继续显示上一帧内容。
- `stale_after_minutes=90`：超过 90 分钟再次失败才把 stale 写回文档，避免每次重试都涨 revision。
- 帧的 render key 含 `day_key`，跨零点自动重画页头日期。
- 刷新每小时一次，与固定 60 s 轮询相互独立；只有内容变化才 200，其余 304。

## `/manage`

天气卡片顶部列出四个城市按钮，当前城市反白禁用。点击其它城市会调用
`select-city`、重拉文档并重生成预览；消息行会提示「设备下一轮轮询取新帧」。

## 限制

- 只支持配置里列出的城市，不做任意城市搜索（避免把上游地理编码引进来）。
- 不做分钟级降水、空气质量、预警；保持 8 小时 + 3 天的固定版式。
- 不使用上游时区之外的时间；一切日期按 Host 东八区计算。
