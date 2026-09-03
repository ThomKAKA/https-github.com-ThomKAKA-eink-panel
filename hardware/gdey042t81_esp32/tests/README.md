# 验证分层

## STEP-008 历史验证结果（2026-09-03）

- 现有 Python：`125 passed in 1.09s`；Python 语法编译检查通过。
- ESP32 构建：`PlatformIO unavailable`，未构建、未烧录。
- Host C++：当前没有可用 C++ 编译器，下面 7 组测试已编写但未执行。
- 实物：未验证。不能用 Python 回归通过或静态源码检查替代编译/硬件通过。
- `git diff --check` 通过；仅有仓库既有的 LF/CRLF 提示，没有空白错误。
- 新硬件文件：尾随空白 0、本地文档坏链接 0、敏感信息模式扫描 0 命中；未创建私有配置。
- 哈希对比确认：现有业务代码、配置、测试、UI 及原 P1 文件未改；仅 4 个入口/状态文件变化。

## STEP-011 历史状态（2026-09-03）

STEP-010 检查与文档完成，环境准备尚未完成；STEP-011 文档准备 COMPLETE，不代表工具链或实物验收完成。
PlatformIO / Arduino CLI：NOT INSTALLED（当前检测范围内未发现）。
七组主机 C++ 测试：**BLOCKED / NOT RUN**，当前 PATH 无可调用的 `g++`、`clang++` 或 `cl`，
未确认其他自定义安装位置；不安装、不构建、不运行这些测试。
检测范围、七组既有函数名称及检查内容见 [环境报告](../../../docs/H0_ENVIRONMENT_REPORT.md)。
Python 回归与本轮文档检查结果记录在 [progress](../../../progress.md)，不能作为 C++ 通过证据。
COMPILE VERIFIED=NO，HARDWARE VERIFIED=NO；H0 BLOCKED BY HARDWARE IDENTIFICATION。

## STEP-012 当前结果（2026-09-03）

- 隔离 PlatformIO Core 6.1.19 实际执行 `pio run -e esp32dev`，退出码 0；无项目源码或依赖声明修复。
- example esp32dev / 默认 H0 / 无私有配置：COMPILE VERIFIED=YES；REAL BOARD IDENTIFIED=NO、HARDWARE VERIFIED=NO。
- BIN、ELF 已生成；RAM 36,696 bytes（11.2%），Flash 285,241 bytes（21.8%）；仅描述此次受保护构建。
- 构建后 Python：`125 passed in 0.86s`；硬件环境 pip check 通过。
- 七组既有主机测试仍为 BLOCKED / NOT RUN，缺少主机 C++17 编译器。未新增 native 环境，未运行 pio test，也未使用交叉编译器伪装主机测试通过。
- 完整版本、日志和 SHA-256 见 [环境报告](../../../docs/H0_ENVIRONMENT_REPORT.md) 第 7 节；命令见 [BUILD_GUIDE](../docs/BUILD_GUIDE.md)。

## Python 隔离性

从仓库根目录运行：

```powershell
.\.venv\Scripts\python.exe -m pytest -q
git diff --check
```

本目录不被 Python 导入，不给 pytest 增加硬件前提，不更改事件、PNG/BMP 或 Panel 测试。
未通过实际删除目录来验收；采用源文件哈希对比、依赖搜索与原测试回归检查隔离。

## 纯 C++ 测试（将来已有编译器时）

`test_core.cpp` 不依赖 Arduino/GxEPD2 或实物；只需主机 C++17 编译器和标准库。
7 组检查涵盖首次 FULL、失败不推进、同帧保持、
最小间隔、5 次局刷后 FULL、FAST_FULL/禁用快刷、millis 回绕、帧布局和禁用 fetcher 不写缓冲。

以下命令只供将来获准后使用，本步骤不执行。在硬件目录运行，使用已安装的 C++17 编译器（示例 `g++`）：

```powershell
New-Item -ItemType Directory -Force .build
g++ -std=c++17 -Wall -Wextra -Werror -Iinclude -Isrc tests/test_core.cpp src/refresh_policy.cpp -o .build/test_core.exe
.\.build\test_core.exe
```

期望输出 `7 core test groups passed`。不要加 `-DNDEBUG`，否则会关闭断言。
这些测试是主机逻辑测试，不是 ESP32 固件构建，也不验证真实驱动时序。

## ESP32 编译（将来已有 PlatformIO 时）

工作目录、工具与权限前置条件、日志要求见 [BUILD_GUIDE](../docs/BUILD_GUIDE.md)。
STEP-012 已使用独立环境的该命令成功构建示例配置；完整绝对路径见 BUILD_GUIDE：

```powershell
pio run -e esp32dev
```

默认源码路径为 H0。H0 实物通过且后续另行获准后，H1 才需要单独构建：在已确认的本地配置中
选择 `EPD_BRINGUP_STAGE=1`，再构建 H1 单帧与启用有限演示的配置，本步骤均不执行。
无私有配置的受保护默认构建路径已通过示例编译；保护逻辑未在实体板运行验收，
不能把编译当成实物通过。若未来更换配置后构建失败，应记录该配置未通过，不沿用本次成功状态。

实机验收依照 [BRINGUP](../docs/BRINGUP.md)：H0 → H1 → FULL/PARTIAL 序列 → 记录照片/日志，
最后才另行讨论 H2。当前不得通过测试命令自动上传或刷新真实设备。
