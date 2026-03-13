import shutil
import socket
import subprocess
from pathlib import Path
from typing import Mapping, Optional

import docker
from docker.errors import NotFound

from ..domain.errors import AppAlreadyExistsError, AppNotFoundError
from .armory import get_armory_dir
from .scaffold import rewrite_app_references

client = None


def get_docker_client():
    global client
    if client is None:
        client = docker.from_env()
    return client


def ensure_network(network_name: str = "aesiron-net"):
    docker_client = get_docker_client()
    try:
        docker_client.networks.get(network_name)
    except NotFound:
        docker_client.networks.create(network_name, driver="bridge")


def run_make_target(app_dir: Path, command: str):
    return subprocess.run(
        ["make", command], cwd=app_dir, capture_output=True, text=True
    )


def run_docker_command(app_name: str, command: str, armory_path: Optional[str] = None):
    armory = get_armory_dir(armory_path)
    app_dir = armory / app_name

    if not app_dir.exists():
        raise AppNotFoundError(f"App {app_name} not found in {armory}.")

    ensure_network()
    result = run_make_target(app_dir, command)
    return result.stdout + result.stderr


def get_running_containers():
    try:
        return get_docker_client().containers.list(filters={"name": "app-aesiron-"})
    except Exception:
        return []


def get_running_app_names():
    return [str(container.name).replace("app-aesiron-", "") for container in get_running_containers()]


def destroy_app(name: str, armory_path: Optional[str] = None):
    armory = get_armory_dir(armory_path)
    app_dir = armory / name
    if not app_dir.exists():
        raise AppNotFoundError(f"App {name} not found.")

    subprocess.run(["make", "down"], cwd=app_dir, capture_output=True)

    image_name = f"app-aesiron-{name}"
    try:
        get_docker_client().images.remove(image_name, force=True)
    except Exception:
        pass

    shutil.rmtree(app_dir)


def restart_app(name: str, armory_path: Optional[str] = None):
    armory = get_armory_dir(armory_path)
    app_dir = armory / name
    if not app_dir.exists():
        raise AppNotFoundError(f"App {name} not found in {armory}.")

    run_docker_command(name, "down", armory_path)
    run_docker_command(name, "run", armory_path)


def get_app_logs(
    name: str,
    armory_path: Optional[str] = None,
    tail: int = 100,
    follow: bool = False,
):
    del armory_path
    container_name = f"app-aesiron-{name}"
    try:
        container = get_docker_client().containers.get(container_name)
    except NotFound:
        raise AppNotFoundError(
            f"App {name} is not running (container '{container_name}' not found)."
        )

    if follow:
        return container.logs(tail=tail, stream=True, follow=True)

    raw = container.logs(tail=tail, stream=False)
    return raw.decode("utf-8", errors="replace")


def get_host_ip(env: Optional[Mapping[str, str]] = None, docker_client=None):
    import os

    env = os.environ if env is None else env

    if env.get("AESIRON_HOST_IP"):
        return env["AESIRON_HOST_IP"]

    if Path("/.dockerenv").exists():
        try:
            docker_client = docker_client or get_docker_client()
            script = (
                "import socket; "
                "s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); "
                "s.connect(('10.255.255.255', 1)); "
                "print(s.getsockname()[0], end='')"
            )
            out = docker_client.containers.run(
                "python:3.11-slim",
                f'python -c "{script}"',
                network_mode="host",
                remove=True,
            )
            return out.decode("utf-8").strip()
        except Exception:
            pass

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("10.255.255.255", 1))
        return sock.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        sock.close()


def extract_container_port(container):
    ports = container.attrs.get("NetworkSettings", {}).get("Ports", {})
    for port_data in ports.values():
        if port_data:
            return port_data[0].get("HostPort", "")
    return ""


def get_app_urls():
    ip = get_host_ip()
    return [
        {
            "name": str(container.name).replace("app-aesiron-", ""),
            "port": extract_container_port(container),
            "url": f"http://{ip}:{extract_container_port(container)}",
        }
        for container in get_running_containers()
    ]


def rename_app(old_name: str, new_name: str, armory_path: Optional[str] = None):
    armory = get_armory_dir(armory_path)
    old_dir = armory / old_name
    new_dir = armory / new_name

    if not old_dir.exists():
        raise AppNotFoundError(f"App {old_name} not found in {armory}.")
    if new_dir.exists():
        raise AppAlreadyExistsError(f"App {new_name} already exists in {armory}.")

    subprocess.run(["make", "down"], cwd=old_dir, capture_output=True)

    old_image = f"app-aesiron-{old_name}"
    try:
        get_docker_client().images.remove(old_image, force=True)
    except Exception:
        pass

    old_dir.rename(new_dir)
    rewrite_app_references(new_dir, old_name, new_name)
