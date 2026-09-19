# PanelX — 技术方案 Planning.md

> 单文件 Python 3 服务器运维管理面板 · 端口 5221 · 标准库零第三方依赖

## 1. 项目概述
PanelX 是一个面向服务器运维的轻量 Web 管理面板。它以 **单一 Python 3 源文件** 交付，
仅依赖 Python 标准库（含 `http.server` / `ctypes` / `platform` / `os` 等），**不引入任何
第三方框架或库**（不使用 Flask / Django / psutil / tornado 等）。启动即用，适合内网 / 局域网
运维场景。

## 2. 已确认的关键决策（来自用户）
| 项 | 决策 |
|----|------|
| 目标平台 | 主要面向 **Linux**；同时保留 Windows 回退实现（开发机为 Windows，便于本地测试） |
| 默认账号 | `admin` / `admin123456`，首次登录弹窗建议修改密码（面板内置改密接口） |
| 传输安全 | **仅 HTTP**（内网运维常用，零依赖最简单；外网建议前置反向代理 + TLS） |
| 端口 | `5221`（`0.0.0.0` 监听，可通过 `--host` / `--port` 覆盖） |

## 3. 交付物清单
- `panelx.py` — 单文件应用（HTTP 服务 + 监控 + 鉴权 + 内嵌 UI）
- `users.json` — 运行时自动生成的账号库（哈希存储，不随仓库提交）
- `PanelX_logo.png` — 品牌 Logo（内嵌为 base64，缺失时回退文字标）
- `README.md` / `README-zh.md` — 中英双语文档
- `PanelX.html` — 对外公开的项目商业风格落地页（根目录）
- `LICENSE` — Available License 声明
- 推送至 `https://github.com/Developerprit/PanelX.git`（先核验仓库存在性）

## 4. 功能模块
1. **登录认证**：`/api/login` 校验，服务端会话 token（随机 16 字节 hex），`HttpOnly` Cookie；
   密码以 `sha256(salt + password)` 存于 `users.json`。未登录访问 `/api/*`（除 login/health）返回 401。
2. **系统信息概览**：OS / 内核版本 / 主机名 / 运行时长 / Python 版本 / 架构 / 逻辑核数 / CPU 型号。
3. **资源监控（实时）**：CPU 使用率、内存（总量/已用/可用）、磁盘（各挂载点）、网络（收发速率）。
   前端每 2 秒轮询 `/api/stats` 与 `/api/processes`。
4. **进程管理**：列出 PID / 名称 / 用户 / CPU% / 内存 / 状态 / 命令行；支持终止进程
   （Linux `SIGTERM→SIGKILL`，Windows `TerminateProcess`）。
5. **改密**：`/api/password` 校验旧密码后更新 `users.json`。
6. **UI**：响应式（桌面 + 移动端），浅色 / 深色双主题（持久化 + 跟随系统），
   仪器控制台风格（中性墨色 + 单一信号绿强调色，无霓虹/发光/AI 渐变）。

## 5. 跨平台监控实现（零依赖）
| 指标 | Linux 来源 | Windows 来源（回退） |
|------|-----------|---------------------|
| CPU 总占用 | `/proc/stat` 两次采样差值 | `GetSystemTimes`（ctypes） |
| 内存 | `/proc/meminfo` | `GlobalMemoryStatusEx`（ctypes） |
| 磁盘 | 解析 `/proc/mounts` + `os.statvfs` | `GetLogicalDriveStrings` + `shutil.disk_usage` |
| 网络 | `/proc/net/dev` 累计字节求速率 | `GetIfTable`（iphlpapi，ctypes） |
| 进程列表 | 遍历 `/proc/<pid>/{stat,statm,status,cmdline}` | `CreateToolhelp32Snapshot`（ctypes） |
| 进程 CPU% | 采样 `/proc/<pid>/stat` 的 utime+stime 求差 | 置 0（Linux 为主目标） |
| 运行时长 | `/proc/uptime` | `GetTickCount64` |
| 系统信息 | `platform` + `/proc/cpuinfo` | `platform` + `GetNativeSystemInfo` |

## 6. API 设计
| 方法 | 路径 | 鉴权 | 说明 |
|------|------|------|------|
| GET | `/` | 否 | 返回 SPA（前端按会话切换登录/面板） |
| GET | `/api/health` | 否 | 存活探针 `{ok:true}` |
| POST | `/api/login` | 否 | `{username,password}` → 设置会话 |
| POST | `/api/logout` | 是 | 清除会话 |
| GET | `/api/me` | 否 | `{authenticated,username,is_default}` |
| GET | `/api/system` | 是 | 系统信息 |
| GET | `/api/stats` | 是 | CPU/内存/磁盘/网络实时数据 |
| GET | `/api/processes` | 是 | 进程列表 |
| POST | `/api/kill` | 是 | `{pid}` 终止进程 |
| POST | `/api/password` | 是 | `{old,new}` 修改密码 |

## 7. 测试计划
- 本地 `python panelx.py` 启动，验证端口监听。
- `curl` 验证：未登录 `/api/system` 返回 401；登录后返回 200 与正确 JSON。
- 验证 `/api/stats`、`/api/processes`、`/api/kill`、`/api/password` 可用性。
- 浏览器手测登录态、深色/浅色切换、移动端布局。

## 8. 安全说明
- 会话 token 随机生成，Cookie `HttpOnly` + `SameSite=Lax`，默认有效期 8 小时。
- 密码加盐哈希，不落明文。
- 终止进程需要运行 PanelX 的账户具备相应权限（Linux 上通常需 root 才能杀系统进程）。
- 仅 HTTP 时请勿直接暴露公网；建议用 Nginx/Caddy 反代并启用 HTTPS。
