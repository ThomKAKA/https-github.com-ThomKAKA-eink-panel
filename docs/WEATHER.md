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

## 添加一个城市（配置即接口）

城市清单是唯一扩展点：抓取、文档、校验、`/api/pages/weather/cities`、`/manage` 按钮都按
`config/weather.json` 的 `cities` 数组长度工作，没有写死 4 个。加城市只改配置，不改代码：

```json
{
  "id": "shanghai",
  "name": "上海",
  "latitude": 31.2222,
  "longitude": 121.4581
}
```

规则与步骤：

- `id`：小写字母开头，只含小写字母、数字、`_`、`-`，最长 16 字符，必须唯一。
- `name`：显示在页头和选城按钮上，最长 8 个字符（例：天津、上海）。
- 经纬度用十进制度，取城市中心即可；精度 4 位小数足够。
- `default_city` 必须仍在清单里；想让新城市当默认就一并改它。
- 保存文件后**重启 Host**（配置只在启动时读一次）。设备照常显示最后一帧，不需要重新配网。
- 重启后下一次整点或手动 `POST /api/pages/weather/refresh` 即抓到新城市；
  `/manage` 的按钮与 `GET /api/pages/weather/cities` 会自动多一项。
- 回归护栏：`test_a_fifth_city_needs_config_only`（批量抓取与落盘）、
  `test_a_fifth_city_renders_without_a_panel_change`（渲染）、
  `test_a_fifth_city_only_needs_a_config_edit`（接口与切换）。这三条测试证明第 5 城
  不需要改任何生产代码。

容量与边界：

- 页面文档上限 16 KiB；实测 4 城 2,472 B（约 600 B/城），按此外推约 26 城到上限，
  建议不超过 20 城留余量。超限时刷新返回 `{"ok": false, "error": "weather document
  exceeds the 16 KiB budget"}`，旧文档与旧帧保持不变（有测试覆盖）。
- 面板一次只画 `current_city` 一个城市，城市数量不影响版式；`/manage` 的按钮会自动换行。
- 四城用一次批量请求。城市变多后 URL 会变长，Open-Meteo 单次多坐标的上限未实测；
  如果以后加到二三十城，建议把请求拆成多批（目前未实现，属后续增量）。
- 2026-11-08 实测扩展：临时把上海加为第 5 城并重启 Host，启动抓取与手动刷新都成功，
  文档 3,080 B、`/api/pages/weather/cities` 立即多出「上海」，随后已还原为四城配置。
  全过程没有改任何生产代码。
- 删除城市同理：从数组里去掉、改 `default_city`（若删的是默认城）、重启。当前选中的城市
  若被删除，下一次刷新会自动回落到 `default_city`。

## 限制

- 只支持配置里列出的城市，不做任意城市搜索（避免把上游地理编码引进来）。
- 不做分钟级降水、空气质量、预警；保持 8 小时 + 3 天的固定版式。
- 不使用上游时区之外的时间；一切日期按 Host 东八区计算。
