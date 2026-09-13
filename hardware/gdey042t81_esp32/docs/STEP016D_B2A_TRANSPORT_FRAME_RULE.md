# STEP016D-B2A — Transport Frame Rule

状态：RULE FROZEN；测试内数学模型验证通过，不是生产适配器或实机放行。
基线：`84886cc15af2bec7d220e062865450927fcfaacc`。
承接 [D-A方向契约](STEP016D_ORIENTATION_RULE.md)、[Bitmap接口](STEP016D_BITMAP_INTERFACE.md)、[嵌入决策](STEP016D_FRAME_EMBED_DECISION.md)、[显示流程](STEP016D_DISPLAY_FLOW.md) 及 [B1报告](STEP016D_B1_FRAME_CONVERTER_REPORT.md)。

## 1. L与T定义

L是STEP016C Renderer的正常阅读页面；B1将PNG编码成progress.logical.raw及C数组，仍保持L坐标。PNG压缩文件字节不等于raw帧。
T是未来PC Transport Adapter生成、供固定H1路径使用的传输帧。B1产物不是T，不得直接作为正向H1传输帧放行。
两者均400×300，左上原点，x向右、y向下。P为正视屏幕、FPC朝下的物理坐标；新业务页的P仍待实测。

## 2. 像素与字节映射

源像素位置映射与目标采样公式分别为：

```text
x_T = x_L
y_T = 299 - y_L
T(x,y) = L(x,299-y)
```

L和T均精确15000字节、stride 50、row-major、MSB-first、0黑1白、无头部或padding。

```text
T[50*y+b] = L[50*(299-y)+b]    y=0..299, b=0..49
offset(x,y) = 50*y + floor(x/8)
mask(x) = 0x80 >> (x % 8)
```

只反转300行的顺序；行内50字节顺序、每字节bit7至bit0顺序及黑白极性不变。
原帧首行到目标末行，原帧末行到目标首行；x=0/7/8/399保持同一列和位掩码。
转换是对合：f(f(L))=L。哈希通常不同但不保证不同，对称帧可能T=L；哈希只能确认字节身份，不能独立证明方向正确。

## 3. 方案选择与责任

| 方案 | H1兼容性与重复翻转风险 | 可测试性与可追溯性 | 决策 |
| --- | --- | --- | --- |
| PC独立L→T适配 | 保持H1；在一个明确边界行反转 | 可逐像素独立核对，分别记录L/T哈希 | 唯一选择 |
| MCU入口处理L | 增加运行时方向逻辑，容易与H1固定翻转混淆 | 需另审代码和构建，PC产物不能直接表示传输方向 | 不选 |
| 修改H1 mirror或增加rotation | 改动冻结方向基线，或引入额外变换 | 需重新审计和实测，超出范围 | 不选 |

```text
Renderer / B1：L（不翻转）
  → 未来PC Transport Adapter：T(x,y)=L(x,299-y)
  → MCU复制到有效RAM：字节不变
  → 固定H1 mirror_y=true：P(x,y)=T(x,299-y)=L(x,y)
```

未来PC Adapter独占一次L→T行反转。固定H1的翻转属于T→P边界，不是新增的应用层翻转；两处相互抵消不是同一边界重复转换。
这是当前固定软件/面板路径的契约，不推广为所有SSD1683配置的固有属性。

## 4. 禁止事项与执行边界

- Renderer不翻转；B1不翻转；MCU加载不翻转；PC适配不得叠加另一个mirror开关或rotation。
- 不改变H1的invert=false、mirror_y=true、pgm=false；不加入GFX rotation。
- 本轮不实现生产Adapter、不生成业务T raw/header、不接入ESP32、不编译或操作硬件。
- 未来仍按完整双RAM准备、一次标准FULL、刷新返回后零显示命令执行；不得增加补写、清屏、重试、powerOff或hibernate。
- PROJECT_STATE.md及历史设计不修改；其D-A历史阶段条目不冒充B1/B2A最新执行记录，分别以阶段报告为准。

## 5. 验证与未完成项

本轮 [纯数学测试](../../../tests/test_transport_frame_rule.py) 只使用内存合成帧，不导入或执行H1、不写出帧文件。
独立像素模型验证全部120000个合成逻辑像素，与按行字节模型一致；不等于物理像素验证。
测试结果及可复核哈希见 [B2A测试计划](STEP016D_B2A_TRANSPORT_TEST_PLAN.md)。

生产适配、业务T产物、固件集成、构建及新业务页实机方向/显示验证：NOT RUN。
H0 PASS、H1 PASS (limited scope)保持历史边界；PRODUCT FUNCTION VERIFIED=NO。
