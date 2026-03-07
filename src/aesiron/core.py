import os
import shutil
import docker
from pathlib import Path
from rich.console import Console

console = Console()
client = docker.from_env()

BASE_DIR = Path(__file__).parent
TEMPLATE_DIR = BASE_DIR / "template"


def get_armory_dir():
    # Definição padrão: pasta aesiron-armory no mesmo nível da pasta aesiron
    # Se estiver rodando dentro de um container, pode ser mapeado via volume
    armory_env = os.getenv("AESIRON_ARMORY", "../aesiron-armory")
    path = Path(armory_env).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def list_apps():
    armory = get_armory_dir()
    apps = []
    for item in armory.iterdir():
        if item.is_dir() and (item / "Makefile").exists():
            apps.append(item.name)
    return sorted(apps)


def forge_app(name: str, port: int):
    armory = get_armory_dir()
    app_dir = armory / name
    if app_dir.exists():
        raise ValueError(f"App {name} already exists in armory.")

    app_dir.mkdir()

    # Copiar template
    for item in TEMPLATE_DIR.iterdir():
        if item.name == "Makefile.root":
            continue  # Pula o backup do Makefile root
        if item.is_dir():
            shutil.copytree(item, app_dir / item.name)
        else:
            shutil.copy2(item, app_dir / item.name)

    # Substituir placeholders
    for root, dirs, files in os.walk(app_dir):
        for file in files:
            path = Path(root) / file
            try:
                content = path.read_text()
                new_content = content.replace("{{APP_NAME}}", name).replace(
                    "{{PORT}}", str(port)
                )
                if content != new_content:
                    path.write_text(new_content)
            except Exception:
                pass  # Ignora arquivos binários ou problemas de encoding

    # Copiar .env.example para .env
    env_example = app_dir / ".env.example"
    if env_example.exists():
        shutil.copy2(env_example, app_dir / ".env")

    return app_dir


def run_docker_command(app_name: str, command: str):
    armory = get_armory_dir()
    app_dir = armory / app_name

    if not app_dir.exists():
        raise ValueError(f"App {app_name} not found.")

    # Criar rede se não existir
    try:
        client.networks.get("aesiron-net")
    except docker.errors.NotFound:
        client.networks.create("aesiron-net", driver="bridge")

    # Usaremos subprocess para rodar o Makefile local do app, pois ele já tem a lógica Docker complexa
    import subprocess

    result = subprocess.run(
        ["make", command], cwd=app_dir, capture_output=True, text=True
    )
    return result.stdout + result.stderr


def get_running_containers():
    return client.containers.list(filters={"name": "app-aesiron-"})


def destroy_app(name: str):
    armory = get_armory_dir()
    app_dir = armory / name
    if not app_dir.exists():
        raise ValueError(f"App {name} not found.")

    # Stop and remove image via Makefile local
    import subprocess

    subprocess.run(["make", "down"], cwd=app_dir)

    image_name = f"app-aesiron-{name}"
    try:
        client.images.remove(image_name, force=True)
    except Exception:
        pass

    shutil.rmtree(app_dir)
