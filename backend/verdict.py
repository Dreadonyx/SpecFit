def get_verdict(memory_percent, swap_percent):
    if memory_percent > 85 or swap_percent > 50:
        return "OVERLOADED"
    if memory_percent > 70 or swap_percent > 20:
        return "STRAINED"
    return "NORMAL"