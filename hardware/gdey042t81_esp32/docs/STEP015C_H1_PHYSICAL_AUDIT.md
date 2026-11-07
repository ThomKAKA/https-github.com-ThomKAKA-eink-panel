# STEP-015C — H1 physical verification closure

审查日期：2026-09-11。实现基线：`55e32b5e788d762cc3a08587ccceb45e457bed20`。

## 结论与证据等级

`H1 PHYSICAL TEST = PASS (limited scope)`。
这是用户报告的首次 H1 实验、保存的上传摘要、前后照片和源码静态证据的联合结论，不是独立仪器验证。

| 项目 | 结论 | 依据与边界 |
| --- | --- | --- |
| esp32-m1-h1 上传 | PASS | 用户保存的摘要含环境、目标 BIN、100% 写入、Hash of data verified、RTS reset、SUCCESS |
| COM11 烧录链路 | PASS | 摘要 SOURCE / DEVICE 和 Using manually specified: COM11；本轮不访问端口 |
| GDEY042T81 显示链路响应 | PASS，用户报告结合照片 | 用户确认首次 H1 实机测试通过；照片确认最终测试图内容 |
| 单次标准 FULL 显示观察 | PASS，用户报告结合静态路径 | B1 正常单次启动路径为一次标准 FULL；无视频、命令追踪或运行时串口日志直接计数 |
| 无明显异常闪烁、观察期间稳定 | PASS，用户观察 | 本地观察记录无连续闪烁、无异常刷新循环；未提供观察时长 |

`HARDWARE VERIFIED = YES (display chain only)`。
`DISPLAY VERIFIED = YES (single full refresh observation; user-reported, not instrumented)`。
`PRODUCT FUNCTION VERIFIED = NO`。

## 照片核对与方向

两张照片均可见实体屏幕、FPC、板卡及 L/R 标记。before 照片 FPC 朝下；after 照片 FPC 在右，顺时针旋转 90°的坐标解释可恢复 FPC 朝下、L 左 R 右。
规范化后均可见全屏外框、横纵十字、中央实心块、左下实心角块、右下空心框，与 [H1 测试图](../src/h1/pattern.h) 经唯一 Y 翻转的预期一致。
这里只核验几何特征，不宣称逐像素穷举一致，也未修改或旋转保存原照片。

重要限制：上传前已经显示相同测试图。两张静态照片本身不能排除旧图保持，不能独立证明新固件执行了刷新、刷新次数或时间稳定性。
本轮接受用户对 H1 实验成功及单次 FULL 观察的明确报告；本地 observation 文件单独只描述上传自动复位后图案保持、无循环闪烁，不能增强为波形计数证据。
观察文件中的无烟雾/热异常属于用户报告，不是照片证明的温度、电压、电流或安全认证。

## 固件与历史边界

[STEP-015A](STEP015A_H1_PREFLIGHT.md) 保留默认入口 NO-GO；[STEP-015B1](STEP015B1_H1_ATOMIC_PREFLIGHT.md) 保留当时 compile/static only、UPLOAD NOT RUN 的历史记录，不追改历史结论。
本步骤仅验证专用 `esp32-m1-h1`，不等于默认产品入口已通过实机验证。
按 B1 源码审计：cold init(initial=true)、fast-full 禁用、0x26 后 0x24 完整写入、一次普通 FULL、refresh 返回后显示命令为零。
这些仍是源码性质；完整 RAM 写入未读回，超时后零命令未通过故障注入实测。
上传摘要不含 BIN SHA-256、完整分区写入明细或运行时启动日志，不能据此独立证明上传字节与 B1 BIN 完全一致或所有分区逐一校验。

## 未验证项目

- BUSY timeout fault injection / 故障路径：NOT TESTED。
- Deep Sleep、Partial Refresh、Fast Refresh：NOT TESTED。
- 长时间运行、长期稳定性、逐像素映射：NOT TESTED。
- Wi-Fi、HTTP、frame fetching、产品 renderer / 事件流程：NOT PHYSICALLY VERIFIED。
- 电气测量、功耗、热安全：本轮未验证。

## 证据与检查

文件、大小、当前真实 SHA-256 和来源见 [H1 证据清单](STEP015C_EVIDENCE_MANIFEST.md)。原始 evidence 与本地 manifest 均不提交。
日志为用户整理保存的上传摘要（含人工来源说明），不是自动生成的原始 PowerShell transcript；字段存在不等于独立鉴真。
此前自引用旧哈希及错误文件归属已被当前实际文件哈希替代，不再用旧值作为验收依据；本轮不再修改上传日志。

项目 Python 回归：`.venv/Scripts/python.exe -B -m pytest -q`，125 passed in 1.11s，退出码 0。
提交前检查新增文档的本地链接、空白、敏感信息模式和暂存 diff；仅允许本报告和证据清单进入提交。
本轮无源码、固件、配置保护、第三方库或 H0 基线修改，无重新构建、串口访问或硬件操作；不推送、不打标签。
