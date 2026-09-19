# PanelX（中文文档）

> 单文件 Python 3 服务器运维管理面板
> English documentation: [README.md](./README.md)

[![License](https://img.shields.io/badge/license-Available_License-green)](https://license.kscm.top/available.md)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org)

**PanelX** 是一个轻量级的服务器运维 Web 面板。它以**单个 Python 3 文件**交付，
**零第三方依赖**——只用标准库（`http.server`、`ctypes`、`platform` 等）。启动后浏览器登录，
即可查看实时的 CPU / 内存 / 磁盘 / 网络监控、可终止的进程列表与系统信息，界面响应式并支持浅色/深色主题。

---

## ✨ 功能一览

- 📊 **资源监控**：实时 CPU、内存、磁盘、网络使用率
- 🧾 **进程管理**：列出运行中的进程，支持按 PID 终止
- 🖥 **系统信息**：操作系统 / 主机名 / 运行时长 / Python 版本 / 架构
- 🔐 **登录认证**：会话令牌登录，密码以 `sha256(salt+password)` 加盐哈希存储于 `users.json`
- 🎨 **界面**：响应式布局，浅色 / 深色双主题，无前端框架
- 📦 **部署**：单文件，`python3 panelx.py` 即可运行

---

## 🚀 快速开始

```bash
# 1. 启动（默认端口 5221）
python3 panelx.py                 # 或：python3 panelx.py --host 0.0.0.0 --port 5221

# 便捷启动脚本（效果同上）：
python3 run.py                   # 跨平台 Python 启动器
./run.sh                         # Linux / macOS（需 chmod +x run.sh）
run.bat                          # Windows（使用 py -3，规避 python 别名桩）

# 2. 浏览器打开
#    http://<服务器IP>:5221/

# 3. 使用默认账号登录后立即修改密码
#    用户名：admin
#    密码：admin123456
```

> ⚠️ **安全提示**：默认账号 `admin / admin123456` 仅用于首次登录，登录后面板会提示修改密码。
> 仅 HTTP 时请勿直接暴露到公网，建议用 Nginx / Caddy 做反向代理并启用 HTTPS；
> 终止系统进程通常需要以 root 权限运行 PanelX。

---

## 🧩 监控实现（零依赖）

| 指标 | Linux 数据来源 | Windows 回退实现 |
|------|---------------|------------------|
| CPU | `/proc/stat` 两次采样差值 | `GetSystemTimes`（ctypes） |
| 内存 | `/proc/meminfo` | `GlobalMemoryStatusEx`（ctypes） |
| 磁盘 | 解析 `/proc/mounts` + `os.statvfs` | `GetLogicalDriveStrings` + `shutil` |
| 网络 | `/proc/net/dev` 累计字节求速率 | `GetIfTable`（iphlpapi） |
| 进程 | 遍历 `/proc/<pid>/{stat,statm,status,cmdline}` | `CreateToolhelp32Snapshot`（ctypes） |
| 运行时长 | `/proc/uptime` | `GetTickCount64` |

不依赖 `psutil`、`Flask`、`Django`，只用 Python 标准库。

---

## 🔌 接口列表

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|------|------|
| GET | `/api/health` | 否 | 存活探针 |
| POST | `/api/login` | 否 | `{username,password}` → 会话 Cookie |
| POST | `/api/logout` | 是 | 清除会话 |
| GET | `/api/me` | 否 | `{authenticated,username,is_default}` |
| GET | `/api/system` | 是 | 系统信息 |
| GET | `/api/stats` | 是 | CPU / 内存 / 磁盘 / 网络 |
| GET | `/api/processes` | 是 | 进程列表 |
| POST | `/api/kill` | 是 | `{pid}` 终止进程 |
| POST | `/api/password` | 是 | `{old,new}` 修改密码 |

---

## 📁 文件结构

```
panelx.py        # 整个应用（服务 + 监控 + 界面）
PanelX_logo.png  # 品牌 Logo（内嵌进界面）
Planning/Planning.md  # 技术方案
README.md / README-zh.md
PanelX.html      # 对外公开落地页
```

## 📜 许可证

基于 **Available License** 发布，详见 <https://license.kscm.top/available.md>。
