# STEP016D — Frame Embed Decision

状态：DESIGN FROZEN；IMPLEMENTATION / COMPILATION / PHYSICAL VERIFICATION = NOT RUN。
基线：`45ca1dcc0e9043639299621229a223c7f0eca7de`。

## 方案比较

占用分析仅为设计估算，不是编译或实测结果；完整帧固定15000字节。当前PNG样例为1619字节，但其他页面压缩大小不固定。

| 方案 | Flash | RAM | 复杂度及H1兼容性 | 决策 |
| --- | --- | --- | --- | --- |
| A：PNG运行时解码 | PNG内容加解码器代码，未测总量 | 完整帧15000字节加解码工作区，未测峰值 | 新增解码和失败路径；仍需转换为H1完整RAM帧 | 不选 |
| B：PC离线转C数组，编译嵌入 | 固定帧数据15000字节，另有代码/对齐开销 | 独立完整静态RAM缓冲15000字节，另有运行开销 | 无MCU图像解码；直接满足已冻结H1输入约束 | 选择 |
| C：链接器嵌入raw | 原始帧15000字节加对齐开销 | 同样需完整RAM缓冲15000字节 | 无解码，但增加链接符号/构建绑定；H1输入要求不变 | 本版不选 |

采用B与 [B Display Entry](STEP016B_DISPLAY_ENTRY.md) 一致。C数组文本体积不是固件Flash占用；Flash/RAM总量和峰值须未来构建/验证，不在设计阶段宣称已通过资源验收。

## 冻结的存储与加载方式

PC人工运行一次构建前转换，生成 [Bitmap接口](STEP016D_BITMAP_INTERFACE.md) 定义的raw及header；不新增自动转换钩子、自动上传或网络流程。
header内完整数组以只读嵌入存储进入固件，未来以链接映射验证实际存储段及长度；缺失或长度错误时拒绝构建。
启动时通过针对固定ESP32工具链审查过的复制方式，把全部15000字节复制到独立静态RAM缓冲，存活至少至刷新返回。
不在栈上分配整帧，不把未经审查的Flash/PROGMEM指针直接作为 `pgm=false` 输入，也不为此改动H1参数。

设备不读取PNG、JSON、SD或串口文件。更换业务页需要新的PC产物和固件构建；上传另行批准。
本轮不创建数组、加载代码或新环境。执行约束见 [Display Flow](STEP016D_DISPLAY_FLOW.md)，未来字节一致性与存储核验见 [测试计划](STEP016D_DISPLAY_TEST_PLAN.md)。
