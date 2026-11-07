# STEP016D — Bitmap Interface

状态：DESIGN FROZEN；STEP016D IMPLEMENTATION / COMPILATION / PHYSICAL VERIFICATION = NOT RUN。
基线：`45ca1dcc0e9043639299621229a223c7f0eca7de`，STEP016C Renderer 已完成。
承接 [架构冻结](STEP016A_ARCHITECTURE_FREEZE.md) 和 [B Render 接口](STEP016B_RENDER_INTERFACE.md)。

## 已有输入，不冒充完整传输产物

当前实现见 [离线入口](../../../panels/offline_progress.py)，阶段事实见 [PROJECT_STATE](../../../PROJECT_STATE.md)。
未发现单独的 STEP016C Renderer 接口文档；本文件联合上述规范、已提交代码和本地 renderer-manifest.json 记录实际接口。

现有目录：`artifacts/step016-offline-progress/step016c-final-20260913/`（相对仓库根目录，已忽略）。

| 属性 | 当前值 |
| --- | --- |
| 文件 | progress.preview.png |
| 容器 / 尺寸 | PNG / 400×300 |
| 色深 / 极性 | Pillow mode 1，1-bit；解码像素0黑、255白 |
| 方向 | L：正常业务阅读方向，左上原点，x右、y下；未预翻转 |
| 大小 | 1619 bytes |
| SHA-256 | 538be61374b7804bc64a05dd1eb4f6caca65a778201d2e03ddbae8f7aedb0c2a |
| 伴随记录 | renderer-manifest.json；仅 Renderer 阶段，不是完整发布 manifest |

PNG 是带容器、压缩和扫描行编码的文件；1619字节不是控制器帧长度。不得直接传 PNG 文件字节，或剥去任意固定前缀充当 raw。
Python 继续负责数据、字体、布局及正常预览；不改 Renderer 方向或引入 ESP32 图像解码。

## 未来传输格式（本轮不生成）

先按 [方向规则](STEP016D_ORIENTATION_RULE.md) 从 L 生成 T，再按 [既有帧格式](FRAME_PROTOCOL.md) 打包；只复用其像素格式，不引入其候选 HTTP 协议。

| 属性 | 固定契约 |
| --- | --- |
| raw 文件 | progress.frame.raw |
| 尺寸 / 字节数 | 400×300 / 精确15000 |
| 行布局 | T坐标，row-major，从上到下；stride 50，无padding |
| 位序 / 极性 | 每行从左到右，MSB-first，bit7最左；0黑1白 |
| 容器 | 无文件头、调色板、压缩 |
| 嵌入文件 | progress_frame.h；完整数组的字节序列等于raw |

T像素位置：`offset = y * 50 + floor(x / 8)`，`mask = 0x80 >> (x % 8)`。
header文本哈希不等于raw哈希；必须提取数组元素逐字节比较。命名不代表这些产物已经存在。

## 来源、输出与失败边界

未来人工执行构建前转换，写入新的未占用 `artifacts/step016-offline-progress/<run-id>/`，不修改或补写旧 STEP016C 目录。
完整候选集合含正常方向 progress.preview.png、传输raw、header及独立 manifest.json。
manifest记录源Renderer运行标识/输入及字体来源、工具版本、方向契约、三份产物大小与SHA-256，不保存自身哈希。
保留 renderer-manifest.json 的 Renderer-only 含义，不通过重命名把它当完整发布清单。

输入尺寸/模式/哈希不符、生成失败、目录冲突或元素不一致时拒绝放行，不覆盖上次结果、不混用run-id、不自动编译或上传。
完整集合的字节校验与预览验收均通过才可供未来构建使用。测试见 [D测试计划](STEP016D_DISPLAY_TEST_PLAN.md)。
