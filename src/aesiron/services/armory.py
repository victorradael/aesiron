import os
from pathlib import Path
from typing import Mapping, Optional


def resolve_armory_dir(
    custom_path: Optional[str] = None,
    env: Optional[Mapping[str, str]] = None,
    cwd: Optional[Path] = None,
):
    """
    Define o Arsenal. Ordem de prioridade:
    1. Argumento direto da CLI
    2. Variavel de ambiente AESIRON_ARMORY
    3. Diretorio atual (CWD)
    """
    env = os.environ if env is None else env

    if custom_path:
        return Path(custom_path).resolve()

    armory_env = env.get("AESIRON_ARMORY")
    if armory_env:
        return Path(armory_env).resolve()

    return (cwd or Path.cwd()).resolve()


def get_armory_dir(
    custom_path: Optional[str] = None,
    create: bool = True,
    env: Optional[Mapping[str, str]] = None,
    cwd: Optional[Path] = None,
):
    path = resolve_armory_dir(custom_path, env=env, cwd=cwd)
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def list_apps(armory_path: Optional[str] = None):
    armory = get_armory_dir(armory_path, create=False)
    if not armory.exists():
        return []

    apps = []
    for item in armory.iterdir():
        if item.is_dir() and (item / "Makefile").exists():
            apps.append(item.name)
    return sorted(apps)
