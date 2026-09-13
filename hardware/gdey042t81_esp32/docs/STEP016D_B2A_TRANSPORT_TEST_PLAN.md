# STEP016D-B2A — Transport Test Plan

状态：规则数学验证完成；生产转换及硬件阶段未执行。
基线：`84886cc15af2bec7d220e062865450927fcfaacc`。
规范见 [L→T规则](STEP016D_B2A_TRANSPORT_FRAME_RULE.md)；测试见 [test_transport_frame_rule.py](../../../tests/test_transport_frame_rule.py)。

## 1. 本轮已执行：仅数学与Python回归

| 检查 | 方法与验收 | 结果 |
| --- | --- | --- |
| 长度 | 拒绝0、14999、15001字节；有效输入输出15000字节 | PASS |
| 坐标和字节映射 | 独立逐像素搬运再打包，对比整行倒序，遍历120000像素及15000字节 | PASS |
| 非对称四角 | 四个不同角标字节，确认上下互换、左右及位序不变 | PASS |
| 位边界和首末行 | 单黑像素x=0/7/8/399，y=0/1/298/299，共16组 | PASS |
| 极性与对称帧 | 全黑、全白、重复0x81不变；允许L/T同哈希 | PASS |
| 可逆性 | f(f(L))=L | PASS |
| 固定H1合成 | 用独立像素模型模拟T→P，结果P=L；未执行H1代码 | PASS |
| 哈希 | 固定合成数据的L/T SHA-256与golden值一致 | PASS |

测试模型仅存在于测试文件，无生产API、CLI、raw/header或业务传输产物。
整行模型与逐像素模型采用不同实现，避免仅用同一个函数反转两次作为唯一证明。

## 2. 合成帧与黄金哈希

固定无随机种子算法，y=0..299，b=0..49：

```text
L[50*y+b] = (17*y + 29*b + (y*b)%251)%256
T[50*y+b] = L[50*(299-y)+b]
```

| 对象 | 长度 | SHA-256 |
| --- | --- | --- |
| 合成L | 15000 bytes | 6ef4696f9124b264ec2742728f3398ecf1d584a3855719746974f6d8af1b339a |
| 合成T | 15000 bytes | a0ade0ea621dc91f1a1a6f362d35b430981e8540b902fb83527f53cc8dcbe6b3 |

这些是内存合成测试帧哈希，不是STEP016C页面或最终固件frame哈希，不应写进业务发布manifest。

## 3. 实际运行结果

使用现有项目.venv，未安装/升级依赖：

```powershell
& '.\.venv\Scripts\python.exe' -B -m pytest -q tests/test_transport_frame_rule.py
& '.\.venv\Scripts\python.exe' -B -m pytest -q
```

- 修改前既有回归：244 passed in 2.29s。
- 新增数学测试：26 passed in 0.22s。
- 完整回归：270 passed in 2.48s（244既有＋26新增）。
- 没有执行ESP32或C/C++构建、串口或硬件测试。

## 4. 未来执行矩阵

| 阶段 | 未来验收方法 | 当前状态 |
| --- | --- | --- |
| 生产PC Adapter | 实现规则，严格长度/格式/方向来源校验；错误拒绝，不覆盖旧结果 | NOT RUN |
| 业务T raw/header | raw/header字节一致，分别记录L/T及文件哈希；重复生成一致，预览仍是L | NOT RUN |
| 中文业务方向 | 独立解码实际产物，结合非对称标记验证L→T→P，不依赖文件名判断方向 | NOT RUN |
| 构建隔离 | 新入口独立，默认保护与冻结H1不变；缺配置或帧拒绝；记录BIN/ELF大小和哈希 | NOT RUN |
| 显示流程 | 静态复核双RAM写满、一次标准FULL、fast关闭、返回后零显示命令 | NOT RUN |
| 新页面实机 | 另行授权上传；内容区别于旧图，过程观察及最终照片，FPC/可读文字锚定物理坐标 | NOT RUN |

单张照片不能证明刷新次数。新页面白屏/黑屏/无变化/超时/方向错误只记录，不立即修改或重刷。
BUSY故障注入、Deep Sleep、Partial/Fast Refresh、长期稳定性继续NOT TESTED；数学PASS不升级H0/H1或产品验证状态。
后续硬件测试承接 [D显示测试计划](STEP016D_DISPLAY_TEST_PLAN.md)，本文件不构成上传授权。

## 5. 文件与提交边界

只新增本文件、规则文档及数学测试；PROJECT_STATE.md、Renderer、B1、H1、ESP32、PlatformIO、第三方库及原始evidence不修改。
提交信息：`docs(display): freeze L to T transport frame rule`。
原始evidence保持local-only未跟踪；不推送、不打标签、不进入ESP32集成。
