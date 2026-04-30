import os
import time
import signal
import requests
import psutil
from collections import defaultdict, deque
from dotenv import load_dotenv
from flask import Flask, render_template, jsonify, request

load_dotenv()

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"

# ---------------------------------------------------------------------------
# History buffers (last 60 data points for sparkline graphs)
# ---------------------------------------------------------------------------
MAX_HISTORY = 60
cpu_history = deque(maxlen=MAX_HISTORY)
memory_history = deque(maxlen=MAX_HISTORY)
swap_history = deque(maxlen=MAX_HISTORY)
net_sent_history = deque(maxlen=MAX_HISTORY)
net_recv_history = deque(maxlen=MAX_HISTORY)
disk_read_history = deque(maxlen=MAX_HISTORY)
disk_write_history = deque(maxlen=MAX_HISTORY)
cpu_per_core_history = defaultdict(lambda: deque(maxlen=MAX_HISTORY))

_prev_net = psutil.net_io_counters()
_prev_disk = psutil.disk_io_counters()
_prev_time = time.time()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_top_processes(n=10):
    """Get top N processes by memory, aggregated by executable name."""
    memory_by_name = defaultdict(lambda: {"memory_bytes": 0, "cpu": 0.0, "pids": 0})

    for p in psutil.process_iter(["name", "exe", "memory_info", "cpu_percent"]):
        try:
            exe_path = p.info.get("exe")
            name = os.path.basename(exe_path) if exe_path else (p.info["name"] or "unknown")
            mem = p.info["memory_info"].rss
            cpu = p.info.get("cpu_percent", 0.0) or 0.0
            memory_by_name[name]["memory_bytes"] += mem
            memory_by_name[name]["cpu"] += cpu
            memory_by_name[name]["pids"] += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    sorted_procs = sorted(memory_by_name.items(), key=lambda x: x[1]["memory_bytes"], reverse=True)[:n]
    total_mem = psutil.virtual_memory().total
    return [
        {
            "name": name,
            "memory_mb": round(info["memory_bytes"] / (1024 ** 2), 1),
            "memory_percent": round(info["memory_bytes"] / total_mem * 100, 1),
            "cpu_percent": round(info["cpu"], 1),
            "instances": info["pids"],
        }
        for name, info in sorted_procs
    ]


def get_verdict(cpu, memory):
    if cpu > 90 or memory > 85:
        return "OVERLOADED"
    if cpu > 70 or memory > 70:
        return "STRAINED"
    return "NORMAL"


def get_ai_insight(verdict, cpu, memory, top_proc_name, top_proc_mem_mb):
    """Get AI insight from Groq API."""
    if verdict == "NORMAL":
        return "System stable. No action needed."

    prompt = f"""You are a system health advisor. Be concise. Output EXACTLY 3 numbered lines.

System: {verdict} | CPU: {cpu}% | Memory: {memory}%
Top process: {top_proc_name} using {top_proc_mem_mb} MB

Format:
1. [What's happening]
2. [What to do]
3. [Next step]
"""

    try:
        resp = requests.post(
            GROQ_ENDPOINT,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": "Concise system health advisor. Follow format exactly."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
                "max_tokens": 150,
            },
            timeout=10,
        )
        data = resp.json()
        choices = data.get("choices", [])
        if choices:
            text = choices[0].get("message", {}).get("content", "").strip()
            if text:
                return text
    except Exception:
        pass

    return f"Memory at {memory}%. Consider closing {top_proc_name}."


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/status")
def api_status():
    global _prev_net, _prev_disk, _prev_time

    now = time.time()
    dt = max(now - _prev_time, 0.1)

    # CPU
    cpu_total = psutil.cpu_percent(interval=0.5)
    cpu_cores = psutil.cpu_percent(interval=0, percpu=True)
    cpu_freq = psutil.cpu_freq()

    # Memory
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    # Disk
    partitions = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            partitions.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "total_gb": round(usage.total / (1024 ** 3), 1),
                "used_gb": round(usage.used / (1024 ** 3), 1),
                "free_gb": round(usage.free / (1024 ** 3), 1),
                "percent": usage.percent,
            })
        except (PermissionError, OSError):
            continue

    disk_io = psutil.disk_io_counters()
    disk_read_rate = round((disk_io.read_bytes - _prev_disk.read_bytes) / dt / (1024 ** 2), 2)
    disk_write_rate = round((disk_io.write_bytes - _prev_disk.write_bytes) / dt / (1024 ** 2), 2)

    # Network
    net_io = psutil.net_io_counters()
    net_sent_rate = round((net_io.bytes_sent - _prev_net.bytes_sent) / dt / 1024, 2)
    net_recv_rate = round((net_io.bytes_recv - _prev_net.bytes_recv) / dt / 1024, 2)
    net_connections = len(psutil.net_connections(kind="inet"))

    _prev_net = net_io
    _prev_disk = disk_io
    _prev_time = now

    # Processes
    processes = get_top_processes(10)

    # Verdict + AI
    verdict = get_verdict(cpu_total, mem.percent)
    top_proc = processes[0] if processes else {"name": "unknown", "memory_mb": 0}
    ai_insight = get_ai_insight(verdict, cpu_total, mem.percent, top_proc["name"], top_proc["memory_mb"])

    # Update histories
    cpu_history.append(cpu_total)
    memory_history.append(mem.percent)
    swap_history.append(swap.percent)
    net_sent_history.append(net_sent_rate)
    net_recv_history.append(net_recv_rate)
    disk_read_history.append(disk_read_rate)
    disk_write_history.append(disk_write_rate)
    for i, core_pct in enumerate(cpu_cores):
        cpu_per_core_history[i].append(core_pct)

    # Temperature (Linux only, graceful fail)
    temps = {}
    try:
        sensor_temps = psutil.sensors_temperatures()
        if sensor_temps:
            for chip, entries in sensor_temps.items():
                for entry in entries:
                    if entry.current > 0:
                        label = entry.label or chip
                        temps[label] = round(entry.current, 1)
    except (AttributeError, OSError):
        pass

    # System info
    boot_time = psutil.boot_time()
    uptime_secs = int(now - boot_time)
    uptime_str = f"{uptime_secs // 3600}h {(uptime_secs % 3600) // 60}m"

    return jsonify({
        "cpu": {
            "total": cpu_total,
            "cores": cpu_cores,
            "core_count": psutil.cpu_count(logical=True),
            "physical_cores": psutil.cpu_count(logical=False),
            "freq_mhz": round(cpu_freq.current, 0) if cpu_freq else None,
            "history": list(cpu_history),
            "per_core_history": {str(k): list(v) for k, v in cpu_per_core_history.items()},
        },
        "memory": {
            "percent": mem.percent,
            "total_gb": round(mem.total / (1024 ** 3), 1),
            "used_gb": round(mem.used / (1024 ** 3), 1),
            "available_gb": round(mem.available / (1024 ** 3), 1),
            "cached_gb": round(getattr(mem, "cached", 0) / (1024 ** 3), 1),
            "buffers_gb": round(getattr(mem, "buffers", 0) / (1024 ** 3), 1),
            "history": list(memory_history),
        },
        "swap": {
            "percent": swap.percent,
            "total_gb": round(swap.total / (1024 ** 3), 1),
            "used_gb": round(swap.used / (1024 ** 3), 1),
            "free_gb": round(swap.free / (1024 ** 3), 1),
            "history": list(swap_history),
        },
        "disk": {
            "partitions": partitions,
            "io": {
                "read_mb_s": disk_read_rate,
                "write_mb_s": disk_write_rate,
                "read_history": list(disk_read_history),
                "write_history": list(disk_write_history),
            },
        },
        "network": {
            "sent_kb_s": net_sent_rate,
            "recv_kb_s": net_recv_rate,
            "total_sent_mb": round(net_io.bytes_sent / (1024 ** 2), 1),
            "total_recv_mb": round(net_io.bytes_recv / (1024 ** 2), 1),
            "connections": net_connections,
            "sent_history": list(net_sent_history),
            "recv_history": list(net_recv_history),
        },
        "processes": processes,
        "temperatures": temps,
        "system": {
            "hostname": os.uname().nodename,
            "os": f"{os.uname().sysname} {os.uname().release}",
            "uptime": uptime_str,
            "python": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
        },
        "verdict": verdict,
        "ai_insight": ai_insight,
    })


@app.route("/api/kill/<int:pid>", methods=["POST"])
def kill_process(pid):
    try:
        proc = psutil.Process(pid)
        proc.terminate()
        return jsonify({"status": "ok", "message": f"Sent SIGTERM to {proc.name()} (PID {pid})"})
    except psutil.NoSuchProcess:
        return jsonify({"status": "error", "message": "Process not found"}), 404
    except psutil.AccessDenied:
        return jsonify({"status": "error", "message": "Access denied. Run with sudo."}), 403
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    # Prime the CPU percent counter
    psutil.cpu_percent(interval=0.1)
    psutil.cpu_percent(interval=0.1, percpu=True)
    app.run(debug=True, port=5000)
