# 验证分层

## 当前真实结果（2026-09-03）

- 现有 Python：`125 passed in 1.09s`；Python 语法编译检查通过。
- ESP32 构建：`PlatformIO unavailable`，未构建、未烧录。
- Host C++：当前没有可用 C++ 编译器，下面 7 组测试已编写但未执行。
- 实物：未验证。不能用 Python 回归通过或静态源码检查替代编译/硬件通过。
- `git diff --check` 通过；仅有仓库既有的 LF/CRLF 提示，没有空白错误。
- 新硬件文件：尾随空白 0、本地文档坏链接 0、敏感信息模式扫描 0 命中；未创建私有配置。
- 哈希对比确认：现有业务代码、配置、测试、UI 及原 P1 文件未改；仅 4 个入口/状态文件变化。

## Python 隔离性

从仓库根目录运行：

```powershell
.\.venv\Scripts\python.exe -m pytest -q
git diff --check
```

本目录不被 Python 导入，不给 pytest 增加硬件前提，不更改事件、PNG/BMP 或 Panel 测试。
未通过实际删除目录来验收；采用源文件哈希对比、依赖搜索与原测试回归检查隔离。

## 纯 C++ 测试（将来已有编译器时）

`test_core.cpp` 不依赖 Arduino/GxEPD2；7 组检查涵盖首次 FULL、失败不推进、同帧保持、
最小间隔、5 次局刷后 FULL、FAST_FULL/禁用快刷、millis 回绕、帧布局和禁用 fetcher 不写缓冲。

在硬件目录运行，使用你已安装的 C++17 编译器（示例 `g++`）：

```powershell
New-Item -ItemType Directory -Force .build
g++ -std=c++17 -Wall -Wextra -Werror -Iinclude -Isrc tests/test_core.cpp src/refresh_policy.cpp -o .build/test_core.exe
.\.build\test_core.exe
```

期望输出 `7 core test groups passed`。不要加 `-DNDEBUG`，否则会关闭断言。
这些测试是主机逻辑测试，不是 ESP32 固件构建，也不验证真实驱动时序。

## ESP32 编译（将来已有 PlatformIO 时）

```powershell
pio run -e esp32dev
```

默认构建 H0。H1 也需要单独构建：在已确认的本地配置中选择 `EPD_BRINGUP_STAGE=1`，
再构建 H1 单帧与启用有限演示的配置。没有本地配置可以编译，但保护逻辑拒绝驱动显示 GPIO。
工具不可用时不要自动安装或虚构成功；保留 `COMPILE VERIFIED: NO`。

实机验收依照 [BRINGUP](../docs/BRINGUP.md)：H0 → H1 → FULL/PARTIAL 序列 → 记录照片/日志，
最后才另行讨论 H2。当前不得通过测试命令自动上传或刷新真实设备。
