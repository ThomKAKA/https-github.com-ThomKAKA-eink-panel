# STEP016D-B2B — Embedded Frame Integration Report

基线：`e1fa8b94f357d5878ffedc4b0ac94421fbea5fb8`。
状态：PC TRANSPORT ADAPTER / EMBEDDED ENTRY / COMPILATION COMPLETE。
新业务页物理显示验证、STEP016D-C：NOT RUN；本报告不是上传授权。

## 1. 修改与保护范围

新增 [Transport Adapter](../../../panels/transport_adapter.py)、[测试](../../../tests/test_transport_adapter.py)、[Progress入口](../src/progress/main.cpp)、[配置检查](../src/progress/config.h)、[T数组](../src/progress/progress_frame.h) 和本报告。
修改 [PlatformIO](../platformio.ini) 仅追加10行专用环境；全部检查通过后更新 [PROJECT_STATE](../../../PROJECT_STATE.md)。
Renderer、B1工具、B2A规则及数学测试、H0/H1源码和第三方依赖不修改。
原始evidence不修改、不提交；私有配置、转换产物、构建日志和隔离检查副本均在已有忽略目录。

## 2. T帧来源与PC接口

B2A只有规则及数学模型，没有业务T产物。本轮依据 [冻结规则](STEP016D_B2A_TRANSPORT_FRAME_RULE.md) 实现独立PC Adapter，不改变 [B1](STEP016D_B1_FRAME_CONVERTER_REPORT.md) 的L编码行为。
在仓库根目录手动调用（新run-id，不自动编译）：

```powershell
& '.\.venv\Scripts\python.exe' -B -m panels.transport_adapter `
  --input-dir 'artifacts/step016-frame-converter/step016d-b1-review' `
  --run-id '<new-run-id>'
```

读取B1清单及固定文件名的raw/header，校验阶段、L方向、尺寸/格式、长度、哈希及B1数组完整一致；重复JSON键也拒绝。
PNG来源字段继承B1记录，通用raw API不声称重新认证PNG；本轮另行读取实际冻结PNG并验证其打包像素等于L。
哈希和清单是完整性/来源记录，不是签名认证，不能防止同时伪造数据与清单。

唯一转换：`T[50*y+b] = L[50*(299-y)+b]`。保持400×300、15000字节、stride50、MSB-first、0黑1白。
检查和生成先在内存完成；输出目录/文件独占创建，transport-manifest.json最后发布。不复用失败目录、不覆盖旧结果；无完整清单的目录不放行。
它是Transport阶段清单，不是完整Renderer发布manifest；不记录自身哈希。

本轮目录（相对仓库根）：

- PNG：`artifacts/step016-offline-progress/step016c-final-20260913/progress.preview.png`
- B1：`artifacts/step016-frame-converter/step016d-b1-review/`
- T：`artifacts/step016-transport-adapter/step016d-b2b-review/`

| 对象 | 大小 | SHA-256 |
| --- | --- | --- |
| 输入PNG | 1619 | 538be61374b7804bc64a05dd1eb4f6caca65a778201d2e03ddbae8f7aedb0c2a |
| B1 converter-manifest.json | 1147 | f9bac58212430b18a3fcf982e1814c2491b22b649280189b5088196f533cface |
| L logical raw | 15000 | b482dfb702fb425b9734bc1824ed02587fd428516b0aea2edacfaa3718e54209 |
| T progress.frame.raw / 数组字节内容 | 15000 | a243c5740472d3f2f3c09ca440446d2e50b5da0b32bcb00b6ddca533f6084f8d |
| progress_frame.h文件（本轮LF字节） | 94727 | 8c1814143bdf489c43a1032509ff91c2e0264dbf6fccab3834d942e8ac394e68 |

生成header原样复制到src/progress并提交，数组15000个uint8_t；header文件哈希不等于数组哈希。Git换行转换可能影响后续检出header的文本哈希，不改变数组内容，复核时必须区分。
header只用标准整数/长度头文件，记录T坐标、几何及来源哈希；无Arduino/PROGMEM依赖。
业务PNG→L及T→模拟P逐像素一致；这只验证120000个逻辑像素，不是实机读回。

## 3. 调用链与H1保护

原H1保持：`kPattern RAM → SPI → coldInit → prepareColdStartFullFrame → refreshOnce → 时间/BUSY判定 → delay停驻`。

新入口：

```text
编译期检查T声明、400×300、stride50、sizeof数组=15000
→ memcpy完整只读T数组到15000字节静态frame_ram（不翻转）
→ SPI.begin
→ 原样H1 coldInit（initial=true、4MHz、fast-full关闭）
→ 原样prepareColdStartFullFrame（0,0,400,300；pgm=false）
→ 原版GxEPD2完整写previous 0x26、current 0x24
→ 原样refreshOnce：标准FULL 0x22=0xF7 → 0x20
→ 原样无符号耗时/BUSY判定，MCU-only停驻
```

未复制驱动，未修改_initial_write处理、初始化、FULL或BUSY策略。固定invert=false、mirror_y=true、pgm=false保持。
PC仅一次L→T行反转；MCU复制不变；H1固定映射后模型P=L。不能泛化成所有SSD1683配置的固有方向。
刷新返回后EPD命令为0；没有补写、清屏、重试、powerOff或hibernate。软件返回条件满足不记为显示实测PASS。
完整RAM写入是源码推导；不证明控制器确认、掉电原子性或库内其他前置BUSY等待超时后立即中止。BUSY故障注入仍未测。

新环境esp32-m1-progress继承esp32-m1，仅选择progress/main.cpp；冻结H1入口及默认环境不改。
两个默认环境会扫描到新文件，但专用宏未定义，其翻译单元为空；旧三环境ELF均无Progress frame符号。
新环境保留复用H1所需宏，并增加EINK_PROGRESS_EMBEDDED_TEST；私有目录独立为`.build/progress-private/`。
配置复用原H1断言，另要求PROGRESS_PRIVATE_PROFILE=1；GPIO BUSY/RST/DC/CS/SCK/MOSI=13/12/14/27/18/23。
私有配置不提交，其他检出副本未提供配置时应构建失败，不允许静默回退。

## 4. 测试与构建结果

- 修改前回归：270 passed in 2.90s。
- 新增Python测试：41 passed in 0.61s。
- 完整Python回归：311 passed in 3.00s。
- 覆盖来源错误/缺失、格式、哈希、数组不一致、重复键、非对称方向、位边界、B2A黄金哈希、可逆性、失败发布、重复生成及入口隔离。
- 现有项目.venv：Python 3.12.14；使用已有依赖，无安装升级。

构建使用`.venv-hw/Scripts/python.exe -B -m platformio run --project-dir hardware/gdey042t81_esp32 -e <env>`。
仅在进程内设置PLATFORMIO_CORE_DIR到项目`.venv-hw/pio-core`，关闭遥测；未执行上传/串口命令。
PlatformIO 6.1.19；espressif32 6.12.0；Arduino包3.20017.241212+sha.dcc1105b；Xtensa 8.4.0+2021r2-patch5；GxEPD2 1.6.9固定de82887；Adafruit GFX 1.12.6。
新环境依赖缓存从已有H1缓存原样复制并核对哈希。无依赖下载/安装/升级；1930个基线文件最终仅允许PROJECT_STATE.md和platformio.ini变化，其余保持。

| 环境 | 退出码 | RAM bytes | Flash bytes |
| --- | --- | --- | --- |
| esp32dev | 0 | 36696 | 285241 |
| esp32-m1 | 0 | 36696 | 285241 |
| esp32-m1-h1 | 0 | 21616 | 294689 |
| esp32-m1-progress | 0 | 36616 | 294725 |

下表产物均位于`hardware/gdey042t81_esp32/.pio/build/<环境>/firmware.<类型>`：

| 环境 / 类型 | 文件bytes | SHA-256 |
| --- | --- | --- |
| esp32dev / bin | 285600 | 603de0a11e8809f3697ac3e98516d04d406c13ebc996cb436114e518374e5574 |
| esp32dev / elf | 7004404 | b3c597ae5497494c86f5c91c091e89f844ff5cdc04246879457091a30c81e9e0 |
| esp32-m1 / bin | 285600 | af37ef2757a3d2ffe9356eed217c41ec0c7f44f25a1cfe726d2a745fdd4ac6d6 |
| esp32-m1 / elf | 7004692 | 142fd73b618aee85cb828b47744795b3442b1ca3953d9e7d07da4e6e1f092ffe |
| esp32-m1-h1 / bin | 295056 | 4651616d92e03009b69eb260de11bcd548d4504504ee6931bdbbcafe7e2f8ed1 |
| esp32-m1-h1 / elf | 6735708 | 3cf68337ef9173615427f44b323cf1aac8367efaafeff5ab7d75f805cbb4fecd |
| esp32-m1-progress / bin | 295088 | 942f7eaa9a7ad6574ee36a05478d085d52440d0578c82ed0457a7c65ac241523 |
| esp32-m1-progress / elf | 6721320 | a5c170fe154e8a4df6b978342d274b48b270cf1dcbff34f23011b4ecc41302f1 |

构建日志、退出码文件、compile_commands.json、负向编译日志及build-verification.json均位于`artifacts/step016-b2b-build/`，保持忽略。
固件文件哈希标识本次构建，不声称跨构建时间/目录可重现。

## 5. 编译拒绝与ELF核验

基于PlatformIO导出的实际编译参数，使用现有Xtensa编译器对`.build/b2b-negative/`隔离副本执行-fsyntax-only；不是运行固件，也不反复全量链接。

| 副本 | 退出码 | 核验结果 |
| --- | --- | --- |
| valid | 0 | 正常入口编译通过 |
| missing_frame | 1 | 缺progress_frame.h拒绝 |
| wrong_length | 1 | Complete frame required断言失败 |
| wrong_coordinate | 1 | Transport frame required断言失败 |
| missing_private | 1 | 缺display_config.local.h拒绝 |
| wrong_pins | 1 | H1原有GPIO断言失败 |

使用现有pyelftools/工具链nm读取正式Progress ELF：

- progress_frame：`.flash.rodata`、地址0x3f400240、15000字节，提取后与T raw逐字节一致。
- frame_ram：`.dram0.bss`、地址0x3ffc1c7c、15000字节静态缓冲；不是栈上帧。
- 此工具链聚合`.flash.rodata`的ELF flags为3（含W），不能单凭flags断言只读；固定memory.ld把DROM定义为`drom0_0_seg (R)`，地址0x3F400020起，数组位于该Flash映射区。
- memcpy源码及存储检查证明集成结构，不是运行时RAM复制或物理显示实测。

辅助检查曾遇自定义配置路径定位失败，改为进程级extra script后成功导出编译数据库；ELF检查也按实际链接段澄清flags含义。均未修改正式工具链或H1。

## 6. 未完成项与提交边界

STEP016D-C / 新业务页上传、中文/方向物理观察、运行时RAM核验：NOT RUN。
BUSY故障注入、Deep Sleep、Partial/Fast Refresh、长期稳定性：NOT TESTED。
H0 PASS及H1 PASS (limited scope)不扩大；PRODUCT FUNCTION VERIFIED=NO。
未加入网络、JSON运行时解析、页面生成或循环刷新。
本地提交信息：`feat(display): integrate embedded progress frame`。
不提交原始evidence、私有配置或构建产物；不推送、不打标签，完成后停止。
