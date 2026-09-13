# STEP016D — Display Test Plan

状态：TEST PLAN FROZEN。下表是未来STEP016D用例，全部NOT RUN；本轮只检查设计文档和已有产物记录。
基线：`45ca1dcc0e9043639299621229a223c7f0eca7de`。STEP016C历史203 passed不是本轮新测试结果。
契约：[Bitmap](STEP016D_BITMAP_INTERFACE.md)、[Embed](STEP016D_FRAME_EMBED_DECISION.md)、[Flow](STEP016D_DISPLAY_FLOW.md)、[Orientation](STEP016D_ORIENTATION_RULE.md)。

| ID | 未来测试 | 验收条件及证据边界 | 状态 |
| --- | --- | --- | --- |
| S1 | PNG输入及来源 | 400×300、mode 1、哈希匹配；损坏/错误尺寸/错误模式拒绝，不静默缩放或改方向 | NOT RUN |
| S2 | raw编码 | 精确15000字节、stride50、MSB-first、0黑1白、无头；独立解码覆盖字节边界及首末像素 | NOT RUN |
| S3 | header一致性 | 提取完整数组与raw逐字节相同；长度错误/缺失拒绝 | NOT RUN |
| S4 | 可重复性与manifest | 固定输入/字体/工具的像素和raw一致；输入及三产物大小/哈希可复核，无自身哈希 | NOT RUN |
| S5 | 输出失败 | 目录冲突、生成中断、错误输入不得覆盖旧结果或发布混合/部分集合 | NOT RUN |
| O1 | L→T→P | 独立预期的不对称角标与中文；各边界一次翻转、最终等于L，无额外rotation | NOT RUN |
| B1 | 构建隔离 | 专用入口独立；默认两环境和冻结H1不变；无网络/JSON/UI执行流程 | NOT RUN |
| B2 | 配置/帧失败 | 缺失或错误私有配置、缺帧/长度错误拒绝，无默认回退 | NOT RUN |
| B3 | 存储及产物 | 核对只读帧存储、完整静态RAM加载；记录工具版本、退出码、RAM/Flash、BIN/ELF路径/大小/SHA-256 | NOT RUN |
| B4 | 静态执行审计 | 初始化/准备/最终FULL刷新数0/0/1，双RAM完整写入，最终refresh返回后显示命令0；不冒充实测计数 | NOT RUN |
| R1 | Python回归 | 以既有203项为基线另加导出测试，实际通过数分别记录，不预填结果 | NOT RUN |
| H1 | 首次新页面上传 | 另行批准；检查构建产物一致、端口/硬件，保存真实上传证据；成功不等于显示成功 | NOT RUN |
| H2 | 显示与物理方向 | 不同于旧图的业务内容；FPC朝下、中文可读、左右及非对称参照与L一致；保存最终照片 | NOT RUN |
| H3 | 单次FULL观察 | 保存启动到停驻的过程观察/视频及来源；单张静态照片不能证明次数，旧保持画面不能证明新刷新 | NOT RUN |
| H4 | BUSY故障注入 | 独立安全方案批准后验证超时及后续命令；正常显示或源码不能替代故障注入 | NOT RUN |
| X1 | Deep Sleep / Partial / Fast | 不纳入本版，需专项评审及批准 | NOT RUN |
| X2 | 长期稳定性/电气/功耗 | 独立定义仪器、时长和失败条件；不从静态画面推断 | NOT RUN |

## 放行与失败纪律

未来软件导出和编译通过仅允许记录软件/编译预检通过；不能改成物理PASS。
未来实机操作须另行明确授权，本轮无上传命令、串口访问、编译或硬件动作。
首次实验不自动开serial monitor、不循环刷新、不测试网络或休眠；白屏、黑屏、无变化、方向错误、超时或异常闪烁只记录，不立即修改、重刷或重试。
证据区分用户报告、照片、过程观察、源码、运行日志与仪器测量；原始日志/照片继续hardware/evidence/本地未跟踪，不纳入文档提交。

## 本轮设计验收

只核对五份文档交叉链接、接口及方向一致性、格式/敏感信息、Git差异和精确暂存清单。
文档完成后更新PROJECT_STATE.md为STEP016D-A DESIGN FREEZE COMPLETE，实现/编译/实机仍NOT RUN。
H0/H1历史及STEP016C完成记录保持不变，PRODUCT FUNCTION VERIFIED=NO。
