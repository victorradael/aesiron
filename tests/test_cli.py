"""
tests/test_cli.py
Testes de integração para os novos comandos da CLI — Fase RED (TDD).
Usa typer.testing.CliRunner e mocka as funções de core para testar apenas a camada CLI.
"""
from typer.testing import CliRunner
from aesiron.application.dto import AppLogsResult, AppStatus, AppStatusView, AppUrl, DnsSetupResult, RenamedApp
from aesiron.cli import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# restart
# ---------------------------------------------------------------------------

class TestRestartCommand:
    def test_restart_success(self, mocker):
        """Deve exibir mensagem de sucesso após reiniciar o app."""
        mocker.patch("aesiron.cli.resolve_target_apps", return_value=["my-app"])
        mocker.patch("aesiron.cli.restart_apps_command", return_value=["my-app"])

        result = runner.invoke(app, ["restart", "my-app"])

        assert result.exit_code == 0
        assert "my-app" in result.output
        assert "reiniciado" in result.output.lower() or "restart" in result.output.lower()

    def test_restart_app_not_found(self, mocker):
        """Deve exibir erro e sair com código 1 quando o app não existe."""
        mocker.patch("aesiron.cli.resolve_target_apps", return_value=["app-inexistente"])
        mocker.patch("aesiron.cli.restart_apps_command", side_effect=ValueError("App not found"))

        result = runner.invoke(app, ["restart", "app-inexistente"])

        assert result.exit_code == 1
        assert "erro" in result.output.lower() or "error" in result.output.lower()


# ---------------------------------------------------------------------------
# logs
# ---------------------------------------------------------------------------

class TestLogsCommand:
    def test_logs_with_tail(self, mocker):
        """Deve passar o valor de --tail para application.get_app_logs_command."""
        mock_logs = mocker.patch(
            "aesiron.cli.get_app_logs_command",
            return_value=AppLogsResult(
                name="my-app",
                follow=False,
                output="linha1\nlinha2\n",
                tail=20,
                path=None,
            ),
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
            "aesiron.cli.get_app_logs_command",
            side_effect=ValueError("App my-app is not running")
        )

        result = runner.invoke(app, ["logs", "my-app"])

        assert result.exit_code == 1
        assert "erro" in result.output.lower() or "error" in result.output.lower()


# ---------------------------------------------------------------------------
# urls
# ---------------------------------------------------------------------------

class TestUrlsCommand:
    def test_urls_renders_core_output(self, mocker):
        """Deve renderizar as URLs retornadas pelo core."""
        mocker.patch(
            "aesiron.cli.get_app_urls_view",
            return_value=[
                AppUrl(
                    name="my-app",
                    port="8501",
                    lan_url="http://192.168.0.10:8501",
                    dns_url="http://my-app.iron",
                )
            ],
        )

        result = runner.invoke(app, ["urls"])

        assert result.exit_code == 0
        assert "my-app" in result.output
        assert "http://192.168.0.10:8501" in result.output
        assert "http://my-app.iron" in result.output

    def test_dns_setup_renders_manual_instructions(self, mocker):
        mocker.patch(
            "aesiron.cli.configure_dns_client_command",
            return_value=DnsSetupResult(lines=["Servidor DNS configurado nesta maquina: 192.168.0.10"]),
        )

        result = runner.invoke(app, ["dns-setup"])

        assert result.exit_code == 0
        assert "192.168.0.10" in result.output

    def test_dns_reset_renders_cleanup_message(self, mocker):
        mocker.patch(
            "aesiron.cli.reset_dns_client_command",
            return_value=DnsSetupResult(lines=["Entradas locais do Aesiron removidas de /etc/hosts."]),
        )

        result = runner.invoke(app, ["dns-reset"])

        assert result.exit_code == 0
        assert "removida" in result.output.lower()


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------

class TestStatusCommand:
    def test_status_shows_table(self, mocker):
        """Deve renderizar tabela com os campos esperados."""
        mocker.patch(
            "aesiron.cli.get_app_status_view",
            return_value=AppStatusView(
                apps=["my-app"],
                statuses=[
                    AppStatus(
                        name="my-app",
                        status="running",
                        port="8501",
                        uptime="2h 15m",
                        cpu_pct="0.3%",
                        ram_mb="48 MB",
                    )
                ],
                running_names={"my-app"},
            ),
        )

        result = runner.invoke(app, ["status"])

        assert result.exit_code == 0
        assert "my-app" in result.output
        assert "8501" in result.output
        assert "2h 15m" in result.output

    def test_status_no_apps_running(self, mocker):
        """Deve exibir mensagem amigável quando nenhum app roda."""
        mocker.patch(
            "aesiron.cli.get_app_status_view",
            return_value=AppStatusView(apps=["my-app"], statuses=[], running_names=set()),
        )

        result = runner.invoke(app, ["status"])

        assert result.exit_code == 0
        assert "nenhum" in result.output.lower() or "no apps" in result.output.lower()


# ---------------------------------------------------------------------------
# rename
# ---------------------------------------------------------------------------

class TestRenameCommand:
    def test_rename_success_with_confirmation(self, mocker):
        """Deve renomear e exibir mensagem de sucesso."""
        mocker.patch(
            "aesiron.cli.rename_app_command",
            return_value=RenamedApp(old_name="my-app", new_name="new-app"),
        )

        # Simula confirmação 'y' no input interativo
        result = runner.invoke(app, ["rename", "my-app", "new-app"], input="y\n")

        assert result.exit_code == 0
        assert "new-app" in result.output

    def test_rename_cancelled(self, mocker):
        """Deve abortar quando o usuário nega a confirmação."""
        mock_rename = mocker.patch("aesiron.cli.rename_app_command")

        result = runner.invoke(app, ["rename", "my-app", "new-app"], input="n\n")

        assert result.exit_code == 0
        mock_rename.assert_not_called()
