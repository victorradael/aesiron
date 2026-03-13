from dataclasses import dataclass
from typing import Iterable, List, Optional, Set, Union


@dataclass(frozen=True)
class AppOverview:
    name: str
    running: bool


@dataclass(frozen=True)
class AppUrl:
    name: str
    port: str
    url: str


@dataclass(frozen=True)
class AppStatus:
    name: str
    status: str
    port: str
    uptime: str
    cpu_pct: str
    ram_mb: str


@dataclass(frozen=True)
class AppStatusView:
    apps: List[str]
    statuses: List[AppStatus]
    running_names: Set[str]

    @property
    def status_map(self):
        return {status.name: status for status in self.statuses}


@dataclass(frozen=True)
class CommandExecution:
    name: str
    output: str


@dataclass(frozen=True)
class DestroyedApp:
    name: str


@dataclass(frozen=True)
class RenamedApp:
    old_name: str
    new_name: str


@dataclass(frozen=True)
class AppLogsResult:
    name: str
    follow: bool
    output: Union[str, Iterable[Union[bytes, str]]]
    tail: int
    path: Optional[str] = None
