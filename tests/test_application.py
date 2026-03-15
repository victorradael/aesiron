class TestApplicationViews:
    def test_resolve_target_apps_returns_explicit_name(self):
        from aesiron.application.views import resolve_target_apps

        assert resolve_target_apps("my-app", "/tmp/armory") == ["my-app"]

    def test_get_apps_overview_marks_running_apps(self, mocker):
        from aesiron.application.dto import AppOverview
        from aesiron.application.views import get_apps_overview

        mocker.patch("aesiron.application.views.list_apps", return_value=["app-1", "app-2"])
        mocker.patch("aesiron.application.views.get_running_app_names", return_value=["app-2"])

        assert get_apps_overview("/tmp/armory") == [
            AppOverview(name="app-1", running=False),
            AppOverview(name="app-2", running=True),
        ]

    def test_get_app_status_view_aggregates_status_data(self, mocker):
        from aesiron.application.views import get_app_status_view

        mocker.patch("aesiron.application.views.list_apps", return_value=["app-1", "app-2"])
        mocker.patch(
            "aesiron.application.views.get_app_status",
            return_value=[
                {
                    "name": "app-2",
                    "status": "running",
                    "port": "8501",
                    "uptime": "1h 00m",
                    "cpu_pct": "1.0%",
                    "ram_mb": "40 MB",
                }
            ],
        )

        result = get_app_status_view("/tmp/armory")

        assert result.apps == ["app-1", "app-2"]
        assert result.running_names == {"app-2"}
        assert result.status_map["app-2"].port == "8501"

class TestApplicationCommands:
    def test_initialize_armory_delegates_to_service(self, mocker):
        from aesiron.application.commands import initialize_armory

        mocker.patch("aesiron.application.commands.get_armory_dir", return_value="/tmp/armory")

        assert initialize_armory("/tmp/armory") == "/tmp/armory"

    def test_run_apps_command_executes_all_targets(self, mocker):
        from aesiron.application.dto import CommandExecution
        from aesiron.application.commands import run_apps_command

        mocker.patch("aesiron.application.commands.resolve_target_apps", return_value=["app-1", "app-2"])
        mock_run = mocker.patch(
            "aesiron.application.commands.run_docker_command",
            side_effect=["up-1", "up-2"],
        )
        mock_sync = mocker.patch("aesiron.application.commands.sync_network_infra")

        result = run_apps_command(path="/tmp/armory")

        assert result == [
            CommandExecution(name="app-1", output="up-1"),
            CommandExecution(name="app-2", output="up-2"),
        ]
        assert mock_run.call_count == 2
        mock_sync.assert_called_once_with("/tmp/armory")

    def test_restart_apps_command_restarts_all_targets(self, mocker):
        from aesiron.application.commands import restart_apps_command

        mocker.patch("aesiron.application.commands.resolve_target_apps", return_value=["app-1", "app-2"])
        mock_restart = mocker.patch("aesiron.application.commands.restart_app")
        mock_sync = mocker.patch("aesiron.application.commands.sync_network_infra")

        result = restart_apps_command(path="/tmp/armory")

        assert result == ["app-1", "app-2"]
        mock_restart.assert_any_call("app-1", "/tmp/armory")
        mock_restart.assert_any_call("app-2", "/tmp/armory")
        mock_sync.assert_called_once_with("/tmp/armory")

    def test_destroy_app_command_syncs_infra(self, mocker):
        from aesiron.application.commands import destroy_app_command

        mock_destroy = mocker.patch("aesiron.application.commands.destroy_app")
        mock_sync = mocker.patch("aesiron.application.commands.sync_network_infra")

        result = destroy_app_command("app-1", "/tmp/armory")

        mock_destroy.assert_called_once_with("app-1", "/tmp/armory")
        mock_sync.assert_called_once_with("/tmp/armory")
        assert result.name == "app-1"

    def test_rename_app_command_returns_payload(self, mocker):
        from aesiron.application.dto import RenamedApp
        from aesiron.application.commands import rename_app_command

        mock_rename = mocker.patch("aesiron.application.commands.rename_app")
        mock_sync = mocker.patch("aesiron.application.commands.sync_network_infra")

        result = rename_app_command("old", "new", "/tmp/armory")

        mock_rename.assert_called_once_with("old", "new", "/tmp/armory")
        mock_sync.assert_called_once_with("/tmp/armory")
        assert result == RenamedApp(old_name="old", new_name="new")

    def test_get_app_logs_command_returns_dto(self, mocker):
        from aesiron.application.commands import get_app_logs_command

        mocker.patch(
            "aesiron.application.commands.get_app_logs",
            return_value="linha1\nlinha2\n",
        )

        result = get_app_logs_command("my-app", "/tmp/armory", tail=20, follow=False)

        assert result.name == "my-app"
        assert result.tail == 20
        assert result.follow is False
        assert result.output == "linha1\nlinha2\n"

    def test_configure_dns_client_command_returns_result(self, mocker):
        from aesiron.application.commands import configure_dns_client_command

        mocker.patch(
            "aesiron.application.commands.configure_local_dns_client",
            return_value=["Servidor DNS configurado nesta maquina: 192.168.0.10"],
        )

        result = configure_dns_client_command("/tmp/armory")

        assert result.lines == ["Servidor DNS configurado nesta maquina: 192.168.0.10"]

    def test_reset_dns_client_command_returns_result(self, mocker):
        from aesiron.application.commands import reset_dns_client_command

        mocker.patch(
            "aesiron.application.commands.reset_local_dns_client",
            return_value=["Entradas locais do Aesiron removidas de /etc/hosts."],
        )

        result = reset_dns_client_command("/tmp/armory")

        assert result.lines == ["Entradas locais do Aesiron removidas de /etc/hosts."]
