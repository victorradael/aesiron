import os
import shutil
from pathlib import Path
from typing import Mapping, Optional

from rich.console import Console

from ..domain.errors import AppAlreadyExistsError
from .armory import get_armory_dir

console = Console()

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = BASE_DIR / "template"


def render_template_content(
    content: str, name: str, port: int, env: Optional[Mapping[str, str]] = None
):
    env = os.environ if env is None else env
    host_pwd = env.get("HOST_PWD")
    app_host_path = f"{host_pwd}/{name}" if host_pwd else "."
    return (
        content.replace("{{APP_NAME}}", name)
        .replace("{{PORT}}", str(port))
        .replace("{{APP_HOST_PATH}}", app_host_path)
    )


def copy_template_tree(template_dir: Path, app_dir: Path):
    for item in template_dir.iterdir():
        dest = app_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)


def apply_template_placeholders(
    app_dir: Path, name: str, port: int, env: Optional[Mapping[str, str]] = None
):
    for root, _, files in os.walk(app_dir):
        for file_name in files:
            path = Path(root) / file_name
            try:
                content = path.read_text(encoding="utf-8")
                new_content = render_template_content(content, name, port, env=env)
                if content != new_content:
                    path.write_text(new_content, encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                pass


def copy_default_env(app_dir: Path):
    env_example = app_dir / ".env.example"
    if env_example.exists():
        shutil.copy2(env_example, app_dir / ".env")


def apply_host_ownership(app_dir: Path, env: Optional[Mapping[str, str]] = None):
    env = os.environ if env is None else env
    host_uid_str = env.get("HOST_UID")
    host_gid_str = env.get("HOST_GID")
    if not (host_uid_str and host_gid_str):
        return

    try:
        uid = int(host_uid_str)
        gid = int(host_gid_str)
        for file_root, dirs, files_list in os.walk(app_dir):
            for directory in dirs:
                os.chown(os.path.join(file_root, directory), uid, gid)
            for file_name in files_list:
                os.chown(os.path.join(file_root, file_name), uid, gid)
        os.chown(app_dir, uid, gid)
    except Exception as exc:
        console.print(
            f"[yellow]Aviso: Nao foi possivel alterar a permissao dos arquivos para o usuario host: {exc}[/yellow]"
        )


def rewrite_app_references(app_dir: Path, old_name: str, new_name: str):
    config_files = ["Makefile", "compose.yml", "docker-compose.yml", "Dockerfile", ".env"]
    for filename in config_files:
        file_path = app_dir / filename
        if not file_path.exists():
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
            new_content = content.replace(old_name, new_name)
            if content != new_content:
                file_path.write_text(new_content, encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            pass


def forge_app(name: str, port: int, armory_path: Optional[str] = None):
    armory = get_armory_dir(armory_path)
    app_dir = armory / name
    if app_dir.exists():
        raise AppAlreadyExistsError(f"App {name} already exists in armory ({app_dir}).")

    if not TEMPLATE_DIR.exists():
        raise FileNotFoundError(
            f"Template directory not found at {TEMPLATE_DIR}. Are you sure the package is installed correctly?"
        )

    app_dir.mkdir(parents=True)
    copy_template_tree(TEMPLATE_DIR, app_dir)
    apply_template_placeholders(app_dir, name, port)
    copy_default_env(app_dir)
    apply_host_ownership(app_dir)
    return app_dir
