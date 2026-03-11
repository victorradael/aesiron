import os
import shutil
import docker
import subprocess
from pathlib import Path
from rich.console import Console

console = Console()
client = docker.from_env()

# Utiliza o caminho do arquivo instalado para encontrar o template
BASE_DIR = Path(__file__).parent
TEMPLATE_DIR = BASE_DIR / "template"


def get_armory_dir(custom_path: str = None):
    """
    Define o Arsenal. Ordem de prioridade:
    1. Argumento direto da CLI
    2. Variável de ambiente AESIRON_ARMORY
    3. Diretório atual (CWD)
    """
    if custom_path:
        path = Path(custom_path).resolve()
    else:
        armory_env = os.getenv("AESIRON_ARMORY")
        if armory_env:
            path = Path(armory_env).resolve()
        else:
            path = Path.cwd()

    path.mkdir(parents=True, exist_ok=True)
    return path


def list_apps(armory_path: str = None):
    armory = get_armory_dir(armory_path)
    apps = []
    if not armory.exists():
        return []
    for item in armory.iterdir():
        if item.is_dir() and (item / "Makefile").exists():
            apps.append(item.name)
    return sorted(apps)


def forge_app(name: str, port: int, armory_path: str = None):
    armory = get_armory_dir(armory_path)
    app_dir = armory / name
    if app_dir.exists():
        raise ValueError(f"App {name} already exists in armory ({app_dir}).")

    app_dir.mkdir(parents=True)

    if not TEMPLATE_DIR.exists():
        raise FileNotFoundError(
            f"Template directory not found at {TEMPLATE_DIR}. Are you sure the package is installed correctly?"
        )

    # Copiar template (incluindo arquivos ocultos)
    for item in TEMPLATE_DIR.iterdir():
        dest = app_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)

    # Substituir placeholders
    for root, dirs, files in os.walk(app_dir):
        for file in files:
            path = Path(root) / file
            try:
                content = path.read_text(encoding="utf-8")
                # Se estamos rodando no Docker via alias, usamos o HOST_PWD pra formatar o caminho do volume.
                # Senão, usamos './' (que resolve localmente).
                host_pwd = os.getenv("HOST_PWD")
                app_host_path = f"{host_pwd}/{name}" if host_pwd else "."
                new_content = (
                    content.replace("{{APP_NAME}}", name)
                    .replace("{{PORT}}", str(port))
                    .replace("{{APP_HOST_PATH}}", app_host_path)
                )
                if content != new_content:
                    path.write_text(new_content, encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                pass

    env_example = app_dir / ".env.example"
    if env_example.exists():
        shutil.copy2(env_example, app_dir / ".env")

    # Ajusta as permissões dos arquivos gerados caso rodando sob o alias (Docker)
    host_uid_str = os.getenv("HOST_UID")
    host_gid_str = os.getenv("HOST_GID")
    if host_uid_str and host_gid_str:
        try:
            uid = int(host_uid_str)
            gid = int(host_gid_str)
            for file_root, dirs, files_list in os.walk(app_dir):
                for d in dirs:
                    os.chown(os.path.join(file_root, d), uid, gid)
                for f in files_list:
                    os.chown(os.path.join(file_root, f), uid, gid)
            os.chown(app_dir, uid, gid)
        except Exception as e:
            console.print(
                f"[yellow]Aviso: Não foi possível alterar a permissão dos arquivos para o usuário host: {e}[/yellow]"
            )

    return app_dir


def run_docker_command(app_name: str, command: str, armory_path: str = None):
    armory = get_armory_dir(armory_path)
    app_dir = armory / app_name

    if not app_dir.exists():
        raise ValueError(f"App {app_name} not found in {armory}.")

    try:
        client.networks.get("aesiron-net")
    except docker.errors.NotFound:
        client.networks.create("aesiron-net", driver="bridge")

    result = subprocess.run(
        ["make", command], cwd=app_dir, capture_output=True, text=True
    )
    return result.stdout + result.stderr


def get_running_containers():
    try:
        return client.containers.list(filters={"name": "app-aesiron-"})
    except Exception:
        return []


def destroy_app(name: str, armory_path: str = None):
    armory = get_armory_dir(armory_path)
    app_dir = armory / name
    if not app_dir.exists():
        raise ValueError(f"App {name} not found.")

    subprocess.run(["make", "down"], cwd=app_dir, capture_output=True)

    image_name = f"app-aesiron-{name}"
    try:
        client.images.remove(image_name, force=True)
    except Exception:
        pass

    shutil.rmtree(app_dir)


def restart_app(name: str, armory_path: str = None):
    """Para e reinicia um app existente."""
    armory = get_armory_dir(armory_path)
    app_dir = armory / name
    if not app_dir.exists():
        raise ValueError(f"App {name} not found in {armory}.")

    run_docker_command(name, "down", armory_path)
    run_docker_command(name, "run", armory_path)


def get_app_logs(name: str, armory_path: str = None, tail: int = 100, follow: bool = False):
    """
    Retorna os logs do container de um app.
    Se follow=True, retorna um gerador de linhas para streaming.
    Se follow=False, retorna uma string com as últimas `tail` linhas.
    """
    container_name = f"app-aesiron-{name}"
    try:
        container = client.containers.get(container_name)
    except docker.errors.NotFound:
        raise ValueError(f"App {name} is not running (container '{container_name}' not found).")

    if follow:
        return container.logs(tail=tail, stream=True, follow=True)
    else:
        raw = container.logs(tail=tail, stream=False)
        return raw.decode("utf-8", errors="replace")


def get_app_status(armory_path: str = None):
    """
    Retorna uma lista de dicionários com métricas de cada container rodando.
    Campos: name, status, port, uptime, cpu_pct, ram_mb.
    """
    from datetime import datetime, timezone

    containers = get_running_containers()
    result = []

    for container in containers:
        app_name = container.name.replace("app-aesiron-", "")

        # Porta
        ports = container.attrs["NetworkSettings"]["Ports"]
        port = ""
        for p in ports:
            if ports[p]:
                port = ports[p][0]["HostPort"]
                break

        # Uptime
        started_at_str = container.attrs["State"]["StartedAt"]
        try:
            # Python <3.11 não suporta 'Z' diretamente — normaliza
            started_at_str = started_at_str[:26].rstrip("Z") + "+00:00"
            started_at = datetime.fromisoformat(started_at_str).replace(tzinfo=timezone.utc)
            delta = datetime.now(timezone.utc) - started_at
            total_seconds = int(delta.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            uptime = f"{hours}h {minutes:02d}m"
        except Exception:
            uptime = "—"

        # CPU e RAM
        try:
            stats = container.stats(stream=False)

            cpu_delta = (
                stats["cpu_stats"]["cpu_usage"]["total_usage"]
                - stats["precpu_stats"]["cpu_usage"]["total_usage"]
            )
            system_delta = (
                stats["cpu_stats"].get("system_cpu_usage", 0)
                - stats["precpu_stats"].get("system_cpu_usage", 0)
            )
            num_cpus = stats["cpu_stats"].get("online_cpus", 1)
            cpu_pct = (
                f"{(cpu_delta / system_delta) * num_cpus * 100:.1f}%"
                if system_delta > 0
                else "0.0%"
            )

            ram_bytes = stats["memory_stats"].get("usage", 0)
            ram_mb = f"{ram_bytes / (1024 * 1024):.0f} MB"
        except Exception:
            cpu_pct = "—"
            ram_mb = "—"

        result.append(
            {
                "name": app_name,
                "status": "running",
                "port": port,
                "uptime": uptime,
                "cpu_pct": cpu_pct,
                "ram_mb": ram_mb,
            }
        )

    return result


def rename_app(old_name: str, new_name: str, armory_path: str = None):
    """
    Renomeia um app: para o container, renomeia o diretório, substitui referências
    nos arquivos de config e remove a imagem Docker antiga.
    """
    armory = get_armory_dir(armory_path)
    old_dir = armory / old_name
    new_dir = armory / new_name

    if not old_dir.exists():
        raise ValueError(f"App {old_name} not found in {armory}.")
    if new_dir.exists():
        raise ValueError(f"App {new_name} already exists in {armory}.")

    # Para o container antes de renomear
    subprocess.run(["make", "down"], cwd=old_dir, capture_output=True)

    # Remove a imagem antiga
    old_image = f"app-aesiron-{old_name}"
    try:
        client.images.remove(old_image, force=True)
    except Exception:
        pass

    # Renomeia o diretório
    old_dir.rename(new_dir)

    # Substitui todas as ocorrências do nome antigo pelo novo nos arquivos de config
    config_files = ["Makefile", "compose.yml", "docker-compose.yml", "Dockerfile", ".env"]
    for filename in config_files:
        file_path = new_dir / filename
        if file_path.exists():
            try:
                content = file_path.read_text(encoding="utf-8")
                new_content = content.replace(old_name, new_name)
                if content != new_content:
                    file_path.write_text(new_content, encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                pass
