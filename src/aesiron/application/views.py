from typing import Optional

from ..services.armory import list_apps
from ..services.docker import get_app_urls, get_running_app_names
from ..services.status import get_app_status
from .dto import AppOverview, AppStatus, AppStatusView, AppUrl


def resolve_target_apps(name: Optional[str], path: Optional[str] = None):
    all_apps = list_apps(path)
    if name:
        if name not in all_apps:
            from ..domain.errors import AppNotFoundError
            from ..services.armory import get_armory_dir
            armory = get_armory_dir(path, create=False)
            raise AppNotFoundError(f"App '{name}' not found in {armory}.")
        return [name]
    return all_apps


def get_apps_overview(path: Optional[str] = None):
    apps = list_apps(path)
    running = set(get_running_app_names())
    return [AppOverview(name=app_name, running=app_name in running) for app_name in apps]


def get_app_urls_view(path: Optional[str] = None):
    return [AppUrl(**app_url) for app_url in get_app_urls(path)]


def get_app_status_view(path: Optional[str] = None):
    apps = list_apps(path)
    statuses = [AppStatus(**status) for status in get_app_status(path)]
    return AppStatusView(
        apps=apps,
        statuses=statuses,
        running_names={status.name for status in statuses},
    )
