from datetime import datetime, timezone


class TestStatusHelpers:
    def test_format_uptime_returns_expected_window(self):
        from aesiron.services.status import format_uptime

        now = datetime(2026, 3, 12, 12, 30, tzinfo=timezone.utc)

        result = format_uptime("2026-03-12T10:15:00Z", now=now)

        assert result == "2h 15m"

    def test_format_uptime_returns_fallback_on_invalid_input(self):
        from aesiron.services.status import format_uptime

        assert format_uptime("invalid-date") == "-"

    def test_format_cpu_pct_returns_expected_value(self):
        from aesiron.services.status import format_cpu_pct

        stats = {
            "cpu_stats": {
                "cpu_usage": {"total_usage": 200_000_000},
                "system_cpu_usage": 1_000_000_000,
                "online_cpus": 2,
            },
            "precpu_stats": {
                "cpu_usage": {"total_usage": 100_000_000},
                "system_cpu_usage": 900_000_000,
            },
        }

        assert format_cpu_pct(stats) == "200.0%"

    def test_format_cpu_pct_handles_missing_values(self):
        from aesiron.services.status import format_cpu_pct

        assert format_cpu_pct({}) == "-"

    def test_format_ram_mb_returns_expected_value(self):
        from aesiron.services.status import format_ram_mb

        stats = {"memory_stats": {"usage": 50 * 1024 * 1024}}

        assert format_ram_mb(stats) == "50 MB"

    def test_build_app_status_uses_helpers_and_container_stats(self):
        from unittest.mock import MagicMock

        from aesiron.services.status import build_app_status

        container = MagicMock()
        container.name = "app-aesiron-my-app"
        container.attrs = {
            "NetworkSettings": {"Ports": {"8501/tcp": [{"HostPort": "8501"}]}},
            "State": {"StartedAt": "2026-03-12T10:15:00Z"},
        }
        container.stats.return_value = {
            "cpu_stats": {
                "cpu_usage": {"total_usage": 200_000_000},
                "system_cpu_usage": 1_000_000_000,
                "online_cpus": 2,
            },
            "precpu_stats": {
                "cpu_usage": {"total_usage": 100_000_000},
                "system_cpu_usage": 900_000_000,
            },
            "memory_stats": {"usage": 50 * 1024 * 1024},
        }

        result = build_app_status(
            container,
            now=datetime(2026, 3, 12, 12, 30, tzinfo=timezone.utc),
        )

        assert result == {
            "name": "my-app",
            "status": "running",
            "port": "8501",
            "uptime": "2h 15m",
            "cpu_pct": "200.0%",
            "ram_mb": "50 MB",
        }
