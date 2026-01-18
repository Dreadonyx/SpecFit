import psutil
from utils import bytes_to_gb

def get_system_metrics():
    cpu_percent = psutil.cpu_percent(interval=1)

    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    return {
        "cpu_percent": cpu_percent,
        "memory": {
            "total_gb": bytes_to_gb(mem.total),
            "used_gb": bytes_to_gb(mem.used),
            "free_gb": bytes_to_gb(mem.free),
            "available_gb": bytes_to_gb(mem.available),
            "percent": mem.percent
        },
        "swap": {
            "total_gb": bytes_to_gb(swap.total),
            "used_gb": bytes_to_gb(swap.used),
            "percent": swap.percent
        }
    }