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

    # Extrair porta do compose.yml para garantir que o runtime esteja sincronizado
    port = None
    compose_path = app_dir / "compose.yml"
    if not compose_path.exists():
        compose_path = app_dir / "docker-compose.yml"
    
    if compose_path.exists():
        import yaml
        try:
            with open(compose_path, 'r') as f:
                config = yaml.safe_load(f)
                services = config.get("services", {})
                for service in services.values():
                    ports_list = service.get("ports", [])
                    for p in ports_list:
                        if isinstance(p, str):
                            port = int(p.split(":")[0])
                        elif isinstance(p, dict):
                            port = int(p.get("published"))
        except (Exception, ValueError):
            pass

    ensure_streamlit_runtime_config(app_dir, port or 8501)
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


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def find_next_available_port(start_port: int = 8501, armory_path: Optional[str] = None) -> int:
    used_ports = set()
    
    # 1. Check running containers
    current_containers = get_running_containers()
    for container in current_containers:
        ports = container.attrs.get("NetworkSettings", {}).get("Ports", {})
        if ports:
            for host_bindings in ports.values():
                if host_bindings:
                    for binding in host_bindings:
                        try:
                            used_ports.add(int(binding.get("HostPort", 0)))
                        except (ValueError, TypeError):
                            pass
        
    # 2. Check all forged apps in the armory (even if not running)
    from .armory import get_armory_dir
    import yaml
    
    armory = get_armory_dir(armory_path, create=False)
    if armory.exists():
        for app_dir in armory.iterdir():
            if not app_dir.is_dir():
                continue
            compose_path = app_dir / "compose.yml"
            if not compose_path.exists():
                compose_path = app_dir / "docker-compose.yml"
            
            if compose_path.exists():
                try:
                    with open(compose_path, 'r') as f:
                        config = yaml.safe_load(f)
                        services = config.get("services", {})
                        for service in services.values():
                            ports_list = service.get("ports", [])
                            for p in ports_list:
                                if isinstance(p, str):
                                    # Handle "HOST:CONTAINER" or just "PORT"
                                    host_port = p.split(":")[0]
                                    try:
                                        used_ports.add(int(host_port))
                                    except ValueError:
                                        pass
                                elif isinstance(p, dict):
                                    host_port = p.get("published")
                                    if host_port:
                                        try:
                                            used_ports.add(int(host_port))
                                        except ValueError:
                                            pass
                except Exception:
                    # Ignore malformed or unreadable files
                    pass

    port = start_port
    while port in used_ports or is_port_in_use(port):
        port += 1
    return port


def resolve_hostname_locally(hostname: str):
    try:
        return socket.gethostbyname(hostname)
    except OSError:
        return None


def get_app_urls(armory_path: Optional[str] = None):
    from .infra import get_app_url, read_local_dns_state

    host_ip = get_host_ip()
    configured_hostnames = set(read_local_dns_state(armory_path))

    return [
        {
            "name": str(container.name).replace("app-aesiron-", ""),
            "port": extract_container_port(container),
            "lan_url": f"http://{host_ip}:{extract_container_port(container)}",
            "dns_url": _build_dns_url_if_available(
                str(container.name).replace("app-aesiron-", ""),
                expected_ip=host_ip,
                build_url=get_app_url,
                configured_hostnames=configured_hostnames,
            ),
        }
        for container in get_running_containers()
    ]


def _build_dns_url_if_available(app_name: str, expected_ip: str, build_url, configured_hostnames):
    hostname = build_url(app_name)
    if hostname.startswith("http://"):
        hostname = hostname[len("http://") :]
    if hostname in configured_hostnames:
        return f"http://{hostname}"
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
