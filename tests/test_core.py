"""
tests/test_core.py
Testes unitários para as funções de core.py — Fase RED (TDD).
Todos os testes devem FALHAR antes da implementação.
"""
import pytest
from docker.errors import NotFound
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def armory(tmp_path):
    """Cria um Arsenal temporário com um app de exemplo."""
    app_dir = tmp_path / "my-app"
    app_dir.mkdir()
    # Arquivos mínimos para o app ser reconhecido
    (app_dir / "Makefile").write_text("APP_NAME=my-app\nPORT=8501\n")
    (app_dir / "compose.yml").write_text("services:\n  my-app:\n    image: my-app\n")
    (app_dir / "Dockerfile").write_text("FROM python:3.12-slim\n# my-app\n")
    return tmp_path


@pytest.fixture
def mock_docker_client(mocker):
    """Mocka o cliente Docker utilizado em core.py."""
    mock_client = MagicMock()
    mocker.patch("aesiron.services.docker.client", mock_client)
    return mock_client


# ---------------------------------------------------------------------------
# restart_app
# ---------------------------------------------------------------------------

class TestRestartApp:
    def test_restart_app_stops_and_starts(self, armory, mock_docker_client, mocker):
        """Deve chamar 'make down' antes de 'make run'."""
        from aesiron import core

        call_order = []

        def fake_run(cmd, **kwargs):
            call_order.append(cmd[-1])  # captura o alvo do make: 'down' ou 'run'
            result = MagicMock()
            result.stdout = ""
            result.stderr = ""
            return result

        mocker.patch("aesiron.services.docker.subprocess.run", side_effect=fake_run)
        # Garante que a rede já existe
        mock_docker_client.networks.get.return_value = MagicMock()

        core.restart_app("my-app", str(armory))

        assert call_order == ["down", "run"]

    def test_restart_app_not_found_raises(self, armory):
        """Deve levantar ValueError para app que não existe."""
        from aesiron import core

        with pytest.raises(ValueError, match="not found"):
            core.restart_app("app-inexistente", str(armory))


# ---------------------------------------------------------------------------
# helpers / seams
# ---------------------------------------------------------------------------

class TestCoreHelpers:
    def test_resolve_armory_dir_prefers_argument_over_env(self, tmp_path):
        from aesiron import core

        resolved = core.resolve_armory_dir(
            custom_path=str(tmp_path / "arg-armory"),
            env={"AESIRON_ARMORY": str(tmp_path / "env-armory")},
            cwd=tmp_path,
        )

        assert resolved == (tmp_path / "arg-armory").resolve()

    def test_render_template_content_uses_host_pwd_when_available(self):
        from aesiron import core

        content = "{{APP_NAME}} {{PORT}} {{APP_HOST_PATH}} {{APP_HOSTNAME}}"

        rendered = core.render_template_content(
            content,
            "my-app",
            8501,
            env={"HOST_PWD": "/workspace"},
        )

        assert rendered == "my-app 8501 /workspace/my-app my-app.iron"

    def test_list_apps_does_not_create_missing_armory_dir(self, tmp_path):
        from aesiron import core

        missing = tmp_path / "missing-armory"

        assert core.list_apps(str(missing)) == []
        assert not missing.exists()

    def test_get_app_urls_builds_structured_output(self, mocker):
        from aesiron import core

        fake_container = MagicMock()
        fake_container.name = "app-aesiron-my-app"
        fake_container.attrs = {
            "NetworkSettings": {"Ports": {"8501/tcp": [{"HostPort": "8501"}]}}
        }

        mocker.patch("aesiron.services.docker.get_host_ip", return_value="192.168.0.10")
        mocker.patch("aesiron.services.docker.get_running_containers", return_value=[fake_container])
        mocker.patch("aesiron.services.infra.read_local_dns_state", return_value=["my-app.iron"])

        result = core.get_app_urls()

        assert result == [
            {
                "name": "my-app",
                "port": "8501",
                "lan_url": "http://192.168.0.10:8501",
                "dns_url": "http://my-app.iron",
            }
        ]

    def test_get_app_hostname_normalizes_name(self):
        from aesiron import core

        assert core.get_app_hostname(" Meu_App 01 ") == "meu-app-01.iron"

    def test_build_dnsmasq_config_points_zone_to_host_ip(self):
        from aesiron import core

        config = core.build_dnsmasq_config("192.168.0.10", ["1.1.1.1"])

        assert "address=/.iron/192.168.0.10" in config
        assert "server=1.1.1.1" in config

    def test_ensure_streamlit_runtime_config_adds_proxy_settings(self, tmp_path):
        from aesiron.services.scaffold import ensure_streamlit_runtime_config

        config_dir = tmp_path / "app" / ".streamlit"
        config_dir.mkdir(parents=True)
        config_path = config_dir / "config.toml"
        config_path.write_text("[server]\nport = 8501\n", encoding="utf-8")

        ensure_streamlit_runtime_config(tmp_path)

        content = config_path.read_text(encoding="utf-8")
        assert 'address = "0.0.0.0"' in content
        assert "enableCORS = false" in content
        assert "enableXsrfProtection = false" in content


# ---------------------------------------------------------------------------
# get_app_logs
# ---------------------------------------------------------------------------

class TestGetAppLogs:
    def test_get_app_logs_returns_lines(self, armory, mock_docker_client):
        """Deve retornar as últimas N linhas de log do container."""
        from aesiron import core

        fake_container = MagicMock()
        fake_container.logs.return_value = b"linha1\nlinha2\nlinha3\n"
        mock_docker_client.containers.get.return_value = fake_container

        logs = core.get_app_logs("my-app", str(armory), tail=10, follow=False)

        mock_docker_client.containers.get.assert_called_once_with("app-aesiron-my-app")
        fake_container.logs.assert_called_once_with(tail=10, stream=False)
        assert isinstance(logs, str)
        assert "linha1" in logs
        assert "linha2" in logs

    def test_get_app_logs_container_not_found(self, armory, mock_docker_client):
        """Deve levantar ValueError quando o container não está rodando."""
        from aesiron import core

        mock_docker_client.containers.get.side_effect = NotFound("nope")

        with pytest.raises(ValueError, match="not running"):
            core.get_app_logs("my-app", str(armory), tail=10, follow=False)


# ---------------------------------------------------------------------------
# get_app_status
# ---------------------------------------------------------------------------

class TestGetAppStatus:
    def test_get_app_status_running(self, armory, mock_docker_client):
        """Deve retornar lista com dicionário de métricas para cada container."""
        from aesiron import core

        fake_container = MagicMock()
        fake_container.name = "app-aesiron-my-app"
        fake_container.attrs = {
            "NetworkSettings": {"Ports": {"8501/tcp": [{"HostPort": "8501"}]}},
            "State": {"StartedAt": "2026-03-11T10:00:00Z"},
        }
        fake_container.stats.return_value = {
            "cpu_stats": {
                "cpu_usage": {"total_usage": 200_000_000},
                "system_cpu_usage": 1_000_000_000,
                "online_cpus": 2,
            },
            "precpu_stats": {
                "cpu_usage": {"total_usage": 100_000_000},
                "system_cpu_usage": 900_000_000,
            },
            "memory_stats": {"usage": 50 * 1024 * 1024, "limit": 1024 * 1024 * 1024},
        }
        mock_docker_client.containers.list.return_value = [fake_container]

        result = core.get_app_status(str(armory))

        assert len(result) == 1
        entry = result[0]
        assert entry["name"] == "my-app"
        assert entry["port"] == "8501"
        assert "cpu_pct" in entry
        assert "ram_mb" in entry
        assert "uptime" in entry

    def test_get_app_status_empty(self, mock_docker_client):
        """Deve retornar lista vazia quando nenhum container roda."""
        from aesiron import core

        mock_docker_client.containers.list.return_value = []

        result = core.get_app_status()

        assert result == []


# ---------------------------------------------------------------------------
# rename_app
# ---------------------------------------------------------------------------

class TestRenameApp:
    def test_rename_app_renames_dir_and_updates_files(self, armory, mock_docker_client, mocker):
        """Deve renomear o diretório e substituir o nome nos arquivos de config."""
        from aesiron import core

        mocker.patch("aesiron.services.docker.subprocess.run", return_value=MagicMock(stdout="", stderr=""))
        mock_docker_client.images.remove.return_value = None

        core.rename_app("my-app", "new-app", str(armory))

        new_dir = armory / "new-app"
        old_dir = armory / "my-app"

        assert new_dir.exists()
        assert not old_dir.exists()

        makefile_content = (new_dir / "Makefile").read_text()
        assert "new-app" in makefile_content
        assert "my-app" not in makefile_content

    def test_rename_app_destination_exists_raises(self, armory):
        """Deve levantar ValueError se o novo nome já existe."""
        from aesiron import core

        # Cria o app destino manualmente
        dest = armory / "new-app"
        dest.mkdir()
        (dest / "Makefile").write_text("")

        with pytest.raises(ValueError, match="already exists"):
            core.rename_app("my-app", "new-app", str(armory))
