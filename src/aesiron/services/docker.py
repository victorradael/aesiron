import shutil
import socket
import subprocess
from pathlib import Path
from typing import Mapping, Optional

import docker
from docker.errors import NotFound
from docker.types import IPAMConfig, IPAMPool

from ..domain.errors import AppAlreadyExistsError, AppNotFoundError
from .armory import get_armory_dir
from .scaffold import ensure_streamlit_runtime_config, rewrite_app_references

client = None
NETWORK_NAME = "aesiron-net"
NETWORK_SUBNET = "172.28.0.0/24"


def get_docker_client():
    global client
    if client is None:
        client = docker.from_env()
    return client


def ensure_network(network_name: str = NETWORK_NAME):
    docker_client = get_docker_client()
    try:
        docker_client.networks.get(network_name)
    except NotFound:
        ipam_pool = IPAMPool(subnet=NETWORK_SUBNET)
        ipam_config = IPAMConfig(pool_configs=[ipam_pool])
        docker_client.networks.create(network_name, driver="bridge", ipam=ipam_config)


def run_make_target(app_dir: Path, command: str):
    return subprocess.run(
        ["make", command], cwd=app_dir, capture_output=True, text=True
    )


def run_docker_command(app_name: str, command: str, armory_path: Optional[str] = None):
    armory = get_armory_dir(armory_path)
    app_dir = armory / app_name

    if not app_dir.exists():
        raise AppNotFoundError(f"App {app_name} not found in {armory}.")

    ensure_streamlit_runtime_config(app_dir)
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


def resolve_hostname_locally(hostname: str):
    try:
        return socket.gethostbyname(hostname)
    except OSError:
        return None


def get_app_urls():
    from .infra import get_app_url

    host_ip = get_host_ip()

    return [
        {
            "name": str(container.name).replace("app-aesiron-", ""),
            "port": extract_container_port(container),
            "lan_url": f"http://{host_ip}:{extract_container_port(container)}",
            "dns_url": _build_dns_url_if_available(
                str(container.name).replace("app-aesiron-", ""),
                expected_ip=host_ip,
                build_url=get_app_url,
            ),
        }
        for container in get_running_containers()
    ]


def _build_dns_url_if_available(app_name: str, expected_ip: str, build_url):
    hostname = build_url(app_name)
    if hostname.startswith("http://"):
        hostname = hostname[len("http://") :]
    resolved_ip = resolve_hostname_locally(hostname)
    if resolved_ip != expected_ip:
        return None
    return f"http://{hostname}"


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
