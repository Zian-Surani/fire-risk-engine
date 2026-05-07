from __future__ import annotations

from dataclasses import dataclass

import psutil


@dataclass(slots=True)
class RuntimeMetrics:
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float


def collect_runtime_metrics() -> RuntimeMetrics:
    virtual_memory = psutil.virtual_memory()
    process = psutil.Process()
    return RuntimeMetrics(
        cpu_percent=round(psutil.cpu_percent(interval=None), 2),
        memory_percent=round(virtual_memory.percent, 2),
        memory_used_mb=round(process.memory_info().rss / 1024 / 1024, 2),
    )
