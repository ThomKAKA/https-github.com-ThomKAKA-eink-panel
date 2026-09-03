# Frame Transport v1：候选协议，仅文档

**当前没有实现 `GET /api/display/frame.raw` 或 metadata 端点，也没有网络客户端。**
本文件规定 H1 本地位图格式，并作为将来 H2 的候选 HTTP 契约，不更改现有公开 API。

## 责任分工与 body

Python 负责数据、字体、中文、布局、二值化；ESP32 只显示最终像素。
选用未压缩 raw MONO1，不让 ESP32 解析 PNG/BMP。BMP 文件包含头、调色板和行存储约定，
不能仅去掉任意固定长度前缀就当成这里的 raw 帧。

| 属性 | 固定约定 |
| --- | --- |
| width / height | 400 / 300，不缩放、不裁剪 |
| 坐标原点 | 左上角 (0,0)，x 向右，y 向下 |
| 排列 | row-major，从上到下、每行从左到右 |
| 位序 | MSB first：每字节 bit7 是其最左侧像素 |
| 黑白 | 0 = 黑，1 = 白；`0x00` 为 8 个黑像素 |
| stride | 50 bytes，无额外行 padding |
| payload | `400 × 300 / 8 = 15000 bytes`，必须完全匹配 |

像素 `(x,y)` 对应 `offset = y * 50 + x / 8`，mask 为 `0x80 >> (x % 8)`。
这与已核对的 [GxEPD2 BW 缓冲像素排列](https://github.com/ZinggJM/GxEPD2/blob/de82887e77a78528ea386e68bba2cb0291d2c319/src/GxEPD2_BW.h)
一致；物理方向仍由 H1 非对称图案验收，不把源码推断当实测。

## 候选 HTTP 响应

未来可新增 `GET /api/display/frame.raw`，成功响应 body 仅含上述 15,000 字节。
候选 headers：

```http
Content-Type: application/octet-stream
Content-Length: 15000
X-Eink-Protocol: 1
X-Eink-Width: 400
X-Eink-Height: 300
X-Eink-Format: mono1-msb-white1
ETag: "<frame-content-hash>"
```

不增加二进制 magic/header：HTTP 已划分 headers/body，尺寸、版本、格式由 headers
自描述；body 因而能直接交给显示驱动。未来若改为文件或串口传输，再单独评估容器头，
不复用一个没有上下文的裸字节流。v1 不压缩、不引入 protobuf/MessagePack。

上面不是当前可调用接口；要显示哪组 panel/source 的选择、权限和网络部署，由 H2
方案单独确认。当前服务器仍默认本机绑定且事件 API 无认证，不能为了 ESP32 联网直接对公网开放。

## H2 必须满足的失败边界（未实现）

- 下载到候选缓冲，完整校验状态码、headers、格式及精确字节数后才能提交显示。
- 超时、断线、短包/长包、错误尺寸或格式都不得覆盖最后有效帧；也不触发清屏。
- HTTP 200/长度正确不是安全来源证明；局域网访问范围与认证应在 H2 明确。
- 驱动失败不推进 frame ID 或刷新计数；Serial 优先记录简短错误类别，不打印凭据或响应数据。

## 未来轮询优化（未实现）

先考虑 [RFC 9110 条件 GET](https://www.rfc-editor.org/rfc/rfc9110.html#name-if-none-match)：
用 `If-None-Match` 携带上次 ETag，未变化时由未来服务器返回 304，
无需下载或刷新。这样无需先做一次 metadata 请求再下载，减少两次请求间帧变化的竞态。

若以后确实需要 metadata，可候选增加 `GET /api/display/metadata` 返回 `frame_id`、
`updated_at`、`etag/hash`。下载必须与目标 frame ID/ETag 一致，不得把不匹配的帧标成已显示。
这只是扩展方向，本次不增加相应端点、轮询器或网络库。
