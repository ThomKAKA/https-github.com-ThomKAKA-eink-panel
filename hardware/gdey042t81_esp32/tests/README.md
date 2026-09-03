# 验证分层

## STEP-008 历史验证结果（2026-09-03）

- 现有 Python：`125 passed in 1.09s`；Python 语法编译检查通过。
- ESP32 构建：`PlatformIO unavailable`，未构建、未烧录。
- Host C++：当前没有可用 C++ 编译器，下面 7 组测试已编写但未执行。
- 实物：未验证。不能用 Python 回归通过或静态源码检查替代编译/硬件通过。
- `git diff --check` 通过；仅有仓库既有的 LF/CRLF 提示，没有空白错误。
- 新硬件文件：尾随空白 0、本地文档坏链接 0、敏感信息模式扫描 0 命中；未创建私有配置。
- 哈希对比确认：现有业务代码、配置、测试、UI 及原 P1 文件未改；仅 4 个入口/状态文件变化。

## STEP-011 当前状态（2026-09-03）

STEP-010 检查与文档完成，环境准备尚未完成；STEP-011 文档准备 COMPLETE，不代表工具链或实物验收完成。
PlatformIO / Arduino CLI：NOT INSTALLED（当前检测范围内未发现）。
七组主机 C++ 测试：**BLOCKED / NOT RUN**，当前 PATH 无可调用的 `g++`、`clang++` 或 `cl`，
未确认其他自定义安装位置；不安装、不构建、不运行这些测试。
检测范围、七组既有函数名称及检查内容见 [环境报告](../../../docs/H0_ENVIRONMENT_REPORT.md)。
Python 回归与本轮文档检查结果记录在 [progress](../../../progress.md)，不能作为 C++ 通过证据。
COMPILE VERIFIED=NO，HARDWARE VERIFIED=NO；H0 BLOCKED BY HARDWARE IDENTIFICATION。

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
以下命令尚未执行，不表示允许安装或下载构建依赖：

```powershell
pio run -e esp32dev
```

默认源码路径为 H0。H0 实物通过且后续另行获准后，H1 才需要单独构建：在已确认的本地配置中
选择 `EPD_BRINGUP_STAGE=1`，再构建 H1 单帧与启用有限演示的配置，本步骤均不执行。
无私有配置的受保护默认构建路径仅是设计意图，尚未通过构建验证；源码中的保护逻辑意图是拒绝驱动显示 GPIO，
不能把静态检查当成编译或实物通过。
工具不可用时不要自动安装或虚构成功；保留 `COMPILE VERIFIED: NO`。

实机验收依照 [BRINGUP](../docs/BRINGUP.md)：H0 → H1 → FULL/PARTIAL 序列 → 记录照片/日志，
最后才另行讨论 H2。当前不得通过测试命令自动上传或刷新真实设备。
