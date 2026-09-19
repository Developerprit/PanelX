#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PanelX — 单文件 Python 3 服务器运维管理面板
================================================
零第三方依赖：仅使用 Python 标准库（http.server / ctypes / platform / os ...）。

启动:
    python3 panelx.py [--host 0.0.0.0] [--port 5221]

默认账号: admin / admin123456  (首次登录建议修改密码)
"""

import argparse
import base64
import ctypes
import datetime
import hashlib
import http.cookies
import http.server
import json
import os
import secrets
import shutil
import socket
import struct
import sys
import threading
import time

try:
    import pwd  # POSIX only
except Exception:  # pragma: no cover
    pwd = None

import platform

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "users.json")
LOGO_FILE = os.path.join(BASE_DIR, "PanelX_logo.png")
SESSION_TTL = 8 * 3600  # 秒
DEFAULT_USER = "admin"
DEFAULT_PASS = "admin123456"
# 内嵌 Logo（构建脚本会把下面的占位符替换为真实 base64，使单文件自包含）
LOGO_B64_EMBED = "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"

# ---------------------------------------------------------------------------
# 账号 / 会话
# ---------------------------------------------------------------------------
SESSIONS = {}  # token -> {"user": str, "exp": float}
SESSIONS_LOCK = threading.Lock()


def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def load_users() -> dict:
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if DEFAULT_USER not in data.get("users", {}):
                data.setdefault("users", {})[DEFAULT_USER] = _new_user(DEFAULT_PASS)
                save_users(data)
            return data
        except Exception:
            pass
    data = {"users": {DEFAULT_USER: _new_user(DEFAULT_PASS)}}
    save_users(data)
    return data


def _new_user(password: str) -> dict:
    salt = secrets.token_hex(8)
    return {"salt": salt, "hash": _hash_password(password, salt)}


def save_users(data: dict) -> None:
    tmp = USERS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, USERS_FILE)


def verify_user(username: str, password: str) -> bool:
    data = load_users()
    u = data.get("users", {}).get(username)
    if not u:
        return False
    return _hash_password(password, u["salt"]) == u["hash"]


def is_default_password(username: str) -> bool:
    data = load_users()
    u = data.get("users", {}).get(username)
    if not u:
        return False
    return _hash_password(DEFAULT_PASS, u["salt"]) == u["hash"]


def change_password(username: str, old: str, new: str) -> bool:
    if not verify_user(username, old):
        return False
    data = load_users()
    data["users"][username] = _new_user(new)
    save_users(data)
    return True


def create_session(username: str) -> str:
    token = secrets.token_hex(16)
    with SESSIONS_LOCK:
        SESSIONS[token] = {"user": username, "exp": time.time() + SESSION_TTL}
    return token


def destroy_session(token: str) -> None:
    with SESSIONS_LOCK:
        SESSIONS.pop(token, None)


def user_of(token: str):
    with SESSIONS_LOCK:
        s = SESSIONS.get(token)
        if not s:
            return None
        if s["exp"] < time.time():
            SESSIONS.pop(token, None)
            return None
        return s["user"]
    return None


# ---------------------------------------------------------------------------
# 跨平台系统监控（仅标准库 + ctypes）
# ---------------------------------------------------------------------------
IS_LINUX = sys.platform.startswith("linux")
PAGE_SIZE = os.sysconf("SC_PAGE_SIZE") if hasattr(os, "sysconf") else 4096
CLK_TCK = os.sysconf("SC_CLK_TCK") if hasattr(os, "sysconf") else 100

CPU_PREV = (0, 0, None)  # (total, idle, ts)
CPU_LOCK = threading.Lock()
NET_PREV = (0, 0, None)  # (rx, tx, ts)
NET_LOCK = threading.Lock()
PROC_PREV = {}  # pid -> (utime+stime, ts)
PROC_LOCK = threading.Lock()

# ---- CPU ----
def _linux_cpu_sample():
    with open("/proc/stat", "r") as f:
        line = f.readline()
    parts = [int(x) for x in line.split()[1:]]
    total = sum(parts)
    idle = parts[3] + (parts[4] if len(parts) > 4 else 0)
    return total, idle


def _win_cpu_sample():
    class FILETIME(ctypes.Structure):
        _fields_ = [("lo", ctypes.c_uint32), ("hi", ctypes.c_uint32)]

    idle, kernel, user = FILETIME(), FILETIME(), FILETIME()
    ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user))
    to100 = lambda ft: (ft.hi << 32) | ft.lo
    return (to100(kernel) + to100(user)), to100(idle)


def get_cpu_percent() -> float:
    global CPU_PREV
    now = time.time()
    try:
        if IS_LINUX:
            total, idle = _linux_cpu_sample()
        else:
            total, idle = _win_cpu_sample()
    except Exception:
        return 0.0
    with CPU_LOCK:
        prev = CPU_PREV
        CPU_PREV = (total, idle, now)
        if prev[2] is None:
            return 0.0
        dt = total - prev[0]
        di = idle - prev[1]
    if dt <= 0:
        return 0.0
    pct = (1.0 - di / dt) * 100.0
    return round(max(0.0, min(100.0, pct)), 1)


# ---- 内存 ----
def get_memory() -> dict:
    try:
        if IS_LINUX:
            mi = {}
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    k, v = line.split(":", 1)
                    mi[k.strip()] = int(v.split()[0]) * 1024
            total = mi.get("MemTotal", 0)
            avail = mi.get("MemAvailable", mi.get("MemFree", 0) + mi.get("Buffers", 0) + mi.get("Cached", 0))
            used = total - avail
            return {
                "total": total,
                "used": used,
                "free": avail,
                "percent": round(used / total * 100, 1) if total else 0.0,
            }
        else:
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_uint32),
                    ("dwMemoryLoad", ctypes.c_uint32),
                    ("ullTotalPhys", ctypes.c_uint64),
                    ("ullAvailPhys", ctypes.c_uint64),
                    ("ullTotalPageFile", ctypes.c_uint64),
                    ("ullAvailPageFile", ctypes.c_uint64),
                    ("ullTotalVirtual", ctypes.c_uint64),
                    ("ullAvailVirtual", ctypes.c_uint64),
                    ("ullAvailExtendedVirtual", ctypes.c_uint64),
                ]

                def __init__(self):
                    self.dwLength = ctypes.sizeof(self)

            m = MEMORYSTATUSEX()
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            total = m.ullTotalPhys
            avail = m.ullAvailPhys
            used = total - avail
            return {
                "total": total,
                "used": used,
                "free": avail,
                "percent": round(used / total * 100, 1) if total else 0.0,
            }
    except Exception:
        return {"total": 0, "used": 0, "free": 0, "percent": 0.0}


# ---- 磁盘 ----
def get_disks() -> list:
    out = []
    try:
        if IS_LINUX:
            real_fs = {"ext4", "ext3", "ext2", "xfs", "btrfs", "f2fs", "reiserfs", "jfs", "nilfs2"}
            seen = set()
            with open("/proc/mounts", "r") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) < 3:
                        continue
                    dev, mount, fstype = parts[0], parts[1], parts[2]
                    if fstype not in real_fs:
                        continue
                    if mount in seen:
                        continue
                    if mount.startswith(("/proc", "/sys", "/dev", "/run", "/snap")):
                        continue
                    try:
                        u = os.statvfs(mount)
                        if u.f_blocks == 0:
                            continue
                        total = u.f_blocks * u.f_frsize
                        free = u.f_bavail * u.f_frsize
                        used = total - free
                        out.append({
                            "mount": mount,
                            "total": total,
                            "used": used,
                            "free": free,
                            "percent": round(used / total * 100, 1) if total else 0.0,
                        })
                        seen.add(mount)
                    except Exception:
                        continue
            if not out:  # 兜底
                u = os.statvfs("/")
                total = u.f_blocks * u.f_frsize
                free = u.f_bavail * u.f_frsize
                used = total - free
                out.append({"mount": "/", "total": total, "used": used, "free": free,
                            "percent": round(used / total * 100, 1) if total else 0.0})
        else:
            buf = ctypes.create_unicode_buffer(256)
            ctypes.windll.kernel32.GetLogicalDriveStringsW(255, buf)
            for d in buf.value.split("\x00"):
                if not d:
                    continue
                try:
                    u = shutil.disk_usage(d)
                    out.append({
                        "mount": d,
                        "total": u.total,
                        "used": u.used,
                        "free": u.free,
                        "percent": round(u.used / u.total * 100, 1) if u.total else 0.0,
                    })
                except Exception:
                    continue
    except Exception:
        pass
    return out


# ---- 网络 ----
def _linux_net_sample():
    rx = tx = 0
    with open("/proc/net/dev", "r") as f:
        for line in f:
            if ":" not in line:
                continue
            _, data = line.split(":", 1)
            cols = data.split()
            rx += int(cols[0])
            tx += int(cols[8])
    return rx, tx


def _win_net_sample():
    try:
        iphlpapi = ctypes.windll.iphlpapi
        iphlpapi.GetIfTable.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32]
        iphlpapi.GetIfTable.restype = ctypes.c_uint32

        class MIB_IFROW(ctypes.Structure):
            _fields_ = [
                ("wszName", ctypes.c_wchar * 256),
                ("dwIndex", ctypes.c_uint32),
                ("dwType", ctypes.c_uint32),
                ("dwMtu", ctypes.c_uint32),
                ("dwSpeed", ctypes.c_uint32),
                ("dwPhysAddrLen", ctypes.c_uint32),
                ("bPhysAddr", ctypes.c_byte * 8),
                ("dwAdminStatus", ctypes.c_uint32),
                ("dwOperStatus", ctypes.c_uint32),
                ("dwInOctets", ctypes.c_uint32),
                ("dwOutOctets", ctypes.c_uint32),
                ("dwInUcastPkts", ctypes.c_uint32),
                ("dwInNUcastPkts", ctypes.c_uint32),
                ("dwOutUcastPkts", ctypes.c_uint32),
                ("dwOutNUcastPkts", ctypes.c_uint32),
                ("dwInDiscards", ctypes.c_uint32),
                ("dwOutDiscards", ctypes.c_uint32),
                ("dwInErrors", ctypes.c_uint32),
                ("dwOutErrors", ctypes.c_uint32),
                ("dwOutQlen", ctypes.c_uint32),
                ("dwDescrLen", ctypes.c_uint32),
                ("bDescr", ctypes.c_byte * 256),
            ]

        buf_size = ctypes.c_uint32(16384)
        buf = ctypes.create_string_buffer(buf_size.value)
        ret = iphlpapi.GetIfTable(buf, ctypes.byref(buf_size), 0)
        if ret != 0:
            buf = ctypes.create_string_buffer(buf_size.value)
            ret = iphlpapi.GetIfTable(buf, ctypes.byref(buf_size), 0)
        if ret != 0:
            return 0, 0
        num = struct.unpack_from("I", buf)[0]
        row_size = ctypes.sizeof(MIB_IFROW)
        rx = tx = 0
        for i in range(num):
            row = MIB_IFROW.from_buffer_copy(buf, 4 + i * row_size)
            rx += row.dwInOctets
            tx += row.dwOutOctets
        return rx, tx
    except Exception:
        return 0, 0


def get_network() -> dict:
    global NET_PREV
    now = time.time()
    try:
        if IS_LINUX:
            rx, tx = _linux_net_sample()
        else:
            rx, tx = _win_net_sample()
    except Exception:
        rx = tx = 0
    with NET_LOCK:
        prev = NET_PREV
        NET_PREV = (rx, tx, now)
        if prev[2] is None:
            return {"rx_rate": 0, "tx_rate": 0, "total_rx": rx, "total_tx": tx}
        dw = now - prev[2]
        if dw <= 0:
            return {"rx_rate": 0, "tx_rate": 0, "total_rx": rx, "total_tx": tx}
        rx_rate = max(0, (rx - prev[0]) / dw)
        tx_rate = max(0, (tx - prev[1]) / dw)
    return {"rx_rate": round(rx_rate, 1), "tx_rate": round(tx_rate, 1),
            "total_rx": rx, "total_tx": tx}


# ---- 系统信息 ----
def get_system_info() -> dict:
    info = {
        "os_name": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "hostname": socket.gethostname(),
        "arch": platform.machine(),
        "python_version": platform.python_version(),
        "cpu_count": os.cpu_count() or 0,
        "cpu_model": "—",
        "uptime_seconds": 0,
        "boot_time": "",
    }
    try:
        if IS_LINUX:
            with open("/proc/uptime", "r") as f:
                up = float(f.readline().split()[0])
            info["uptime_seconds"] = int(up)
            try:
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if line.lower().startswith("model name"):
                            info["cpu_model"] = line.split(":", 1)[1].strip()
                            break
            except Exception:
                pass
        else:
            tick = ctypes.windll.kernel32.GetTickCount64()
            info["uptime_seconds"] = int(tick / 1000)
    except Exception:
        pass
    try:
        bt = datetime.datetime.now() - datetime.timedelta(seconds=info["uptime_seconds"])
        info["boot_time"] = bt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        pass
    return info


# ---- 进程 ----
def _linux_processes() -> list:
    now = time.time()
    out = []
    try:
        pids = [p for p in os.listdir("/proc") if p.isdigit()]
    except Exception:
        return out
    for pid in pids:
        try:
            with open("/proc/%s/stat" % pid, "r") as f:
                stat = f.read()
            i = stat.find("(")
            j = stat.find(")", i)
            comm = stat[i + 1:j]
            rest = stat[j + 1:].split()
            state = rest[0]
            utime = int(rest[11])
            stime = int(rest[12])
            ppid = int(rest[1])
            with open("/proc/%s/statm" % pid, "r") as f:
                sm = f.read().split()
            mem = int(sm[1]) * PAGE_SIZE
            try:
                with open("/proc/%s/cmdline" % pid, "rb") as f:
                    cl = f.read().split(b"\x00")
                cmd = " ".join(c.decode("utf-8", "replace") for c in cl if c).strip()
            except Exception:
                cmd = ""
            if not cmd:
                cmd = comm
            user = "?"
            try:
                with open("/proc/%s/status" % pid, "r") as f:
                    st = f.read()
                uid_line = [l for l in st.splitlines() if l.startswith("Uid:")]
                if uid_line:
                    uid = int(uid_line[0].split()[1])
                    user = pwd.getpwuid(uid).pw_name if (pwd and uid >= 0) else str(uid)
            except Exception:
                pass
            tot = utime + stime
            cpu = 0.0
            with PROC_LOCK:
                prev = PROC_PREV.get(int(pid))
                if prev:
                    dt = tot - prev[0]
                    dw = now - prev[1]
                    if dw > 0:
                        cpu = (dt / (dw * CLK_TCK)) * 100.0
                        if cpu < 0:
                            cpu = 0.0
                PROC_PREV[int(pid)] = (tot, now)
            out.append({
                "pid": int(pid), "name": comm, "cmd": cmd, "user": user,
                "cpu": round(cpu, 1), "mem": mem, "state": state, "ppid": ppid,
            })
        except (FileNotFoundError, ProcessLookupError, PermissionError, ValueError):
            continue
        except Exception:
            continue
    # 清理已退出进程
    alive = set(int(p) for p in pids)
    with PROC_LOCK:
        for k in list(PROC_PREV.keys()):
            if k not in alive:
                PROC_PREV.pop(k, None)
    out.sort(key=lambda x: -x["mem"])
    return out


def _win_process_mem(pid):
    try:
        PROCESS_QUERY_INFORMATION = 0x0400
        PROCESS_VM_READ = 0x0010
        kernel32 = ctypes.windll.kernel32
        h = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
        if not h:
            return 0
        # 用 psapi GetProcessMemoryInfo 取工作集
        class PMC(ctypes.Structure):
            _fields_ = [
                ("cb", ctypes.c_uint32),
                ("PageFaultCount", ctypes.c_uint32),
                ("PeakWorkingSetSize", ctypes.c_uint64),
                ("WorkingSetSize", ctypes.c_uint64),
                ("QuotaPeakPagedPoolUsage", ctypes.c_uint64),
                ("QuotaPagedPoolUsage", ctypes.c_uint64),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_uint64),
                ("QuotaNonPagedPoolUsage", ctypes.c_uint64),
                ("PagefileUsage", ctypes.c_uint64),
                ("PeakPagefileUsage", ctypes.c_uint64),
            ]

        obj = PMC()
        obj.cb = ctypes.sizeof(obj)
        ctypes.windll.psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32]
        ctypes.windll.psapi.GetProcessMemoryInfo.restype = ctypes.c_int
        ok = ctypes.windll.psapi.GetProcessMemoryInfo(h, ctypes.byref(obj), ctypes.sizeof(obj))
        kernel32.CloseHandle(h)
        return obj.WorkingSetSize if ok else 0
    except Exception:
        return 0


def _win_processes() -> list:
    try:
        kernel32 = ctypes.windll.kernel32
        TH32CS_SNAPPROCESS = 0x00000002

        class PROCESSENTRY32(ctypes.Structure):
            _fields_ = [
                ("dwSize", ctypes.c_uint32),
                ("cntUsage", ctypes.c_uint32),
                ("th32ProcessID", ctypes.c_uint32),
                ("th32DefaultHeapID", ctypes.c_uint64),
                ("th32ModuleID", ctypes.c_uint32),
                ("cntThreads", ctypes.c_uint32),
                ("th32ParentProcessID", ctypes.c_uint32),
                ("pcPriClassBase", ctypes.c_int32),
                ("dwFlags", ctypes.c_uint32),
                ("szExeFile", ctypes.c_wchar * 260),
            ]

        kernel32.CreateToolhelp32Snapshot.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
        kernel32.CreateToolhelp32Snapshot.restype = ctypes.c_void_p
        kernel32.Process32FirstW.argtypes = [ctypes.c_void_p, ctypes.POINTER(PROCESSENTRY32)]
        kernel32.Process32FirstW.restype = ctypes.c_int
        kernel32.Process32NextW.argtypes = [ctypes.c_void_p, ctypes.POINTER(PROCESSENTRY32)]
        kernel32.Process32NextW.restype = ctypes.c_int
        kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
        kernel32.CloseHandle.restype = ctypes.c_int

        snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if not snap or snap == -1:
            return []
        pe = PROCESSENTRY32()
        pe.dwSize = ctypes.sizeof(pe)
        out = []
        res = kernel32.Process32FirstW(snap, ctypes.byref(pe))
        while res:
            name = pe.szExeFile
            mem = _win_process_mem(pe.th32ProcessID)
            out.append({
                "pid": pe.th32ProcessID,
                "name": name,
                "cmd": name,
                "user": "-",
                "cpu": 0.0,
                "mem": mem,
                "state": "-",
                "ppid": pe.th32ParentProcessID,
            })
            res = kernel32.Process32NextW(snap, ctypes.byref(pe))
        kernel32.CloseHandle(snap)
        out.sort(key=lambda x: -x["mem"])
        return out
    except Exception:
        return []


def get_processes() -> list:
    if IS_LINUX:
        return _linux_processes()
    return _win_processes()


def kill_process(pid: int) -> dict:
    try:
        if IS_LINUX:
            os.kill(pid, 15)  # SIGTERM
            time.sleep(0.3)
            try:
                os.kill(pid, 0)
                os.kill(pid, 9)  # SIGKILL
            except ProcessLookupError:
                pass
        else:
            kernel32 = ctypes.windll.kernel32
            PROCESS_TERMINATE = 0x0001
            h = kernel32.OpenProcess(PROCESS_TERMINATE, False, pid)
            if not h:
                return {"ok": False, "error": "open failed"}
            kernel32.TerminateProcess(h, 0)
            kernel32.CloseHandle(h)
        return {"ok": True, "pid": pid}
    except ProcessLookupError:
        return {"ok": True, "pid": pid, "note": "already gone"}
    except PermissionError:
        return {"ok": False, "error": "permission denied"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ---------------------------------------------------------------------------
# 前端页面（内嵌，含 __LOGO__ 占位符）
# ---------------------------------------------------------------------------
PAGE_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>PanelX · 服务器运维面板</title>
<script>
(function(){try{var t=localStorage.getItem('panelx_theme');if(!t){t=matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';}document.documentElement.setAttribute('data-theme',t);}catch(e){document.documentElement.setAttribute('data-theme','light');}})();
</script>
<style>
:root{
  --bg:#f4f5f7; --surface:#ffffff; --surface-2:#f8f9fb; --ink:#16191f; --muted:#6b7280;
  --border:#e3e6ea; --accent:#1f9d6b; --accent-soft:#e6f6ef; --danger:#e5484d; --danger-soft:#fdecec;
  --warn:#d98a00; --shadow:0 1px 2px rgba(16,24,40,.04),0 8px 24px rgba(16,24,40,.06);
  --mono:ui-monospace,"SF Mono",SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,"PingFang SC","Microsoft YaHei",sans-serif;
  --r:14px;
}
[data-theme="dark"]{
  --bg:#0e1116; --surface:#161b22; --surface-2:#1b222c; --ink:#e6e9ef; --muted:#8b95a5;
  --border:#232a33; --accent:#2fe39b; --accent-soft:#112a20; --danger:#ff6b6f; --danger-soft:#2a1416;
  --warn:#e0a13a; --shadow:0 1px 2px rgba(0,0,0,.3),0 12px 32px rgba(0,0,0,.35);
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{font-family:var(--sans);background:var(--bg);color:var(--ink);-webkit-font-smoothing:antialiased;line-height:1.5}
.mono{font-family:var(--mono)}
a{color:var(--accent)}
.wrap{max-width:1180px;margin:0 auto;padding:24px 20px 64px}
/* top bar */
.topbar{display:flex;align-items:center;gap:14px;padding:14px 20px;border-bottom:1px solid var(--border);background:var(--surface);position:sticky;top:0;z-index:20}
.brand{display:flex;align-items:center;gap:10px;font-weight:700;letter-spacing:.04em}
.brand-img{height:30px;width:30px;object-fit:contain;border-radius:8px}
.brand-fallback{height:30px;width:30px;display:grid;place-items:center;background:var(--accent);color:#fff;border-radius:8px;font-weight:800;font-family:var(--mono)}
.brand b{font-size:18px}
.brand small{color:var(--muted);font-weight:500;letter-spacing:.18em;font-size:10px;text-transform:uppercase}
.spacer{flex:1}
.chip{font-family:var(--mono);font-size:12px;color:var(--muted);border:1px solid var(--border);padding:4px 10px;border-radius:999px;background:var(--surface-2)}
.btn{font-family:var(--sans);font-size:13px;border:1px solid var(--border);background:var(--surface);color:var(--ink);padding:8px 14px;border-radius:10px;cursor:pointer;transition:.18s ease}
.btn:hover{border-color:var(--accent);color:var(--accent)}
.btn.primary{background:var(--accent);border-color:var(--accent);color:#fff}
.btn.primary:hover{filter:brightness(1.05);color:#fff}
.btn.ghost{background:transparent}
.btn.danger{color:var(--danger);border-color:var(--border)}
.btn.danger:hover{background:var(--danger-soft);border-color:var(--danger)}
/* login */
.login-mask{position:fixed;inset:0;display:grid;place-items:center;background:var(--bg);z-index:50;padding:20px}
.login-card{width:min(380px,100%);background:var(--surface);border:1px solid var(--border);border-radius:18px;box-shadow:var(--shadow);padding:32px 28px}
.login-card .brand{justify-content:center;margin-bottom:6px}
.login-card h1{text-align:center;font-size:20px;margin:8px 0 2px}
.login-card p.sub{text-align:center;color:var(--muted);font-size:13px;margin:0 0 22px}
.field{margin-bottom:14px}
.field label{display:block;font-size:12px;color:var(--muted);margin-bottom:6px;letter-spacing:.02em}
.field input{width:100%;padding:11px 12px;border:1px solid var(--border);border-radius:10px;background:var(--surface-2);color:var(--ink);font-size:14px;font-family:var(--mono)}
.field input:focus{outline:none;border-color:var(--accent)}
.err{color:var(--danger);font-size:13px;min-height:18px;margin-bottom:8px;text-align:center}
/* banner */
.banner{display:flex;align-items:center;gap:12px;background:var(--warn);color:#1b1300;border-radius:12px;padding:12px 16px;margin-bottom:20px;font-size:13px}
.banner button{margin-left:auto}
/* grid */
.grid{display:grid;gap:16px}
.cards-4{grid-template-columns:repeat(4,1fr)}
.cards-2{grid-template-columns:repeat(2,1fr)}
@media(max-width:900px){.cards-4{grid-template-columns:repeat(2,1fr)}}
@media(max-width:560px){.cards-4,.cards-2{grid-template-columns:1fr}}
.card{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:18px;box-shadow:var(--shadow)}
.card h3{margin:0 0 4px;font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);font-weight:600;display:flex;align-items:center;gap:8px}
.card .val{font-family:var(--mono);font-size:30px;font-weight:600;letter-spacing:-.02em;margin-top:8px}
.card .val small{font-size:14px;color:var(--muted);font-weight:500}
.bar{height:8px;border-radius:999px;background:var(--surface-2);margin-top:14px;overflow:hidden;border:1px solid var(--border)}
.bar > i{display:block;height:100%;background:var(--accent);width:0;transition:width .9s cubic-bezier(.22,1,.36,1)}
.bar.warn > i{background:var(--warn)}
.bar.danger > i{background:var(--danger)}
.meta{color:var(--muted);font-size:12px;margin-top:8px;font-family:var(--mono)}
/* system info */
.sys{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px 22px}
.sys div{font-size:13px}
.sys span{display:block;color:var(--muted);font-size:11px;letter-spacing:.08em;text-transform:uppercase;margin-bottom:3px}
.sys b{font-family:var(--mono);font-weight:600}
.section-title{font-size:13px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin:28px 0 12px;font-weight:700;display:flex;align-items:center;gap:10px}
.section-title:after{content:"";flex:1;height:1px;background:var(--border)}
/* table */
.tablewrap{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);box-shadow:var(--shadow);overflow:hidden}
.toolbar{display:flex;align-items:center;gap:10px;padding:14px 16px;border-bottom:1px solid var(--border);flex-wrap:wrap}
.toolbar input{padding:8px 12px;border:1px solid var(--border);border-radius:10px;background:var(--surface-2);color:var(--ink);font-size:13px;font-family:var(--mono);min-width:200px}
.toolbar .count{color:var(--muted);font-size:12px;font-family:var(--mono)}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{text-align:left;padding:11px 14px;border-bottom:1px solid var(--border);white-space:nowrap}
th{color:var(--muted);font-size:11px;letter-spacing:.06em;text-transform:uppercase;font-weight:600;background:var(--surface-2)}
td.num,th.num{font-family:var(--mono);text-align:right}
tr:last-child td{border-bottom:none}
tbody tr:hover{background:var(--surface-2)}
.state{font-family:var(--mono);font-size:11px;padding:2px 8px;border-radius:6px;background:var(--surface-2);border:1px solid var(--border)}
.cmd{color:var(--muted);font-family:var(--mono);font-size:11px;max-width:280px;overflow:hidden;text-overflow:ellipsis}
@media(max-width:720px){
  table{font-size:12px}
  .cmd{display:none}
  th.hide-sm,td.hide-sm{display:none}
}
.pulse{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--accent);margin-right:6px;animation:p 1.6s infinite}
@keyframes p{0%,100%{opacity:.35}50%{opacity:1}}
/* modal */
.modal-mask{position:fixed;inset:0;background:rgba(8,11,16,.5);display:none;place-items:center;z-index:40;padding:20px}
.modal-mask.show{display:grid}
.modal{width:min(420px,100%);background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:24px;box-shadow:var(--shadow)}
.modal h2{margin:0 0 16px;font-size:17px}
.modal .field{margin-bottom:12px}
.modal .actions{display:flex;gap:10px;justify-content:flex-end;margin-top:8px}
.ok-msg{color:var(--accent);font-size:13px;min-height:16px}
</style>
</head>
<body>

<!-- LOGIN -->
<div class="login-mask" id="loginMask">
  <div class="login-card">
    <div class="brand">__LOGO__<div><b>PanelX</b><br><small>Server Ops</small></div></div>
    <h1>登录控制台</h1>
    <p class="sub">需要认证才能访问服务器监控</p>
    <div class="err" id="loginErr"></div>
    <div class="field"><label>用户名</label><input id="u" autocomplete="username" placeholder="admin"></div>
    <div class="field"><label>密码</label><input id="p" type="password" autocomplete="current-password" placeholder="••••••••"></div>
    <button class="btn primary" style="width:100%" id="loginBtn">登 录</button>
  </div>
</div>

<!-- APP -->
<div class="topbar" id="topbar" style="display:none">
  __LOGO__<div class="brand"><div><b>PanelX</b><br><small>Server Ops</small></div></div>
  <span class="chip" id="hostChip">—</span>
  <div class="spacer"></div>
  <button class="btn ghost" id="themeBtn" title="切换主题">◐ 主题</button>
  <button class="btn ghost" id="pwBtn">修改密码</button>
  <button class="btn danger" id="logoutBtn">退出</button>
</div>

<div class="wrap" id="app" style="display:none">
  <div class="banner" id="defBanner" style="display:none">
    <span>⚠ 您正在使用默认密码 <b class="mono">admin123456</b>，存在安全风险，建议尽快修改。</span>
    <button class="btn primary" id="defFix">立即修改</button>
  </div>

  <div class="grid cards-4" id="metricGrid">
    <div class="card"><h3><span class="pulse"></span>CPU</h3><div class="val" id="cpuVal">—</div><div class="bar" id="cpuBar"><i></i></div></div>
    <div class="card"><h3>内存</h3><div class="val" id="memVal">—</div><div class="bar" id="memBar"><i></i></div><div class="meta" id="memMeta"></div></div>
    <div class="card"><h3>磁盘 (根)</h3><div class="val" id="diskVal">—</div><div class="bar" id="diskBar"><i></i></div><div class="meta" id="diskMeta"></div></div>
    <div class="card"><h3>网络</h3><div class="val" id="netVal" style="font-size:20px">—</div><div class="meta" id="netMeta"></div></div>
  </div>

  <div class="section-title">系统信息</div>
  <div class="card"><div class="sys" id="sysGrid"></div></div>

  <div class="section-title">进程管理</div>
  <div class="tablewrap">
    <div class="toolbar">
      <input id="procSearch" placeholder="搜索进程名 / 命令行…">
      <span class="count" id="procCount">—</span>
      <div class="spacer"></div>
      <span class="count"><span class="pulse"></span>每 2 秒自动刷新</span>
    </div>
    <div style="overflow-x:auto">
    <table>
      <thead><tr>
        <th class="num">PID</th><th>名称</th><th class="hide-sm">命令行</th><th class="hide-sm">用户</th>
        <th class="num">CPU%</th><th class="num">内存</th><th>状态</th><th></th>
      </tr></thead>
      <tbody id="procBody"></tbody>
    </table>
    </div>
  </div>
  <p class="meta" id="foot" style="margin-top:18px;text-align:center"></p>
</div>

<!-- password modal -->
<div class="modal-mask" id="pwModal">
  <div class="modal">
    <h2>修改密码</h2>
    <div class="field"><label>当前密码</label><input id="oldP" type="password"></div>
    <div class="field"><label>新密码</label><input id="newP" type="password"></div>
    <div class="field"><label>确认新密码</label><input id="newP2" type="password"></div>
    <div class="err" id="pwErr"></div>
    <div class="ok-msg" id="pwOk"></div>
    <div class="actions">
      <button class="btn ghost" id="pwCancel">取消</button>
      <button class="btn primary" id="pwSave">保存</button>
    </div>
  </div>
</div>

<script>
const $=s=>document.querySelector(s);
const state={authed:false,user:null,isDefault:false,paused:false};

async function api(path,opts={}){
  opts.credentials='same-origin';
  const r=await fetch(path,opts);
  let data=null; try{data=await r.json();}catch(e){}
  return {status:r.status,data};
}
function fmtBytes(b){if(b==null)return '—';const u=['B','KB','MB','GB','TB','PB'];let i=0,n=b;while(n>=1024&&i<u.length-1){n/=1024;i++;}return (i?n.toFixed(1):Math.round(n))+' '+u[i];}
function fmtPct(p){return (p==null?'—':p.toFixed(1)+'%');}
function fmtUptime(s){if(!s)return '—';const d=Math.floor(s/86400),h=Math.floor(s%86400/3600),m=Math.floor(s%3600/60);let o=[];if(d)o.push(d+'天');if(h)o.push(h+'时');o.push(m+'分');return o.join(' ');}
function barCls(p){return p>=90?'danger':(p>=70?'warn':'');}
function setBar(id,p){const el=$(id);if(!el)return;el.className='bar '+barCls(p);el.firstElementChild.style.width=Math.max(0,Math.min(100,p))+'%';}

async function refreshMe(){
  const {data}=await api('/api/me');
  if(data&&data.authenticated){enterApp(data);}
  else{showLogin();}
}
function showLogin(){$('#loginMask').style.display='grid';$('#topbar').style.display='none';$('#app').style.display='none';}
function enterApp(data){
  state.authed=true;state.user=data.username;state.isDefault=!!data.is_default;
  $('#loginMask').style.display='none';$('#topbar').style.display='flex';$('#app').style.display='block';
  $('#hostChip').textContent=data.username+' @ '+location.hostname;
  $('#defBanner').style.display=state.isDefault?'flex':'none';
  loadAll();
}
async function loadAll(){await Promise.all([loadStats(),loadSystem(),loadProcesses()]);$('#foot').textContent='最近更新 '+new Date().toLocaleTimeString();}

async function loadStats(){
  const {data}=await api('/api/stats');if(!data)return;
  $('#cpuVal').innerHTML=fmtPct(data.cpu)+' <small></small>';setBar('#cpuBar',data.cpu);
  $('#memVal').innerHTML=fmtPct(data.memory.percent);setBar('#memBar',data.memory.percent);
  $('#memMeta').textContent=fmtBytes(data.memory.used)+' / '+fmtBytes(data.memory.total);
  const root=(data.disks&&data.disks[0])||{percent:0,used:0,total:0};
  $('#diskVal').innerHTML=fmtPct(root.percent);setBar('#diskBar',root.percent);
  $('#diskMeta').textContent=fmtBytes(root.used)+' / '+fmtBytes(root.total)+(root.mount?'  ('+root.mount+')':'');
  $('#netVal').textContent='↓'+fmtBytes(data.network.rx_rate)+'/s  ↑'+fmtBytes(data.network.tx_rate)+'/s';
  $('#netMeta').textContent='累计 ↓'+fmtBytes(data.network.total_rx)+'  ↑'+fmtBytes(data.network.total_tx);
}
async function loadSystem(){
  const {data}=await api('/api/system');if(!data)return;
  const rows=[
    ['操作系统',data.os_name+' '+data.os_release],
    ['主机名',data.hostname],
    ['运行时长',fmtUptime(data.uptime_seconds)],
    ['启动时间',data.boot_time],
    ['CPU 型号',data.cpu_model],
    ['逻辑核心',data.cpu_count],
    ['架构',data.arch],
    ['Python',data.python_version],
  ];
  $('#sysGrid').innerHTML=rows.map(r=>'<div><span>'+r[0]+'</span><b>'+r[1]+'</b></div>').join('');
}
async function loadProcesses(){
  const {data}=await api('/api/processes');if(!data)return;
  const q=($('#procSearch').value||'').toLowerCase();
  const list=data.filter(p=>(p.name+' '+(p.cmd||'')+' '+p.user).toLowerCase().includes(q)).slice(0,300);
  $('#procCount').textContent='共 '+data.length+' 个进程 · 显示 '+list.length;
  $('#procBody').innerHTML=list.map(p=>{
    return '<tr><td class="num">'+p.pid+'</td>'+
      '<td>'+escapeHtml(p.name)+'</td>'+
      '<td class="hide-sm cmd" title="'+escapeHtml(p.cmd||'')+'">'+escapeHtml(p.cmd||'')+'</td>'+
      '<td class="hide-sm">'+escapeHtml(p.user)+'</td>'+
      '<td class="num">'+p.cpu.toFixed(1)+'</td>'+
      '<td class="num">'+fmtBytes(p.mem)+'</td>'+
      '<td><span class="state">'+escapeHtml(p.state)+'</span></td>'+
      '<td><button class="btn danger" data-kill="'+p.pid+'">终止</button></td></tr>';
  }).join('');
}
function escapeHtml(s){return (s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}

// events
$('#loginBtn').onclick=async()=>{
  const u=$('#u').value.trim(),p=$('#p').value;
  $('#loginErr').textContent='';
  const {status,data}=await api('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:p})});
  if(status===200&&data&&data.ok){await refreshMe();}
  else{$('#loginErr').textContent=(data&&data.error)||'用户名或密码错误';}
};
$('#p').addEventListener('keydown',e=>{if(e.key==='Enter')$('#loginBtn').click();});
$('#logoutBtn').onclick=async()=>{await api('/api/logout',{method:'POST'});showLogin();};
$('#themeBtn').onclick=()=>{const cur=document.documentElement.getAttribute('data-theme');const next=cur==='dark'?'light':'dark';document.documentElement.setAttribute('data-theme',next);try{localStorage.setItem('panelx_theme',next);}catch(e){}};
$('#procSearch').oninput=()=>loadProcesses();
$('#procBody').onclick=e=>{const b=e.target.closest('[data-kill]');if(!b)return;const pid=b.getAttribute('data-kill');if(confirm('确定终止 PID '+pid+' 吗？'))killPid(pid);};
async function killPid(pid){
  const {data}=await api('/api/kill',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pid:parseInt(pid)})});
  if(data&&data.ok){loadProcesses();}else{alert((data&&data.error)||'终止失败');}
}
// password modal
$('#pwBtn').onclick=$('#defFix').onclick=()=>{$('#pwModal').classList.add('show');$('#pwErr').textContent='';$('#pwOk').textContent='';};
$('#pwCancel').onclick=()=>$('#pwModal').classList.remove('show');
$('#pwSave').onclick=async()=>{
  const oldP=$('#oldP').value,newP=$('#newP').value,newP2=$('#newP2').value;
  $('#pwErr').textContent='';$('#pwOk').textContent='';
  if(newP.length<6){$('#pwErr').textContent='新密码至少 6 位';return;}
  if(newP!==newP2){$('#pwErr').textContent='两次输入不一致';return;}
  const {status,data}=await api('/api/password',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({old:oldP,new:newP})});
  if(status===200&&data&&data.ok){$('#pwOk').textContent='密码已更新 ✓';$('#defBanner').style.display='none';setTimeout(()=>$('#pwModal').classList.remove('show'),900);$('#oldP').value=$('#newP').value=$('#newP2').value='';}
  else{$('#pwErr').textContent=(data&&data.error)||'修改失败';}
};

// auto refresh
setInterval(()=>{if(state.authed&&!state.paused)loadAll();},2000);
refreshMe();
</script>
</body>
</html>
"""


def build_page() -> str:
    # 内嵌 Logo（缺失则回退文字标）
    logo_html = ""
    try:
        with open(LOGO_FILE, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        logo_html = '<img class="brand-img" src="data:image/png;base64,%s" alt="PanelX">' % b64
    except Exception:
        logo_html = '<img class="brand-img" src="data:image/png;base64,%s" alt="PanelX">' % LOGO_B64_EMBED
    return PAGE_HTML.replace("__LOGO__", logo_html)


# ---------------------------------------------------------------------------
# HTTP 服务
# ---------------------------------------------------------------------------
class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "PanelX/1.0"
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):  # 静默访问日志
        pass

    def _send(self, code, body=b"", ctype="application/octet-stream", extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        if extra:
            for k, v in extra.items():
                self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _send_json(self, obj, code=200, extra=None):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        extra = extra or {}
        extra.setdefault("Cache-Control", "no-store")
        self._send(code, body, "application/json; charset=utf-8", extra)

    def _cookie_token(self):
        c = http.cookies.SimpleCookie()
        c.load(self.headers.get("Cookie", ""))
        v = c.get("panelx_sid")
        return v.value if v else None

    def _authed_user(self):
        return user_of(self._cookie_token())

    def _require_auth(self):
        u = self._authed_user()
        if not u:
            self._send_json({"error": "unauthorized"}, 401)
            return None
        return u

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            self._send(200, build_page().encode("utf-8"), "text/html; charset=utf-8",
                       {"Cache-Control": "no-store"})
            return
        if path == "/api/health":
            self._send_json({"ok": True, "service": "PanelX"})
            return
        if path == "/api/me":
            u = self._authed_user()
            if u:
                self._send_json({"authenticated": True, "username": u,
                                 "is_default": is_default_password(u)})
            else:
                self._send_json({"authenticated": False})
            return
        if path == "/api/system":
            if not self._require_auth():
                return
            self._send_json(get_system_info())
            return
        if path == "/api/stats":
            if not self._require_auth():
                return
            self._send_json({
                "cpu": get_cpu_percent(),
                "memory": get_memory(),
                "disks": get_disks(),
                "network": get_network(),
                "ts": int(time.time()),
            })
            return
        if path == "/api/processes":
            if not self._require_auth():
                return
            self._send_json(get_processes())
            return
        if path == "/api/logo":
            try:
                with open(LOGO_FILE, "rb") as f:
                    self._send(200, f.read(), "image/png")
            except Exception:
                self._send(404, b"", "text/plain")
            return
        self._send(404, b"not found", "text/plain")

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            payload = json.loads(raw.decode("utf-8")) if raw else {}
        except Exception:
            payload = {}

        if path == "/api/login":
            username = str(payload.get("username", "")).strip()
            password = str(payload.get("password", ""))
            if verify_user(username, password):
                token = create_session(username)
                cookie = "panelx_sid=%s; Path=/; HttpOnly; SameSite=Lax; Max-Age=%d" % (token, SESSION_TTL)
                self._send_json({"ok": True, "username": username}, 200, {"Set-Cookie": cookie})
            else:
                self._send_json({"ok": False, "error": "invalid credentials"}, 401)
            return

        if path == "/api/logout":
            token = self._cookie_token()
            if token:
                destroy_session(token)
            cookie = "panelx_sid=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0"
            self._send_json({"ok": True}, 200, {"Set-Cookie": cookie})
            return

        u = self._require_auth()
        if not u:
            return

        if path == "/api/kill":
            pid = int(payload.get("pid", 0))
            if pid <= 0:
                self._send_json({"ok": False, "error": "invalid pid"}, 400)
                return
            self._send_json(kill_process(pid))
            return

        if path == "/api/password":
            old = str(payload.get("old", ""))
            new = str(payload.get("new", ""))
            if change_password(u, old, new):
                self._send_json({"ok": True})
            else:
                self._send_json({"ok": False, "error": "旧密码错误"}, 400)
            return

        self._send(404, b"not found", "text/plain")


def main():
    ap = argparse.ArgumentParser(description="PanelX — 单文件 Python 3 服务器运维面板")
    ap.add_argument("--host", default="0.0.0.0", help="监听地址 (默认 0.0.0.0)")
    ap.add_argument("--port", type=int, default=5221, help="监听端口 (默认 5221)")
    args = ap.parse_args()

    load_users()  # 确保 users.json 存在（含默认 admin）
    httpd = http.server.ThreadingHTTPServer((args.host, args.port), Handler)
    url = "http://%s:%d/" % (args.host if args.host != "0.0.0.0" else "localhost", args.port)
    print("=" * 52)
    print("  PanelX 服务器运维面板已启动")
    print("  访问: %s" % url)
    print("  默认账号: %s / %s" % (DEFAULT_USER, DEFAULT_PASS))
    print("  (首次登录后建议修改密码)")
    print("=" * 52)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n正在关闭 PanelX …")
        httpd.shutdown()


if __name__ == "__main__":
    main()
