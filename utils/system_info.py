"""Small system-information helpers that work on Linux/Android without psutil."""
from __future__ import annotations
import os
import platform
import time
from dataclasses import dataclass

@dataclass
class CpuFreq:
    current: float = 0.0  # MHz
    max: float = 0.0      # MHz

@dataclass
class MemoryInfo:
    total: int = 0
    available: int = 0
    used: int = 0

def _read_int(path: str) -> int | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return int(f.read().strip())
    except (OSError, ValueError):
        return None

def cpu_count(logical: bool = True) -> int:
    logical_count = os.cpu_count() or 1
    if logical:
        return logical_count
    try:
        return max(1, len([x for x in os.listdir("/sys/devices/system/cpu") if x.startswith("cpu") and x[3:].isdigit()]))
    except OSError:
        return logical_count

def cpu_freq() -> CpuFreq:
    cur = _read_int("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq")
    maxf = _read_int("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq")
    return CpuFreq(current=(cur or 0) / 1000.0, max=(maxf or 0) / 1000.0)

def cpu_percent() -> float:
    # A lightweight /proc/stat sample. Falls back to 0 on systems without /proc.
    try:
        def read_cpu():
            with open("/proc/stat", "r", encoding="utf-8") as f:
                parts = f.readline().split()[1:]
            vals = [int(x) for x in parts]
            idle = vals[3] + (vals[4] if len(vals) > 4 else 0)
            total = sum(vals)
            return total, idle
        t1, i1 = read_cpu()
        time.sleep(0.08)
        t2, i2 = read_cpu()
        dt, di = t2 - t1, i2 - i1
        return round(max(0.0, min(100.0, 100.0 * (dt - di) / dt)), 1) if dt else 0.0
    except (OSError, ValueError, IndexError):
        return 0.0

def virtual_memory() -> MemoryInfo:
    values = {}
    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as f:
            for line in f:
                key, value, *_ = line.split()
                values[key.rstrip(":")] = int(value) * 1024
        total = values.get("MemTotal", 0)
        available = values.get("MemAvailable", values.get("MemFree", 0))
        used = max(0, total - available)
        return MemoryInfo(total=total, available=available, used=used)
    except (OSError, ValueError):
        return MemoryInfo()
