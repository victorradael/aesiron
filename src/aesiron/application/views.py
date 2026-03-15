from typing import Optional

from ..services.armory import list_apps
from ..services.docker import get_app_urls, get_running_app_names
from ..services.status import get_app_status
from .dto import AppOverview, AppStatus, AppStatusView, AppUrl


def resolve_target_apps(name: Optional[str], path: Optional[str] = None):
    return [name] if name else list_apps(path)


def get_apps_overview(path: Optional[str] = None):
    apps = list_apps(path)
    running = set(get_running_app_names())
    return [AppOverview(name=app_name, running=app_name in running) for app_name in apps]


def get_app_urls_view(path: Optional[str] = None):
    del path
    return [AppUrl(**app_url) for app_url in get_app_urls()]


def get_app_status_view(path: Optional[str] = None):
    apps = list_apps(path)
    statuses = [AppStatus(**status) for status in get_app_status(path)]
    return AppStatusView(
        apps=apps,
        statuses=statuses,
        running_names={status.name for status in statuses},
    )
