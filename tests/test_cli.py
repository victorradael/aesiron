"""
tests/test_cli.py
Testes de integração para os novos comandos da CLI — Fase RED (TDD).
Usa typer.testing.CliRunner e mocka as funções de core para testar apenas a camada CLI.
"""
from typer.testing import CliRunner
from aesiron.cli import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# restart
# ---------------------------------------------------------------------------

class TestRestartCommand:
    def test_restart_success(self, mocker):
        """Deve exibir mensagem de sucesso após reiniciar o app."""
        mocker.patch("aesiron.core.restart_app", return_value=None)

        result = runner.invoke(app, ["restart", "my-app"])

        assert result.exit_code == 0
        assert "my-app" in result.output
        assert "reiniciado" in result.output.lower() or "restart" in result.output.lower()

    def test_restart_app_not_found(self, mocker):
        """Deve exibir erro e sair com código 1 quando o app não existe."""
        mocker.patch("aesiron.core.restart_app", side_effect=ValueError("App not found"))

        result = runner.invoke(app, ["restart", "app-inexistente"])

        assert result.exit_code == 1
        assert "erro" in result.output.lower() or "error" in result.output.lower()


# ---------------------------------------------------------------------------
# logs
# ---------------------------------------------------------------------------

class TestLogsCommand:
    def test_logs_with_tail(self, mocker):
        """Deve passar o valor de --tail para core.get_app_logs."""
        mock_logs = mocker.patch(
            "aesiron.core.get_app_logs",
            return_value="linha1\nlinha2\n"
        )

        result = runner.invoke(app, ["logs", "my-app", "--tail", "20"])

        assert result.exit_code == 0
        mock_logs.assert_called_once_with(
            "my-app",
            mocker.ANY,   # armory_path
            tail=20,
            follow=False,
        )
        assert "linha1" in result.output

    def test_logs_container_not_running(self, mocker):
        """Deve exibir erro quando o container não está rodando."""
        mocker.patch(
            "aesiron.core.get_app_logs",
            side_effect=ValueError("App my-app is not running")
        )

        result = runner.invoke(app, ["logs", "my-app"])

        assert result.exit_code == 1
        assert "erro" in result.output.lower() or "error" in result.output.lower()


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------

class TestStatusCommand:
    def test_status_shows_table(self, mocker):
        """Deve renderizar tabela com os campos esperados."""
        mocker.patch("aesiron.core.list_apps", return_value=["my-app"])
        mocker.patch(
            "aesiron.core.get_app_status",
            return_value=[
                {
                    "name": "my-app",
                    "status": "running",
                    "port": "8501",
                    "uptime": "2h 15m",
                    "cpu_pct": "0.3%",
                    "ram_mb": "48 MB",
                }
            ],
        )

        result = runner.invoke(app, ["status"])

        assert result.exit_code == 0
        assert "my-app" in result.output
        assert "8501" in result.output
        assert "2h 15m" in result.output

    def test_status_no_apps_running(self, mocker):
        """Deve exibir mensagem amigável quando nenhum app roda."""
        mocker.patch("aesiron.core.get_app_status", return_value=[])

        result = runner.invoke(app, ["status"])

        assert result.exit_code == 0
        assert "nenhum" in result.output.lower() or "no apps" in result.output.lower()


# ---------------------------------------------------------------------------
# rename
# ---------------------------------------------------------------------------

class TestRenameCommand:
    def test_rename_success_with_confirmation(self, mocker):
        """Deve renomear e exibir mensagem de sucesso."""
        mocker.patch("aesiron.core.rename_app", return_value=None)

        # Simula confirmação 'y' no input interativo
        result = runner.invoke(app, ["rename", "my-app", "new-app"], input="y\n")

        assert result.exit_code == 0
        assert "new-app" in result.output

    def test_rename_cancelled(self, mocker):
        """Deve abortar quando o usuário nega a confirmação."""
        mock_rename = mocker.patch("aesiron.core.rename_app", return_value=None)

        result = runner.invoke(app, ["rename", "my-app", "new-app"], input="n\n")

        assert result.exit_code == 0
        mock_rename.assert_not_called()
