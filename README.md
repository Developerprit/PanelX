# PanelX

> 单文件 Python 3 服务器运维管理面板 · Single-file Python 3 server ops panel
> 中文文档见 [README-zh.md](./README-zh.md)

[![License](https://img.shields.io/badge/license-Available_License-green)](https://license.kscm.top/available.md)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org)

**PanelX** is a lightweight web control panel for server operations. It ships as a **single Python 3 file**
with **zero third-party dependencies** — only the standard library (`http.server`, `ctypes`, `platform`, …).
Point it at a server, open a browser, log in, and you get live CPU / memory / disk / network telemetry,
a process table you can kill from, and system info — all over a clean, responsive UI with light & dark themes.

*PanelX 是一个轻量级的服务器运维 Web 面板。它以单个 Python 3 文件交付，零第三方依赖，仅用标准库。
启动后浏览器登录即可看到实时的 CPU/内存/磁盘/网络监控、可终止的进程列表与系统信息，界面响应式并支持浅色/深色主题。*

---

## ✨ Features / 功能

| | English | 中文 |
|---|---|---|
| 📊 Monitoring | Real-time CPU, memory, disk & network usage | 实时 CPU、内存、磁盘、网络使用率 |
| 🧾 Processes | List running processes; terminate by PID | 列出运行进程，按 PID 终止 |
| 🖥 System | OS / hostname / uptime / Python / arch | 操作系统 / 主机名 / 运行时长 / Python / 架构 |
| 🔐 Auth | Session-token login, salted password hash | 会话令牌登录，密码加盐哈希 |
| 🎨 UI | Responsive, light & dark, no framework | 响应式，浅色/深色双主题，无前端框架 |
| 📦 Deploy | One file. `python3 panelx.py`. Done. | 单文件。`python3 panelx.py` 即可运行 |

---

## 🚀 Quick start / 快速开始

```bash
# 1. run it (default port 5221)
python3 panelx.py                 # or: python3 panelx.py --host 0.0.0.0 --port 5221

# Convenience launchers (equivalent to the command above):
python3 run.py                   # cross-platform Python launcher
./run.sh                         # Linux / macOS  (chmod +x run.sh)
run.bat                          # Windows  (uses py -3, avoids the python alias stub)

# One-shot fetch + run (auto git clone if panelx.py is missing):
Download.sh                     # Linux / macOS  (clone repo, then run)
Download.bat                    # Windows  (clone repo, then run)

# 2. open in browser
#    http://<server-ip>:5221/

# 3. login with the default account, then change the password
#    username: admin
#    password: admin123456
```

> ⚠️ **Security / 安全提示**：默认账号 `admin / admin123456` 仅用于首次登录，面板会在登录后弹出修改密码提示。
> 仅 HTTP 时请勿直接暴露公网；建议用 Nginx / Caddy 反代并启用 HTTPS。
> *Default credentials are for first login only — change them immediately. Do not expose the plain-HTTP port to the public internet; put it behind a reverse proxy with TLS.*

---

## 🧩 How monitoring works (zero dependencies) / 监控实现

| Metric | Linux source | Windows fallback |
|--------|--------------|-----------------|
| CPU | `/proc/stat` delta | `GetSystemTimes` (ctypes) |
| Memory | `/proc/meminfo` | `GlobalMemoryStatusEx` (ctypes) |
| Disk | `/proc/mounts` + `os.statvfs` | `GetLogicalDriveStrings` + `shutil` |
| Network | `/proc/net/dev` rate | `GetIfTable` (iphlpapi) |
| Processes | `/proc/<pid>/*` | `CreateToolhelp32Snapshot` (ctypes) |
| Uptime | `/proc/uptime` | `GetTickCount64` |

No `psutil`, no Flask, no Django — just Python.

---

## 🔌 API / 接口

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/health` | no | Liveness probe |
| POST | `/api/login` | no | `{username,password}` → session cookie |
| POST | `/api/logout` | yes | Clear session |
| GET | `/api/me` | no | `{authenticated,username,is_default}` |
| GET | `/api/system` | yes | System information |
| GET | `/api/stats` | yes | CPU / memory / disk / network |
| GET | `/api/processes` | yes | Process list |
| POST | `/api/kill` | yes | `{pid}` terminate |
| POST | `/api/password` | yes | `{old,new}` change password |

---

## 📁 Files / 文件

```
panelx.py        # the whole application (server + monitor + UI)
PanelX_logo.png  # brand logo (embedded into the UI)
Planning/Planning.md  # technical plan
README.md / README-zh.md
PanelX.html      # public landing page
```

## 📜 License

Released under the **Available License** — see <https://license.kscm.top/available.md>.
