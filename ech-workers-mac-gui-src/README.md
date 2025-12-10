# ECH Workers 客户端

[![GitHub release](https://img.shields.io/github/release/byJoey/ech-wk.svg)](https://github.com/byJoey/ech-wk/releases)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

跨平台的 ECH Workers 代理客户端，支持 Windows、macOS 和 Linux（ARM/x86），提供图形界面和命令行两种使用方式。

## 📋 目录

- [功能特性](#功能特性)
- [版本更新](#版本更新)
- [快速开始](#快速开始)
- [命令行使用](#命令行使用)
- [图形界面使用](#图形界面使用)
- [软路由部署](#软路由部署)
- [系统要求](#系统要求)
- [故障排除](#故障排除)
- [技术文档](#技术文档)

## ✨ 功能特性

### 核心功能
- ✅ **ECH 加密** - 基于 TLS 1.3 ECH (Encrypted Client Hello) 技术，加密 SNI 信息
- ✅ **多协议支持** - 同时支持 SOCKS5 和 HTTP CONNECT 代理协议
- ✅ **智能分流** - 三种分流模式：全局代理、跳过中国大陆、直连模式
- ✅ **IPv4/IPv6 双栈** - 完整支持 IPv4 和 IPv6 地址的分流判断

### 图形界面功能
- ✅ **多服务器管理** - 支持多个服务器配置，快速切换
- ✅ **一键系统代理** - 自动设置系统代理，支持分流模式
- ✅ **系统托盘** - 最小化到系统托盘，不占用任务栏
- ✅ **开机自启** - 支持 Windows 和 macOS 开机自动启动
- ✅ **高 DPI 支持** - 完美支持高分辨率显示器
- ✅ **实时日志** - 查看代理运行状态和日志
- ✅ **配置持久化** - 自动保存配置，下次启动自动加载

### 高级功能
- ✅ **自动 IP 列表更新** - 自动下载并应用完整的中国 IP 列表（IPv4/IPv6）
- ✅ **DNS 优选** - 支持自定义 DoH 服务器进行 ECH 查询
- ✅ **IP 直连** - 支持指定服务端 IP，绕过 DNS 解析
- ✅ **跨平台支持** - Windows、macOS、Linux（x86_64/ARM64）

## 🆕 版本更新

### v1.3 最新优化

#### 核心功能增强
- **IPv6 完整支持**
  - 新增 IPv6 地址分流判断功能
  - 自动下载并加载中国 IPv6 IP 列表（`chn_ip_v6.txt`）
  - 支持 IPv4/IPv6 双栈环境下的智能分流

- **智能 IP 列表管理**
  - 自动检测 IP 列表文件是否存在或为空
  - 文件缺失时自动从 GitHub 下载最新列表
  - 支持 IPv4 和 IPv6 列表的独立管理
  - 列表来源：[mayaxcn/china-ip-list](https://github.com/mayaxcn/china-ip-list)

- **分流逻辑优化**
  - 分流判断逻辑移至 Go 核心程序，性能更优
  - 支持域名解析后的多 IP 地址判断
  - 改进的二分查找算法，提升查询效率

#### 命令行体验改进
- **默认行为优化**
  - 命令行模式下，`-routing` 参数默认值改为 `global`（全局代理）
  - 更符合命令行用户的使用习惯
  - GUI 模式不受影响，仍使用配置的默认值

- **参数说明完善**
  - 更新帮助信息，明确各参数的作用和默认值
  - 添加分流模式的详细说明

#### 兼容性提升
- **向后兼容**
  - 保持与旧版本配置文件的兼容性
  - 自动迁移和升级配置格式
  - 平滑升级体验

### 历史版本

#### v1.0
- 初始版本发布
- 基础代理功能
- 图形界面支持
- 系统代理设置

## 🚀 快速开始

### 方法 1: 使用预编译版本（推荐）

从 [GitHub Releases](https://github.com/byJoey/ech-wk/releases) 下载对应平台的压缩包：

#### 桌面版本（包含 GUI）
- **Windows x64**: `ECHWorkers-windows-amd64.zip`
- **macOS Intel**: `ECHWorkers-darwin-amd64.zip`
- **macOS Apple Silicon**: `ECHWorkers-darwin-arm64.zip`
- **Linux x86_64**: `ECHWorkers-linux-amd64.tar.gz`
- **Linux ARM64**: `ECHWorkers-linux-arm64.tar.gz`

#### 软路由版本（仅命令行）
- **Linux x86_64**: `ECHWorkers-linux-amd64-softrouter.tar.gz`
- **Linux ARM64**: `ECHWorkers-linux-arm64-softrouter.tar.gz`

#### 安装步骤

1. **解压文件**
   ```bash
   # Windows: 解压到任意目录
   # macOS/Linux: 解压到 /usr/local/bin 或自定义目录
   tar -xzf ECHWorkers-linux-amd64.tar.gz
   ```

2. **设置执行权限**（Linux/macOS）
   ```bash
   chmod +x ech-workers
   chmod +x ECHWorkersGUI  # 如果使用 GUI
   ```

3. **运行程序**
   - **Windows**: 双击 `ECHWorkersGUI.exe` 启动 GUI，或运行 `ech-workers.exe` 使用命令行
   - **macOS/Linux**: 运行 `./ECHWorkersGUI` 启动 GUI，或运行 `./ech-workers` 使用命令行

> **注意**: 预编译版本已包含所有依赖，无需安装 Python 或任何其他软件。  
> 首次运行"跳过中国大陆"模式时，程序会自动下载 IP 列表文件。

## 💻 命令行使用

`ech-workers` 支持纯命令行运行，适合服务器环境、软路由或无图形界面场景。

### 命令语法

```bash
ech-workers [选项]
```

### 参数说明

#### 必需参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `-f` | 服务端地址（必需） | `-f your-worker.workers.dev:443` |

#### 可选参数

| 参数 | 默认值 | 说明 | 示例 |
|------|--------|------|------|
| `-l` | `127.0.0.1:30000` | 本地监听地址 | `-l 0.0.0.0:30001` |
| `-token` | 空 | 身份验证令牌 | `-token your-token-here` |
| `-ip` | 空 | 指定服务端 IP（绕过 DNS） | `-ip 1.2.3.4` |
| `-dns` | `dns.alidns.com/dns-query` | ECH 查询 DoH 服务器 | `-dns dns.alidns.com/dns-query` |
| `-ech` | `cloudflare-ech.com` | ECH 查询域名 | `-ech cloudflare-ech.com` |
| `-routing` | `global` | 分流模式 | `-routing bypass_cn` |

#### 分流模式说明

| 模式 | 值 | 说明 |
|------|-----|------|
| **全局代理** | `global` | 所有流量都走代理（默认模式） |
| **跳过中国大陆** | `bypass_cn` | 中国 IP 直连，其他走代理 |
| **直连模式** | `none` | 所有流量直连，不设置代理 |

> **注意**: 
> - 使用 `bypass_cn` 模式时，程序会自动下载中国 IP 列表（IPv4/IPv6）
> - 如果 IP 列表文件不存在或为空，程序会自动从 GitHub 下载
> - IP 列表文件保存在程序目录：`chn_ip.txt`（IPv4）和 `chn_ip_v6.txt`（IPv6）

### 使用示例

#### 基本用法

```bash
# Windows
ech-workers.exe -f your-worker.workers.dev:443

# macOS / Linux
./ech-workers -f your-worker.workers.dev:443
```

#### 指定监听地址

```bash
# 监听所有网络接口（适合软路由）
./ech-workers -f your-worker.workers.dev:443 -l 0.0.0.0:30001

# 仅监听本地（默认）
./ech-workers -f your-worker.workers.dev:443 -l 127.0.0.1:30001
```

#### 使用分流模式

```bash
# 全局代理模式（默认）
./ech-workers -f your-worker.workers.dev:443 -routing global

# 跳过中国大陆模式（自动下载 IP 列表）
./ech-workers -f your-worker.workers.dev:443 -routing bypass_cn

# 直连模式
./ech-workers -f your-worker.workers.dev:443 -routing none
```

#### 完整参数示例

```bash
./ech-workers \
  -f your-worker.workers.dev:443 \
  -l 0.0.0.0:30001 \
  -token your-token \
  -ip saas.sin.fan \
  -dns dns.alidns.com/dns-query \
  -ech cloudflare-ech.com \
  -routing bypass_cn
```

#### 查看帮助

```bash
./ech-workers -h
# 或
./ech-workers --help
```

### 后台运行

#### Linux/macOS

**使用 nohup:**
```bash
nohup ./ech-workers -f your-worker.workers.dev:443 -l 127.0.0.1:30001 > ech-workers.log 2>&1 &
```

**使用 screen:**
```bash
screen -S ech-workers
./ech-workers -f your-worker.workers.dev:443 -l 127.0.0.1:30001
# 按 Ctrl+A 然后 D 分离会话
```

**使用 systemd (推荐):**

创建服务文件 `/etc/systemd/system/ech-workers.service`:
```ini
[Unit]
Description=ECH Workers Proxy Client
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/ech-workers
ExecStart=/path/to/ech-workers -f your-worker.workers.dev:443 -l 127.0.0.1:30001 -routing bypass_cn
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

启用并启动服务:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ech-workers
sudo systemctl start ech-workers
sudo systemctl status ech-workers
```

查看日志:
```bash
sudo journalctl -u ech-workers -f
```

#### Windows

**使用 PowerShell:**
```powershell
Start-Process -FilePath "ech-workers.exe" `
  -ArgumentList "-f", "your-worker.workers.dev:443", "-l", "127.0.0.1:30001" `
  -WindowStyle Hidden
```

**使用任务计划程序:**
1. 打开"任务计划程序"
2. 创建基本任务
3. 设置触发器为"计算机启动时"
4. 操作选择启动程序：`ech-workers.exe`
5. 添加参数：`-f your-worker.workers.dev:443 -l 127.0.0.1:30001`

### 配置代理客户端

启动代理后，配置应用程序使用 SOCKS5 代理：

- **代理地址**: `127.0.0.1:30001`（或你指定的监听地址）
- **代理类型**: SOCKS5
- **端口**: 30001（或你指定的端口）

#### 浏览器配置

**Chrome/Edge:**
```bash
# Linux/macOS
google-chrome --proxy-server="socks5://127.0.0.1:30001"

# Windows
chrome.exe --proxy-server="socks5://127.0.0.1:30001"
```

**Firefox:**
- 设置 → 网络设置 → 手动代理配置
- SOCKS 主机: `127.0.0.1`
- 端口: `30001`
- SOCKS v5

#### 环境变量配置

**Linux/macOS:**
```bash
export ALL_PROXY=socks5://127.0.0.1:30001
export HTTP_PROXY=socks5://127.0.0.1:30001
export HTTPS_PROXY=socks5://127.0.0.1:30001
```

**Windows (PowerShell):**
```powershell
$env:ALL_PROXY="socks5://127.0.0.1:30001"
$env:HTTP_PROXY="socks5://127.0.0.1:30001"
$env:HTTPS_PROXY="socks5://127.0.0.1:30001"
```

### 日志输出

程序会在控制台输出运行日志，包括：
- 启动信息和 ECH 配置状态
- 分流模式加载状态
- IP 列表下载和加载信息
- 代理连接和错误信息

将输出重定向到文件：
```bash
./ech-workers -f your-worker.workers.dev:443 -l 127.0.0.1:30001 > ech-workers.log 2>&1
```

## 🖥️ 图形界面使用

### 基本使用

1. **配置服务器**
   - 点击"新增"添加服务器配置
   - 填写服务地址（如：`your-worker.workers.dev:443`）和监听地址（如：`127.0.0.1:30001`）
   - 可选：填写身份令牌、优选IP、DOH服务器、ECH域名等高级选项
   - 点击"保存"保存当前配置

2. **选择分流模式**
   - **全局代理**: 所有流量都走代理
   - **跳过中国大陆**: 中国网站直连，其他网站走代理（自动下载 IP 列表）
   - **不改变代理**: 不设置系统代理，手动配置

3. **启动代理**
   - 点击"启动代理"按钮启动代理服务
   - 查看日志区域了解运行状态
   - 点击"停止"按钮停止代理服务

4. **设置系统代理**
   - 启动代理后，点击"设置系统代理"按钮
   - 系统会自动配置代理设置
   - 停止代理或关闭程序时会自动清理系统代理

### 系统托盘

- **最小化到托盘**: 关闭窗口时程序会最小化到系统托盘，不会退出
- **显示窗口**: 双击托盘图标或右键菜单选择"显示窗口"
- **退出程序**: 右键托盘图标选择"退出"

### 开机自启

勾选"开机启动"复选框，程序会在系统启动时自动运行并启动代理。

## 🛣️ 软路由部署

### OpenWrt 部署

#### 1. 上传文件

```bash
# 通过 SCP 上传
scp ech-workers root@192.168.1.1:/usr/bin/

# 或通过 WinSCP、FileZilla 等工具上传
```

#### 2. 设置执行权限

```bash
ssh root@192.168.1.1
chmod +x /usr/bin/ech-workers
```

#### 3. 创建启动脚本

创建 `/etc/init.d/ech-workers`：

```bash
#!/bin/sh /etc/rc.common

START=99
STOP=10
USE_PROCD=1

start_service() {
    procd_open_instance
    procd_set_param command /usr/bin/ech-workers \
        -f your-worker.workers.dev:443 \
        -l 0.0.0.0:30001 \
        -token your-token \
        -routing bypass_cn
    procd_set_param respawn
    procd_set_param stdout 1
    procd_set_param stderr 1
    procd_close_instance
}
```

设置权限：
```bash
chmod +x /etc/init.d/ech-workers
```

#### 4. 启用并启动服务

```bash
/etc/init.d/ech-workers enable
/etc/init.d/ech-workers start
```

#### 5. 查看服务状态

```bash
/etc/init.d/ech-workers status
logread | grep ech-workers
```

#### 6. 配置 OpenWrt 代理

在 PassWall、OpenClash 等插件中配置：
- 代理类型: SOCKS5
- 服务器: `软路由的IP`
- 端口: `30001`

### iKuai 软路由部署

#### 1. 上传文件

通过 iKuai 的 Web 管理界面或 SSH 上传 `ech-workers` 到 `/bin/` 目录。

#### 2. 创建启动脚本

创建 `/etc/init.d/ech-workers.sh`：

```bash
#!/bin/sh
/bin/ech-workers -f your-worker.workers.dev:443 -l 127.0.0.1:30001 -routing bypass_cn &
```

设置权限：
```bash
chmod +x /etc/init.d/ech-workers.sh
```

#### 3. 添加到开机启动

编辑 `/etc/rc.local`，添加：
```bash
/etc/init.d/ech-workers.sh
```

### 软路由配置建议

#### 网络配置

```bash
# 监听所有网络接口（推荐）
./ech-workers -f your-worker.workers.dev:443 -l 0.0.0.0:30001 -routing bypass_cn

# 或仅监听内网接口
./ech-workers -f your-worker.workers.dev:443 -l 192.168.1.1:30001 -routing bypass_cn
```

#### 防火墙规则

确保防火墙允许代理端口：

```bash
# OpenWrt
uci add firewall rule
uci set firewall.@rule[-1].name='Allow-ECH-Workers'
uci set firewall.@rule[-1].src='lan'
uci set firewall.@rule[-1].dest_port='30001'
uci set firewall.@rule[-1].proto='tcp'
uci set firewall.@rule[-1].target='ACCEPT'
uci commit firewall
/etc/init.d/firewall reload
```

#### 性能优化

- 使用 `-ip` 参数指定固定 IP，减少 DNS 查询
- 调整系统资源限制（如文件描述符数量）
- 考虑使用 `systemd` 或 `procd` 管理进程

#### 监控和日志

```bash
# 查看进程状态
ps | grep ech-workers

# 查看日志
logread | grep ech-workers

# 测试连接
curl --socks5 127.0.0.1:30001 http://www.google.com
```

## 📋 系统要求

### 操作系统
- **Windows**: Windows 10+ (Windows 11 完全支持)
- **macOS**: macOS 10.13+
- **Linux**: Ubuntu 18.04+ / Debian 10+ / CentOS 7+ (支持 x86_64 和 ARM64)

### 运行时要求
- **预编译版本**: 无需额外依赖，可直接运行
- **从源码编译**: 
  - Python 3.6+ (仅 GUI 需要)
  - Go 1.23+ (仅编译时需要，ECH 功能需要此版本)

### 网络要求
- 能够访问 GitHub (用于自动下载 IP 列表)
- 能够访问 Cloudflare Workers 服务

## 🔧 故障排除

### IP 列表下载失败

**问题**: 程序无法下载中国 IP 列表

**解决方案**:
1. 检查网络连接，确保能够访问 GitHub
2. 手动下载 IP 列表文件：
   ```bash
   # IPv4 列表
   curl -L -o chn_ip.txt "https://raw.githubusercontent.com/mayaxcn/china-ip-list/refs/heads/master/chn_ip.txt"
   
   # IPv6 列表
   curl -L -o chn_ip_v6.txt "https://raw.githubusercontent.com/mayaxcn/china-ip-list/refs/heads/master/chn_ip_v6.txt"
   ```
3. 将文件放在程序目录下，程序会自动使用

### 找不到 ech-workers

**问题**: GUI 提示找不到 `ech-workers` 可执行文件

**解决方案**:
1. 确保已编译 Go 程序：
   ```bash
   go build -o ech-workers ech-workers.go
   ```
2. 确保 `ech-workers` 与 GUI 在同一目录
3. 检查文件执行权限（Linux/macOS）：
   ```bash
   chmod +x ech-workers
   ```

### Windows 11 系统代理问题

**问题**: Windows 11 系统代理设置失败

**解决方案**:
1. 确保以管理员权限运行程序
2. 检查防火墙设置
3. 程序会自动使用正确的代理格式（`127.0.0.1:端口`）

### Linux 系统代理设置

**问题**: Linux 不支持自动设置系统代理

**解决方案**:
- 在系统设置中配置 SOCKS5 代理为 `127.0.0.1:端口`
- 或使用环境变量：
  ```bash
  export ALL_PROXY=socks5://127.0.0.1:端口
  ```

### bad CPU type in executable (macOS)

**问题**: 在 macOS 上运行时报错 "bad CPU type"

**解决方案**:
- Intel Mac 请下载 `darwin-amd64` 版本
- Apple Silicon Mac 请下载 `darwin-arm64` 版本

### PyQt5 安装问题

**问题**: GUI 无法启动，提示 PyQt5 未安装

**解决方案**:
```bash
# macOS
pip3 install --user PyQt5

# Windows
pip install PyQt5

# Linux (Debian/Ubuntu)
sudo apt install python3-pyqt5
```

### 软路由重启后服务未启动

**问题**: 软路由重启后代理服务未启动

**解决方案**:
1. 检查启动脚本权限：
   ```bash
   chmod +x /etc/init.d/ech-workers
   ```
2. 确保服务已启用：
   ```bash
   /etc/init.d/ech-workers enable
   ```
3. 检查系统日志：
   ```bash
   logread | grep ech-workers
   ```

## 📚 技术文档

### ECH (Encrypted Client Hello)

ECH 是 TLS 1.3 的扩展功能，用于加密 TLS 握手中的 SNI（服务器名称指示），提供更强的隐私保护。这是本程序的**核心功能**，需要 Go 1.23+ 支持。

### 中国 IP 列表

程序会自动从 [mayaxcn/china-ip-list](https://github.com/mayaxcn/china-ip-list) 下载完整的中国 IP 列表，用于"跳过中国大陆"分流模式。

- **IPv4 列表**: `chn_ip.txt` - 包含约 8000+ 个 IPv4 地址段
- **IPv6 列表**: `chn_ip_v6.txt` - 包含完整的中国 IPv6 地址段

列表文件保存在程序目录，如果文件不存在或为空，程序会自动下载。

### 分流逻辑

分流判断在 Go 核心程序中实现，使用高效的二分查找算法：

1. **域名解析**: 如果目标是域名，先解析为 IP 地址
2. **IP 检查**: 检查所有解析到的 IP（IPv4/IPv6）
3. **范围匹配**: 使用二分查找在 IP 列表中查找匹配
4. **决策**: 根据分流模式决定是否走代理

### 系统代理设置

- **Windows**: 通过注册表设置系统代理，支持 SOCKS5 代理
- **macOS**: 使用 `networksetup` 命令设置所有网络服务的 SOCKS 代理
- **Linux**: 暂不支持自动设置，需要手动配置

### 配置文件

配置文件保存在：
- **Windows**: `%APPDATA%\ECHWorkersClient\config.json`
- **macOS**: `~/Library/Application Support/ECHWorkersClient/config.json`
- **Linux**: `~/.config/ECHWorkersClient/config.json`

## 🤝 致谢

本项目的客户端和 Go 核心程序均基于 [CF_NAT](https://t.me/CF_NAT) 的原始代码开发。

- **原始项目来源**: [CF_NAT - 中转](https://t.me/CF_NAT)
- **Telegram 频道**: [@CF_NAT](https://t.me/CF_NAT)
- **中国 IP 列表**: [mayaxcn/china-ip-list](https://github.com/mayaxcn/china-ip-list)

## 📄 许可证

本项目基于 [CF_NAT](https://t.me/CF_NAT) 的原始代码开发。

## 🌟 Star History

<a href="https://www.star-history.com/#byJoey/ech-wk&type=timeline&logscale&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=byJoey/ech-wk&type=timeline&theme=dark&logscale&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=byJoey/ech-wk&type=timeline&logscale&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=byJoey/ech-wk&type=timeline&logscale&legend=top-left" />
 </picture>
</a>

## 📞 联系方式

- **Telegram 交流群**: https://t.me/+ft-zI76oovgwNmRh
- **GitHub Issues**: [提交问题](https://github.com/byJoey/ech-wk/issues)

## 🙏 贡献

欢迎提交 Issue 和 Pull Request！

---

**注意**: 本项目仅供学习和研究使用，请遵守当地法律法规。
