# STEP016B — Python to Bitmap Interface

状态：INTERFACE FROZEN / IMPLEMENTATION NOT RUN / TESTS NOT RUN。
基线：`dbd7b8c2956513f74e623cb6321e0d59c4eb16a7`；遵循 [STEP016A](STEP016A_ARCHITECTURE_FREEZE.md)。

## 输入与责任

人工调用未来离线生成工具，读取 [离线 JSON](STEP016B_JSON_SCHEMA.md)，严格校验后映射为既有 ProgressPanelData；必须保留显式 timestamp，禁止 Adapter/Renderer 的系统时间回退参与冻结页面。
复用 [Local JSON](../../../adapters/local_json.py)、[ProgressPanel](../../../panels/progress.py)、[BasePanel](../../../panels/base.py) 的职责与语义，不宣称当前代码已有新字段映射或导出入口。
[Stats](../../../panels/stats.py) / [Flow](../../../panels/flow.py) 共享 BasePanel 的 validate/normalize/render 模式，只作对照，不进入本接口，不改它们的模型。

Python 负责数据、中文字体、布局、Pillow 图片生成和二值化。目标调用语义为 ProgressPanel、400×300、eink 模式；现有 render 返回 Pillow Image，不是已有 raw/header 发布工具。
ESP32 不解析 JSON、PNG/BMP，不处理字体或 UI 布局。离线生成无 HTTP 服务、网络、轮询、编译或上传副作用。

## 产物契约

未来输出根目录：`D:\Codex\eink-panel\artifacts\step016-offline-progress\<run-id>\`，已有 artifacts 忽略规则覆盖。
run-id 是单个安全目录名，仅隔离产物，不参与页面内容或时间字段；不得包含路径穿越，也不得复用已有发布目录。目录分配策略属于未来工具实现，不影响以下文件格式。

| 文件 | 固定内容 |
| --- | --- |
| progress.preview.png | 400×300、单通道 1-bit 黑白 PNG；正常阅读的逻辑页面，不是传输方向 |
| progress.frame.raw | 预翻转 Y 的传输帧，精确 15000 字节，无文件头/压缩/调色板 |
| progress_frame.h | 表示同一 raw 字节序列的完整 C++ 字节数组及长度，供独立入口编译嵌入 |
| manifest.json | 输入、字体、工具及三个产物的大小/SHA-256 与方向/格式说明，不保存自身哈希 |

raw 遵循 [既有帧格式](FRAME_PROTOCOL.md)：宽400、高300、stride50、row-major、每行从左到右、bit7 为最左像素、0黑1白，无 padding；不能剥去任意 BMP 前缀代替编码。
header 的数组元素必须与 raw 逐字节一致；“一致”指解码后的数组，不指头文件文本和 raw 文件哈希相同。符号/API 的具体实现形式后续确定，但长度、元素顺序和消费者内存要求不得改变。
manifest 是外部证据清单，至少记录输入文件及哈希、规范化数据、实际字体文件及哈希、Python/Pillow 等实际生成工具版本、三个产物名称/字节数/SHA-256、400×300/stride/位序/极性、PC Y 预翻转与固定 H1 Y 翻转约定。工具版本和字体必须真实读取，不能用期望版本代填。

## 发布与失败

流水线：原始输入校验 → 模型映射 → 字体与页面生成 → 预览验收 → Y 预翻转/raw → header → 字节一致性与外部 manifest 校验 → 发布完整集合。
预览验收包括缺字、溢出及可读性；人工可读性尚未确认时只能是候选产物，不称可放行集合。
失败必须报告明确类别及原因，如 INPUT_INVALID、FONT_INVALID、LAYOUT_INVALID、ENCODING_INVALID、OUTPUT_CONFLICT 或 IO_ERROR；这些是未来结果类别，不是当前函数或 CLI 已实现的返回码。
失败不覆盖旧有效产物，不把部分目录当成功结果，不自动编译/烧录。完整集合必须全部验证后才发布；不得混用不同 run-id 的预览、raw、header 或 manifest。
同一输入、时间、字体与工具环境应得到相同像素和 raw；不承诺不同库版本 PNG 编码或不同字体环境仍有相同文件哈希。

方向精确定义见 [页面布局](STEP016B_PAGE_LAYOUT.md)，RAM 输入要求见 [Display Entry](STEP016B_DISPLAY_ENTRY.md)，验收见 [测试计划](STEP016B_TEST_PLAN.md)。本轮不创建产物或工具。
