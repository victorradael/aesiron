from typing import Optional

from ..services.armory import get_armory_dir
from ..services.docker import (
    destroy_app,
    get_app_logs,
    rename_app,
    restart_app,
    run_docker_command,
)
from ..services.infra import configure_local_dns_client, reset_local_dns_client, sync_network_infra
from ..services.scaffold import forge_app
from .dto import AppLogsResult, CommandExecution, DestroyedApp, DnsSetupResult, RenamedApp
from .views import resolve_target_apps


def initialize_armory(path: Optional[str] = None):
    return get_armory_dir(path)


def forge_app_command(name: str, port: int, path: Optional[str] = None):
    return forge_app(name, port, path)


def run_apps_command(name: Optional[str] = None, path: Optional[str] = None):
    apps = resolve_target_apps(name, path)
    executions = [
        CommandExecution(name=app_name, output=run_docker_command(app_name, "run", path))
        for app_name in apps
    ]
    sync_network_infra(path)
    return executions


def stop_apps_command(name: Optional[str] = None, path: Optional[str] = None):
    apps = resolve_target_apps(name, path)
    executions = [
        CommandExecution(name=app_name, output=run_docker_command(app_name, "down", path))
        for app_name in apps
    ]
    sync_network_infra(path)
    return executions


def destroy_app_command(name: str, path: Optional[str] = None):
    destroy_app(name, path)
    sync_network_infra(path)
    return DestroyedApp(name=name)


def restart_apps_command(name: Optional[str] = None, path: Optional[str] = None):
    apps = resolve_target_apps(name, path)
    for app_name in apps:
        restart_app(app_name, path)
    sync_network_infra(path)
    return apps


def rename_app_command(old_name: str, new_name: str, path: Optional[str] = None):
    rename_app(old_name, new_name, path)
    sync_network_infra(path)
    return RenamedApp(old_name=old_name, new_name=new_name)


def configure_dns_client_command(path: Optional[str] = None):
    return DnsSetupResult(lines=configure_local_dns_client(path))


def reset_dns_client_command():
    return DnsSetupResult(lines=reset_local_dns_client())


def get_app_logs_command(
    name: str,
    path: Optional[str] = None,
    tail: int = 100,
    follow: bool = False,
):
    return AppLogsResult(
        name=name,
        follow=follow,
        output=get_app_logs(name, path, tail=tail, follow=follow),
        tail=tail,
        path=path,
    )
