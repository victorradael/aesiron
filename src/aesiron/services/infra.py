import os
import re
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path
from typing import Any, List, Mapping, Sequence, cast

from docker.errors import NotFound

from .armory import get_armory_dir

DNS_CONTAINER_NAME = "aesiron-dns"
DNS_IMAGE = "jpillora/dnsmasq:latest"
DNS_ZONE = "iron"
DNS_PORT = 53
DNS_CONFIG_FILENAME = "dnsmasq.conf"
FALLBACK_RESOLVERS = ["1.1.1.1", "8.8.8.8"]
FILE_HELPER_IMAGE = "alpine:3.20"
GATEWAY_CONTAINER_NAME = "aesiron-gateway"
GATEWAY_IMAGE = "nginx:1.27-alpine"
GATEWAY_PORT = 80
GATEWAY_CONFIG_FILENAME = "nginx.conf"
INFRA_DIR_NAME = ".aesiron-infra"
LOCAL_DNS_STATE_FILENAME = "local-dns-hosts.txt"
NETWORK_NAME = "aesiron-net"
HOSTS_BEGIN_MARKER = "# >>> aesiron dns >>>"
HOSTS_END_MARKER = "# <<< aesiron dns <<<"


def normalize_app_name(name: str) -> str:
    normalized = name.strip().lower().replace("_", " ")
    normalized = re.sub(r"\s+", "-", normalized)
    normalized = re.sub(r"[^a-z0-9-]", "-", normalized)
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized or "app"


def get_app_hostname(name: str) -> str:
    return f"{normalize_app_name(name)}.{DNS_ZONE}"


def get_app_url(name: str) -> str:
    return f"http://{get_app_hostname(name)}"


def get_infra_dir(armory_path: str | None = None) -> Path:
    armory = get_armory_dir(armory_path)
    infra_dir = armory / INFRA_DIR_NAME
    infra_dir.mkdir(parents=True, exist_ok=True)
    return infra_dir


def resolve_docker_bind_path(path: Path, env: Mapping[str, str] | None = None) -> Path:
    env = os.environ if env is None else env
    host_pwd = env.get("HOST_PWD")
    if not host_pwd:
        return path

    try:
        relative_path = path.resolve().relative_to(Path("/armory"))
    except ValueError:
        return path

    return Path(host_pwd).resolve() / relative_path


def get_gateway_config_path(armory_path: str | None = None) -> Path:
    return get_infra_dir(armory_path) / GATEWAY_CONFIG_FILENAME


def get_dns_config_path(armory_path: str | None = None) -> Path:
    return get_infra_dir(armory_path) / DNS_CONFIG_FILENAME


def get_local_dns_state_path(armory_path: str | None = None) -> Path:
    return get_infra_dir(armory_path) / LOCAL_DNS_STATE_FILENAME


def write_local_dns_state(hostnames: Sequence[str], armory_path: str | None = None):
    state_path = get_local_dns_state_path(armory_path)
    state_path.write_text("\n".join(sorted(set(hostnames))) + "\n", encoding="utf-8")


def read_local_dns_state(armory_path: str | None = None) -> List[str]:
    state_path = get_local_dns_state_path(armory_path)
    if not state_path.exists():
        return []
    return [line.strip() for line in state_path.read_text(encoding="utf-8").splitlines() if line.strip()]


def remove_local_dns_state(armory_path: str | None = None):
    get_local_dns_state_path(armory_path).unlink(missing_ok=True)


def is_containerized_runtime() -> bool:
    return Path("/.dockerenv").exists()


def extract_container_target_port(container) -> str:
    ports = container.attrs.get("NetworkSettings", {}).get("Ports", {})
    for port_key, port_bindings in ports.items():
        if port_bindings:
            return str(port_key).split("/", 1)[0]
    for port_key in ports:
        return str(port_key).split("/", 1)[0]

    exposed_ports = container.attrs.get("Config", {}).get("ExposedPorts", {})
    for port_key in exposed_ports:
        return str(port_key).split("/", 1)[0]
    return "8501"


def get_upstream_nameservers(resolv_conf: Path = Path("/etc/resolv.conf")) -> List[str]:
    try:
        lines = resolv_conf.read_text(encoding="utf-8").splitlines()
    except OSError:
        return FALLBACK_RESOLVERS.copy()

    nameservers: List[str] = []
    for line in lines:
        line = line.strip()
        if not line.startswith("nameserver "):
            continue
        nameserver = line.split(None, 1)[1].strip()
        if nameserver.startswith("127.") or nameserver == "::1":
            continue
        nameservers.append(nameserver)

    return nameservers or FALLBACK_RESOLVERS.copy()


def build_dnsmasq_config(host_ip: str, upstream_nameservers: Sequence[str]) -> str:
    upstream_block = "\n".join(f"server={server}" for server in upstream_nameservers)
    return textwrap.dedent(
        f"""
        no-daemon
        log-facility=-
        bind-interfaces
        port={DNS_PORT}
        domain-needed
        bogus-priv
        expand-hosts
        local=/{DNS_ZONE}/
        address=/.{DNS_ZONE}/{host_ip}
        {upstream_block}
        """
    ).strip() + "\n"


def build_gateway_config(containers: Sequence[Any]) -> str:
    server_blocks = []
    for container in sorted(containers, key=lambda item: str(item.name)):
        app_name = str(container.name).replace("app-aesiron-", "")
        hostname = get_app_hostname(app_name)
        target_port = extract_container_target_port(container)
        server_blocks.append(
            textwrap.dedent(
                f"""
                server {{
                    listen {GATEWAY_PORT};
                    server_name {hostname};

                    location / {{
                        proxy_pass http://{container.name}:{target_port};
                        proxy_http_version 1.1;
                        proxy_set_header Upgrade $http_upgrade;
                        proxy_set_header Connection $connection_upgrade;
                        proxy_set_header Host $host;
                        proxy_set_header X-Real-IP $remote_addr;
                        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                        proxy_set_header X-Forwarded-Proto $scheme;
                        proxy_buffering off;
                        proxy_read_timeout 86400;
                    }}
                }}
                """
            ).strip()
        )

    server_config = "\n\n".join(server_blocks)
    return textwrap.dedent(
        f"""
        worker_processes auto;

        events {{
            worker_connections 1024;
        }}

        http {{
            resolver 127.0.0.11 ipv6=off;
            map $http_upgrade $connection_upgrade {{
                default upgrade;
                '' close;
            }}

            server {{
                listen {GATEWAY_PORT} default_server;
                return 404;
            }}

            {server_config}
        }}
        """
    ).strip() + "\n"


def write_gateway_config(containers: Sequence[Any], armory_path: str | None = None) -> Path:
    config_path = get_gateway_config_path(armory_path)
    config_path.write_text(build_gateway_config(containers), encoding="utf-8")
    return config_path


def write_dns_config(
    host_ip: str,
    upstream_nameservers: Sequence[str],
    armory_path: str | None = None,
) -> Path:
    config_path = get_dns_config_path(armory_path)
    config_path.write_text(
        build_dnsmasq_config(host_ip, upstream_nameservers),
        encoding="utf-8",
    )
    return config_path


def _get_container(name: str):
    from .docker import get_docker_client

    try:
        return get_docker_client().containers.get(name)
    except NotFound:
        return None


def _recreate_container(name: str, run_kwargs: dict[str, Any]):
    from .docker import get_docker_client

    container = _get_container(name)
    if container is not None:
        container.remove(force=True)
    return cast(Any, get_docker_client().containers).run(**run_kwargs)


def remove_infra_containers():
    for name in (DNS_CONTAINER_NAME, GATEWAY_CONTAINER_NAME):
        container = _get_container(name)
        if container is not None:
            container.remove(force=True)


def remove_infra_state(armory_path: str | None = None):
    infra_dir = get_armory_dir(armory_path) / INFRA_DIR_NAME
    if infra_dir.exists():
        shutil.rmtree(infra_dir)


def ensure_gateway_service(containers: Sequence[Any], armory_path: str | None = None):
    from .docker import ensure_network

    ensure_network()
    config_path = write_gateway_config(containers, armory_path)
    bind_config_path = resolve_docker_bind_path(config_path)
    run_kwargs: dict[str, Any] = {
        "image": GATEWAY_IMAGE,
        "name": GATEWAY_CONTAINER_NAME,
        "detach": True,
        "restart_policy": cast(Any, {"Name": "unless-stopped"}),
        "ports": {f"{GATEWAY_PORT}/tcp": GATEWAY_PORT},
        "volumes": {
            str(bind_config_path): {
                "bind": "/etc/nginx/nginx.conf",
                "mode": "ro",
            }
        },
        "network": NETWORK_NAME,
        "labels": {"aesiron.managed": "true", "aesiron.role": "gateway"},
    }
    return _recreate_container(GATEWAY_CONTAINER_NAME, run_kwargs)


def ensure_dns_service(host_ip: str, armory_path: str | None = None):
    from .docker import ensure_network

    ensure_network()
    config_path = write_dns_config(host_ip, get_upstream_nameservers(), armory_path)
    bind_config_path = resolve_docker_bind_path(config_path)
    run_kwargs: dict[str, Any] = {
        "image": DNS_IMAGE,
        "name": DNS_CONTAINER_NAME,
        "detach": True,
        "restart_policy": cast(Any, {"Name": "unless-stopped"}),
        "ports": {
            f"{DNS_PORT}/udp": (host_ip, DNS_PORT),
            f"{DNS_PORT}/tcp": (host_ip, DNS_PORT),
        },
        "volumes": {
            str(bind_config_path): {
                "bind": "/etc/dnsmasq.conf",
                "mode": "ro",
            }
        },
        "network": NETWORK_NAME,
        "cap_add": ["NET_ADMIN"],
        "labels": {"aesiron.managed": "true", "aesiron.role": "dns"},
    }
    return _recreate_container(DNS_CONTAINER_NAME, run_kwargs)


def sync_network_infra(armory_path: str | None = None):
    from .docker import get_host_ip, get_running_containers

    running_containers = list(get_running_containers())
    if not running_containers:
        remove_infra_containers()
        remove_infra_state(armory_path)
        return {"gateway": None, "dns": None, "host_ip": None}

    host_ip = get_host_ip()
    gateway = ensure_gateway_service(running_containers, armory_path)
    dns = ensure_dns_service(host_ip, armory_path)
    return {"gateway": gateway, "dns": dns, "host_ip": host_ip}


def get_dns_setup_lines(armory_path: str | None = None) -> List[str]:
    from .docker import get_host_ip

    host_ip = get_host_ip()
    return [
        f"Servidor DNS da rede: {host_ip}",
        f"Dominio interno: .{DNS_ZONE}",
        "Configure manualmente esse DNS no dispositivo cliente ou no roteador.",
        f"Depois disso, qualquer app rodando podera ser acessado como http://nome-do-app.{DNS_ZONE}",
        f"Exemplo: http://demo.{DNS_ZONE}",
        f"A configuracao gerada da infra fica em {get_infra_dir(armory_path)}",
    ]


def build_hosts_block(host_ip: str, hostnames: Sequence[str]) -> str:
    if not hostnames:
        return ""
    lines = [HOSTS_BEGIN_MARKER]
    lines.extend(f"{host_ip} {hostname}" for hostname in sorted(set(hostnames)))
    lines.append(HOSTS_END_MARKER)
    return "\n".join(lines)


def render_hosts_file(current_content: str, hosts_block: str) -> str:
    lines = current_content.splitlines()
    filtered: List[str] = []
    inside_block = False

    for line in lines:
        stripped = line.strip()
        if stripped == HOSTS_BEGIN_MARKER:
            inside_block = True
            continue
        if stripped == HOSTS_END_MARKER:
            inside_block = False
            continue
        if not inside_block:
            filtered.append(line)

    while filtered and filtered[-1] == "":
        filtered.pop()

    rendered = "\n".join(filtered)
    if hosts_block:
        if rendered:
            rendered += "\n\n"
        rendered += hosts_block
    return rendered.rstrip() + "\n"


def write_system_hosts(
    content: str,
    target: Path = Path("/etc/hosts"),
    armory_path: str | None = None,
):
    if is_containerized_runtime() and target == Path("/etc/hosts"):
        write_host_file_via_helper(content, target, armory_path)
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    if os.geteuid() == 0:
        target.write_text(content, encoding="utf-8")
        return

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as temp_file:
        temp_file.write(content)
        temp_path = temp_file.name

    try:
        subprocess.run(["sudo", "cp", temp_path, str(target)], check=True)
    finally:
        Path(temp_path).unlink(missing_ok=True)


def read_system_hosts(target: Path = Path("/etc/hosts"), armory_path: str | None = None) -> str:
    if is_containerized_runtime() and target == Path("/etc/hosts"):
        return read_host_file_via_helper(target, armory_path)
    if not target.exists():
        return ""
    return target.read_text(encoding="utf-8")


def read_host_file_via_helper(target: Path, armory_path: str | None = None) -> str:
    from .docker import get_docker_client

    del armory_path
    output = cast(Any, get_docker_client().containers).run(
        FILE_HELPER_IMAGE,
        command=["sh", "-c", "cat /target/hosts || true"],
        remove=True,
        volumes={
            str(target): {"bind": "/target/hosts", "mode": "ro"},
        },
    )
    return output.decode("utf-8") if isinstance(output, bytes) else str(output)


def write_host_file_via_helper(content: str, target: Path, armory_path: str | None = None):
    from .docker import get_docker_client

    helper_source = get_infra_dir(armory_path) / "hosts.generated"
    helper_source.write_text(content, encoding="utf-8")
    host_source = resolve_docker_bind_path(helper_source)

    cast(Any, get_docker_client().containers).run(
        FILE_HELPER_IMAGE,
        command=["sh", "-c", "cat /source/hosts.generated > /target/hosts"],
        remove=True,
        volumes={
            str(host_source.parent): {"bind": "/source", "mode": "ro"},
            str(target): {"bind": "/target/hosts", "mode": "rw"},
        },
    )


def reset_local_dns_client(
    armory_path: str | None = None, target: Path = Path("/etc/hosts")
) -> List[str]:
    current_hosts = read_system_hosts(target, armory_path)
    rendered_hosts = render_hosts_file(current_hosts, "")
    write_system_hosts(rendered_hosts, target, armory_path)
    remove_local_dns_state(armory_path)
    return [
        "Entradas locais do Aesiron removidas de /etc/hosts.",
        "O DNS global da maquina nao foi alterado.",
    ]


def configure_local_dns_client(armory_path: str | None = None) -> List[str]:
    from .docker import get_host_ip
    from .docker import get_running_app_names

    host_ip = get_host_ip()
    running_apps = get_running_app_names()
    hostnames = [get_app_hostname(app_name) for app_name in running_apps]
    target = Path("/etc/hosts")
    current_hosts = read_system_hosts(target, armory_path)
    hosts_block = build_hosts_block(host_ip, hostnames)
    rendered_hosts = render_hosts_file(current_hosts, hosts_block)
    write_system_hosts(rendered_hosts, target, armory_path)
    if hostnames:
        write_local_dns_state(hostnames, armory_path)
    else:
        remove_local_dns_state(armory_path)

    if not hostnames:
        return [
            "Nenhum app rodando no momento; qualquer bloco anterior do Aesiron foi removido de /etc/hosts.",
            "Seu DNS global da maquina foi preservado.",
        ]

    return [
        "Configuracao local aplicada sem alterar o DNS global da maquina.",
        f"Entradas adicionadas em /etc/hosts para: {', '.join(hostnames)}",
        f"Todos os hostnames apontam para {host_ip}",
        f"Teste agora com http://{hostnames[0]}",
        f"Arquivos da infra permanecem em {get_infra_dir(armory_path)}",
    ]
