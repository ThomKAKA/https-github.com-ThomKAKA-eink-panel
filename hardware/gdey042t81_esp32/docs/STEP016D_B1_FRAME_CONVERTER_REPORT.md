# STEP016D-B1 — Frame Converter Report

基线：`e0eb4df614c6d424327b9bf7ce6022db525147dd`。
状态：PC LOGICAL FRAME CONVERSION IMPLEMENTED AND TESTED；不是ESP32集成或实机放行。

## 已确认的本轮范围

本轮按用户确认，只把正常阅读PNG转换为L坐标raw和C数组，pixel mapping unchanged；无rotate/flip/mirror。
[D-A方向契约](STEP016D_ORIENTATION_RULE.md) 的T传输帧仍需要L→T预翻转。本轮不实现此步骤，不修改历史契约或固定H1的mirror_y规则。
因此使用独立 logical 文件名，不能把这些L产物直接冒充 [D-A Bitmap接口](STEP016D_BITMAP_INTERFACE.md) 的正向H1传输帧。
PROJECT_STATE.md依用户要求保持不变；B1状态以本报告为准，阶段冻结另行处理。

## 工具接口

实现：[panels/frame_converter.py](../../../panels/frame_converter.py)。测试：[test_frame_converter.py](../../../tests/test_frame_converter.py)。

在仓库根目录手动调用（run-id必须是未占用的安全目录名）：

```powershell
& '.\.venv\Scripts\python.exe' -B -m panels.frame_converter `
  --input 'artifacts/step016-offline-progress/step016c-final-20260913/progress.preview.png' `
  --run-id '<new-run-id>'
```

`<new-run-id>`为占位符，执行时替换；不能复用本次示例目录。
仅接受实际PNG、单帧400×300、mode 1；损坏、错误尺寸/模式、动画、透明度语义或非默认EXIF方向均拒绝，不自动转换/缩放/裁剪。
CRC验证与像素加载分开进行，以满足Pillow verify须紧随open的要求。
raw按row-major、stride50、MSB-first、0黑1白打包，无头部，精确15000字节。
header含include guard、stdint.h/stddef.h、static const uint8_t数组和sizeof长度定义；无Arduino/PROGMEM依赖。
注释记录源PNG及输入/raw哈希和L方向警示；header自身哈希仅写外部converter-manifest.json，manifest不记录自身哈希。
校验在内存完成，目录/文件独占创建，完整清单最后从pending改名；失败目录不复用、不视为完成，不覆盖旧结果。

## 本次示例与SHA-256

输入（相对仓库根目录）：
`artifacts/step016-offline-progress/step016c-final-20260913/progress.preview.png`

输出目录（已忽略）：`artifacts/step016-frame-converter/step016d-b1-review/`。

| 对象 | 大小/长度 | SHA-256 |
| --- | --- | --- |
| 输入PNG | 1619 bytes，400×300，1-bit | 538be61374b7804bc64a05dd1eb4f6caca65a778201d2e03ddbae8f7aedb0c2a |
| progress.logical.raw | 15000 bytes | b482dfb702fb425b9734bc1824ed02587fd428516b0aea2edacfaa3718e54209 |
| progress_logical_frame.h | 94432 bytes（源文件大小，不是Flash占用） | 461165a17acfa5b0b67c4d2e3ba9d4336656ae1451fe6cd6eb0a894649f6f632 |
| progress_logical_frame数组内容 | 15000个uint8_t元素 | b482dfb702fb425b9734bc1824ed02587fd428516b0aea2edacfaa3718e54209 |

伴随converter-manifest.json记录coordinate_frame=L、输入/输出哈希、长度、工具版本和未执行边界；不是完整发布manifest.json。
环境：项目.venv，Python 3.12.14、Pillow 11.3.0；未安装或升级依赖。

## 验证结果

- 新增测试：41 passed in 0.35s。
- 完整Python回归：244 passed in 2.32s（既有203＋新增41）。
- 覆盖格式/尺寸/模式、损坏、动画、透明度、方向元数据、纯黑白、非对称图案和首末/字节边界像素。
- 独立顺序解码核对全部120000个逻辑像素，与PNG一致，无几何变化；不是物理像素验证。
- header数组独立提取后与raw逐字节一致，长度15000；记录大小和SHA-256重新计算一致。
- 输出冲突、路径穿越、输入失败和各阶段写入失败拒绝；没有完成清单的部分目录不发布。
- 同输入重复转换raw/header一致；Python语法检查通过。未执行C/C++编译。

## 保留边界与提交

L→T适配、ESP32集成、构建、实机方向及显示验证：NOT RUN。
既有Renderer、PROJECT_STATE.md、H0/H1、PlatformIO、GxEPD2及原始evidence均不修改。
仅提交转换工具、测试和本报告；所有生成产物保持忽略，hardware/evidence/继续local-only未跟踪。
提交信息：`feat(display): add frame converter for embedded bitmap`。
不推送、不打标签、不访问串口或操作硬件，完成后停止。
