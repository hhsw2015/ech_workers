**Purpose**: 让 AI 编码代理快速在本仓库中上手，列出关键文件、构建/调试命令、项目约定和注意事项。

**Big Picture**:
- **核心二进制（后端）**: Go 源码为主，入口/关键文件为 `ech-workers.go`、`go.mod`。构建脚本在仓库根目录。
- **平台 GUI/前端**: 每个平台放在独立目录，分别为 `ech-workers-linux-gui-src/`、`ech-workers-mac-gui-src/`、`ech-workers-windows-gui-src/`、`ech-workers-android-gui-src/`。它们各自包含自己的 README 和构建脚本（例如 `ech_worker_gui.py`、`gui.py`、`build.bat`）。
- **原生/JNI 代码（Android）**: 位于 `ech-workers-android-gui-src/src/jni/hev-socks5-tunnel/`，包含 `Makefile`、`Android.mk`、`Application.mk`、`conf/main.yml` 等原生构建资源。

**重要文件/目录（快速引用）**:
- `gobuild.sh` — 全平台 Go 编译脚本（会在 `build/` 下产出二进制）。
- `build.sh` — 发布/打包脚本，包含多个跨编译/打包函数（注意：脚本中大量从 OpenList 拷贝的逻辑，修改前请谨慎）。
- `README.md`（仓库根）— 包含运行示例（例如 `ech-win ...`）。
- `ech-workers-*-gui-src/` — 平台 GUI 源码和本地 README（请先阅读每个子目录下的 README）。
- `ech-workers-android-gui-src/src/jni/hev-socks5-tunnel/` — C 源、头文件与 Android NDK 构建文件。

**常用命令（可直接复制执行）**:
```
# 构建所有预设平台（gobuild.sh 会创建 build/ 下的产物）
./gobuild.sh

# 运行发布脚本（包含多平台/交叉编译与打包逻辑）
./build.sh

# 运行本地 Go 二进制（在未交叉编译时，可用 go run 测试）
go run .
```

注意：`gobuild.sh` 与 `build.sh` 都使用 `go build` 并设置 `GOOS/GOARCH`，需要在容器/机器上安装 `go`。`build.sh` 的某些步骤会下载外部工具链、需要 `sudo`、`curl`、`unzip`、`jq` 等依赖。

**约定与模式（此项目的特定点）**:
- 二进制输出目录统一使用 `build/`。
- 发布构建会通过 ldflags 注入版本信息（在 `build.sh` 中有 `builtAt`、`gitCommit`、`version` 三个变量），参考 `ldflags` 的设定不要随意改名。
- Android JNI/本地库与 Go 代码分离：原生代码位于 `ech-workers-android-gui-src/src/jni/hev-socks5-tunnel/`，该目录包含自己的 `Makefile` 与 `Application.mk`，若需改动需按 NDK/Makefile 流程编译。
- 多前端并存：不同平台的 GUI 不是共享同一构建流程，修改 GUI 功能时先在对应子目录内查 README 和脚本。

**修改/PR 指南（给 AI agent 的可执行建议）**:
- 修改核心 Go 代码：先运行 `go vet`、`go build` 或 `./gobuild.sh` 的单平台命令验证二进制能正常构建。
- 修改发布脚本或交叉编译逻辑：谨慎，`build.sh` 中包含外部下载与重用的逻辑块（已注明为“OpenList 原版”）。若更改，请在 PR 描述中说明为何替换外部工具链或移除下载步骤。
- 修改 Android JNI/C 代码：在更改后，先在有 NDK 的环境验证本地编译（参考目录 `ech-workers-android-gui-src/src/jni/hev-socks5-tunnel/` 中的 `Makefile`）。

**快速调查点（定位 bug/行为）**:
- 若需找程序入口/CLI参数：查看 `ech-workers.go`（或以 `_worker.js` 为辅助的脚本）。
- 若需查运行示例：查看仓库根 `README.md` 中的 usage 与示例命令。

**不能仅凭 AI 自动修改的地方**:
- `build.sh` 中大量依赖外部二进制或工具链下载（会用到 GITHUB_TOKEN、sudo 等），自动化 修改可能破坏发布流水线。
- Android NDK / JNI 构建和系统级交叉编译步骤，需要真实环境验证（AI 不应直接替换这些脚本而不标注风险）。

如果这份说明有遗漏或你希望我把某个子目录的构建/运行步骤展开成更详尽的检查清单（例如 Android NDK 本地编译步骤或 macOS GUI 打包说明），请告诉我想要先覆盖的目标平台/目录，我会继续补充并提交更新。
