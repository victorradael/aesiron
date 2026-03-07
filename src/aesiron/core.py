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
    3. Padrão 1: ../aesiron-armory (caso de desenvolvimento, vizinho da pasta aesiron)
    4. Padrão 2: ./aesiron-armory (uso standalone local)
    """
    if custom_path:
        path = Path(custom_path).resolve()
    else:
        armory_env = os.getenv("AESIRON_ARMORY")
        if armory_env:
            path = Path(armory_env).resolve()
        else:
            # Prioriza o vizinho do diretório pai (comum no dev do projeto)
            parent_neighbor = Path.cwd().parent / "aesiron-armory"
            if parent_neighbor.exists() and parent_neighbor.is_dir():
                path = parent_neighbor
            else:
                # Caso contrário, usa/cria no diretório atual
                path = Path.cwd() / "aesiron-armory"

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
        if item.name == "Makefile.root":
            continue
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
                new_content = content.replace("{{APP_NAME}}", name).replace(
                    "{{PORT}}", str(port)
                )
                if content != new_content:
                    path.write_text(new_content, encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                pass

    env_example = app_dir / ".env.example"
    if env_example.exists():
        shutil.copy2(env_example, app_dir / ".env")

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
