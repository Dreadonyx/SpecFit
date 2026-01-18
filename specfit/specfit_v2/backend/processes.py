import psutil
from utils import bytes_to_gb

def get_top_processes(limit=3):
    processes = []

    for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
        try:
            mem_gb = bytes_to_gb(proc.info['memory_info'].rss)
            processes.append({
                "name": proc.info['name'],
                "pid": proc.info['pid'],
                "memory_gb": mem_gb,
                "cpu_percent": proc.info['cpu_percent']
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    top_memory = sorted(
        processes, key=lambda p: p['memory_gb'], reverse=True
    )[:limit]

    top_cpu = sorted(
        processes, key=lambda p: p['cpu_percent'], reverse=True
    )[:limit]

    return {
        "top_memory": top_memory,
        "top_cpu": top_cpu
    }