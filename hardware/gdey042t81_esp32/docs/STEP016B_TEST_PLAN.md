# STEP016B — Interface Test Plan

状态：TEST PLAN FROZEN；下列用例全部 NOT RUN，不因接口文档提交而升级为 PASS。
依据：[JSON](STEP016B_JSON_SCHEMA.md)、[Render](STEP016B_RENDER_INTERFACE.md)、[Display](STEP016B_DISPLAY_ENTRY.md)、[Layout](STEP016B_PAGE_LAYOUT.md)。

| ID | 层/案例 | 验收条件与边界 | 状态 |
| --- | --- | --- | --- |
| D1 | 必填五字段、可选默认及映射 | 内部 title/current_step/updated_at 正确，source 固定，无新模型字段 | NOT RUN |
| D2 | 0/100、越界、bool、浮点、数字字符串 | 严格整数范围，不依赖宽松类型转换 | NOT RUN |
| D3 | 非对象、未知键、混用别名、重复键、畸形 JSON | 明确拒绝，不先解析丢掉重复键后宣称通过 | NOT RUN |
| D4 | 空白文本、null、tags 长度/类型 | 规范化及拒绝符合 schema | NOT RUN |
| D5 | 缺失/非法时间、闰日、错误格式 | 不补当前时间；采用约定本地快照时间 | NOT RUN |
| R1 | 正常进度与 current_step 主标题 | 页面字段来源正确，固定标题替换经未来实现验证 | NOT RUN |
| R2 | 受控等待/错误样例 | 保留语义；无效业务输入不自动发布 | NOT RUN |
| F1 | 中文、拉丁、数字、缺字、字体回退 | 固定实际字体与哈希，缺字候选不放行 | NOT RUN |
| F2 | 长标题/步骤/描述/标签、来源/时间 | 无越界、重叠或不可读内容；必要时拒绝候选 | NOT RUN |
| E1 | PNG模式/尺寸、raw长度/位序/极性 | 400×300、1-bit，15000字节、stride50、MSB、0黑1白，无头部 | NOT RUN |
| E2 | raw 与嵌入 header | 提取数组逐字节一致；header文件哈希不冒充raw哈希 | NOT RUN |
| O1 | 四角及非对称图案、中文 L→T→P | 用独立预期比较，合成恒等，无额外rotation | NOT RUN |
| A1 | 相同输入/时间/字体/工具重复生成 | 像素/raw一致；run-id不影响页面 | NOT RUN |
| A2 | 输出冲突、中途失败、版本混用 | 不覆盖既有发布集合；不发布部分结果或混合run-id | NOT RUN |
| A3 | 外部 manifest | 输入/字体/三产物哈希真实可复核，无自引用 | NOT RUN |
| B1 | 独立入口、默认两环境与冻结H1 | 默认保护不变，无网络/轮询依赖，未改历史入口 | NOT RUN |
| B2 | 私有配置缺失/错误、帧长度错误 | 拒绝且无静默回退；有效RAM缓冲满足pgm=false | NOT RUN |
| B3 | 执行调用链 | 正常init/prepare/FULL激活0/0/1，返回后零显示命令；仅静态证明 | NOT RUN |
| S1 | Python回归与新增测试 | 既有125项不回归，新增数量分开报告，不把历史结果当本轮结果 | NOT RUN |
| S2 | 主机C++运行测试 | 有编译器才运行；不可用则BLOCKED/NOT RUN，不安装绕过 | NOT RUN |
| H1 | 新业务页实机显示 | 独立批准后记录上传、过程及最终图；使用不同于旧图的内容 | NOT RUN |
| H2 | 实机中文/物理方向 | FPC朝下正常阅读、非对称标记匹配，不冒充逐像素穷举 | NOT RUN |
| H3 | 单次FULL与失败停驻 | 过程观察与源码性质分开；照片不能计数，错误不立即重刷 | NOT RUN |
| H4 | BUSY timeout故障注入 | 先批准安全方案；验证故障与后续命令，不由正常显示推断 | NOT RUN |
| X1 | Deep Sleep、Partial/Fast Refresh | 不属第一版，各自专项定义并批准后测试 | NOT RUN |
| X2 | 长期稳定性、电气/热/功耗 | 单独定义测量和时长，不由静态画面推断 | NOT RUN |

未来实机证据须区分：用户报告、照片直接内容、源码静态性质、运行时日志与仪器读数。H1 原有 limited-scope PASS 不覆盖新业务入口、字体或方向组合。
所有硬件用例均须另行批准，无上传命令、无本轮设备访问。失败保留证据，不自动修固件或重试。

## 本轮文档验收

只验证五份文档交叉引用、字段/格式一致性、空白、敏感信息、git diff与精确提交范围；这些是文档检查，不是上述功能用例运行结果。
保持 STEP016A、源码、API、模型、配置、H0/H1与原始 evidence 不变。只创建本地文档提交，不推送、不打标签。
