# P6 Android WebView 外壳

> 目标：在手机上装一个最小的原生壳，打开 Host 的 `/manage`，能切页、能编辑保存。
> 不打包网页、不做离线缓存、不接推送；网页始终由 Host 提供。

## 1. 组成

| 文件 | 作用 |
| --- | --- |
| `android-shell/AndroidManifest.xml` | 包名 `com.eink.shell`，minSdk 24 / targetSdk 34，`INTERNET`，允许明文 HTTP（局域网） |
| `android-shell/src/com/eink/shell/MainActivity.java` | 顶栏（地址 / 重载）+ 一个 WebView；地址存 `SharedPreferences` |
| `android-shell/build.sh` | 不用 Gradle：`javac` → `d8` → `aapt2 link` → `jar uf` → `zipalign` → `apksigner` |

行为细节：

- 首次启动没有保存地址时弹出「Host 地址」输入框；输入 `10.21.98.75:8000` 会自动补
  `http://`，保存后下次直接打开。
- 启动时若 Intent 带 `url` 字符串，直接用该地址打开并保存：
  `adb shell am start -n com.eink.shell/.MainActivity -e url http://<电脑IP>:8000/manage`。
- 顶栏「地址」可随时改 Host；「重载」重新加载当前页。返回键先在 WebView 内后退，到底再退出。
- WebView 打开 JavaScript 与 DOM Storage（`/manage` 需要），关闭文件访问与内容访问；
  不注入任何 JS，不读手机文件，不存任何凭据。

## 2. 工具链

全部装在本机 `D:/Codex/android-toolchain`，不在仓库里：

| 组件 | 版本 |
| --- | --- |
| JDK | 17.0.21+9（`jdk-17.0.21+9`） |
| Android cmdline-tools | 11076708 |
| build-tools | 34.0.0（`aapt2` / `d8` / `zipalign` / `apksigner`） |
| platforms | `android-34`（`android.jar`） |
| platform-tools | 37.0.1（`adb`） |

产物：`D:/Codex/android-toolchain/build/eink-shell.apk`（不提交，仓库只保留源码与脚本）。

## 3. 构建

```bash
bash android-shell/build.sh
```

脚本会检查 `$ANDROID_TOOLCHAIN`（默认 `D:/Codex/android-toolchain`）下的 JDK、build-tools、
`android.jar`，编译 `MainActivity.java`，生成并签名 APK，最后打印 SHA-256。调试签名用
脚本首次生成的 `build/debug.keystore`，密码固定 `android`，只用于本机安装。

已验证产物：12695 字节，SHA-256
`822277b73f01ee7f85d071a67fab04f14d6fe61d76de070e832eabc1a3c43383`（v2/v3 签名校验通过）。

## 4. 安装

普通手机：

```bash
adb install -r D:/Codex/android-toolchain/build/eink-shell.apk
```

ColorOS / OPPO 实测 `adb install` 返回 `Failure [-99]`，系统日志里是
`OplusInstallAccelerateManager` / `PackageInstallerSessionExtImpl statusCode=-99`：
USB 安装被系统的「安装加速」拦下，与 APK 本身无关。两种可行做法：

1. 让手机自己安装：把 APK 推到 `Download` 目录，在「文件管理 → 下载」点开安装，
   允许「未知来源」。`adb push` 到 `/sdcard` 时在 Git Bash 里要用 `//sdcard/...`。
2. 推送后由系统安装器确认：

   ```bash
   adb push eink-shell.apk //data/local/tmp/eink-shell.apk
   adb shell pm install -r //data/local/tmp/eink-shell.apk
   ```

   手机上会弹出 OPPO 安装引导页（`com.oplus.appdetail/.model.guide.ui.InstallGuideActivity`），
   点「继续安装」即可；不点就一直等待。

## 5. 验收怎么用

1. 电脑上启动 Host（明示局域网地址）：
   `python -m server.main --host <电脑IP> --port 8000`
2. 手机与电脑连同一个 Wi-Fi / 热点，手机打开外壳，输入 `<电脑IP>:8000`。
3. 在 `/manage` 切页、编辑、保存；Host 日志里应出现手机的 `GET /manage`、`GET /static/*`、
   `POST /api/pages/<page>/select`、`PUT /api/pages/<page>`。

## 6. 限制

- 只是 WebView 壳：Host 离线就打不开，也没有页面缓存或离线编辑。
- 地址是明文 HTTP，仅限可信局域网；没有登录和 TLS。
- 不做推送、后台常驻、快捷方式，也不内置任何业务逻辑；页面能力全部来自 Host。
- 换电脑 IP 后要在「地址」里改一次；DNS-SD 发现只在 e-ink 设备固件里实现，这一版没有。
- 未做横屏、深色模式、输入法兼容的专项验证。
