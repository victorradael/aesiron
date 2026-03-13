from datetime import datetime, timezone
from typing import Optional

from .docker import extract_container_port, get_running_containers


def format_uptime(started_at_str: Optional[str], now: Optional[datetime] = None):
    try:
        normalized = (started_at_str or "")[:26].rstrip("Z") + "+00:00"
        started_at = datetime.fromisoformat(normalized).replace(tzinfo=timezone.utc)
        delta = (now or datetime.now(timezone.utc)) - started_at
        total_seconds = int(delta.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{hours}h {minutes:02d}m"
    except Exception:
        return "-"


def format_cpu_pct(stats: dict):
    try:
        cpu_delta = (
            stats["cpu_stats"]["cpu_usage"]["total_usage"]
            - stats["precpu_stats"]["cpu_usage"]["total_usage"]
        )
        system_delta = (
            stats["cpu_stats"].get("system_cpu_usage", 0)
            - stats["precpu_stats"].get("system_cpu_usage", 0)
        )
        num_cpus = stats["cpu_stats"].get("online_cpus", 1)
        if system_delta <= 0:
            return "0.0%"
        return f"{(cpu_delta / system_delta) * num_cpus * 100:.1f}%"
    except Exception:
        return "-"


def format_ram_mb(stats: dict):
    try:
        ram_bytes = stats.get("memory_stats", {}).get("usage", 0)
        return f"{ram_bytes / (1024 * 1024):.0f} MB"
    except Exception:
        return "-"


def build_app_status(container, now: Optional[datetime] = None):
    status = {
        "name": str(container.name).replace("app-aesiron-", ""),
        "status": "running",
        "port": extract_container_port(container),
        "uptime": format_uptime(
            container.attrs.get("State", {}).get("StartedAt", ""), now=now
        ),
        "cpu_pct": "-",
        "ram_mb": "-",
    }

    try:
        stats = container.stats(stream=False)
        status["cpu_pct"] = format_cpu_pct(stats)
        status["ram_mb"] = format_ram_mb(stats)
    except Exception:
        pass

    return status


def get_app_status(armory_path=None):
    del armory_path
    return [build_app_status(container) for container in get_running_containers()]
