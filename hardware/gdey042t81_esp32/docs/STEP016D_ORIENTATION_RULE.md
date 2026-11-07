# STEP016D — Orientation Rule

状态：DESIGN FROZEN；新业务传输方向实现和实机验证 NOT RUN。
基线：`45ca1dcc0e9043639299621229a223c7f0eca7de`。
沿用 [A架构](STEP016A_ARCHITECTURE_FREEZE.md)、[B布局](STEP016B_PAGE_LAYOUT.md) 和 [H1固定参数](../src/h1/contract.h)。

## 三个独立坐标系

三个帧均400×300，左上原点，x右、y下。

| 帧 | 定义 | 谁负责 |
| --- | --- | --- |
| L | 正常可读业务页面，STEP016C progress.preview.png | 已有Python Renderer；不改方向 |
| T | 预翻转后的raw/header传输帧 | 未来PC离线导出边界 |
| P | 正视实体屏幕，FPC朝下的物理帧 | 固定H1 mirror_y=true路径；新页面仍需实测 |

```text
T(x,y) = L(x,299-y)
P(x,y) = T(x,299-y) = L(x,y)
```

这是已确认的两个不同边界各一次Y翻转；不是在同一边界重复翻转。
“不能同时发生两次翻转”在本次评审已澄清为：禁止每个边界重复翻转及任何额外rotation，不取消上述相互抵消的两次变换。
Renderer不预翻转；PC导出一次；H1固定翻转一次；MCU加载只复制字节、不翻行。

## 禁止混淆

- 直接把L按raw打包交给固定H1不能当成最终正向页面，导出补偿不能遗漏。
- 不同时使用手动倒行与另一个导出mirror开关；不加GFX rotation或其他隐式方向处理。
- 字节内MSB-first位序不是Y翻转；先确定T行序，再按 [Bitmap接口](STEP016D_BITMAP_INTERFACE.md) 打包。
- PNG预览始终是L，不能拿倒置的T代替业务预览。
- Y mirror是当前固定软件/面板路径的契约，不是所有SSD1683配置的固有属性。

## 验证边界

组合恒等目前是设计结论，不等于新业务页已物理验证。
未来独立解码raw/header，使用不对称角标与中文测试L→T→P；实机照片用FPC、可读文字及物理左右参照锚定P，区分PHOTO FRAME与P。
不能只比较PNG与未经规范化的照片，也不能用正常显示证明逐像素穷举或刷新次数。
具体软件与实机验收见 [Display Test Plan](STEP016D_DISPLAY_TEST_PLAN.md)。
