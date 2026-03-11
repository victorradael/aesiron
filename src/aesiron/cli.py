import typer
from typing import Optional
from rich.console import Console
from rich.table import Table
from . import core

app = typer.Typer(
    help="Aesiron: Forje e gerencie múltiplos apps Streamlit com Docker.",
    rich_markup_mode="rich",
)
console = Console()


def version_callback(value: bool):
    if value:
        import importlib.metadata
        try:
            __version__ = importlib.metadata.version("aesiron")
        except importlib.metadata.PackageNotFoundError:
            __version__ = "unknown"
        console.print(f"Aesiron v[bold cyan]{__version__}[/bold cyan]")
        raise typer.Exit()


@app.callback()
def callback(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Mostra a versão da CLI e sai.",
        callback=version_callback,
        is_eager=True,
    )
):
    pass


@app.command()
def version():
    """Mostra a versão atual da CLI."""
    import importlib.metadata
    try:
        __version__ = importlib.metadata.version("aesiron")
    except importlib.metadata.PackageNotFoundError:
        __version__ = "unknown"
    console.print(f"Aesiron v[bold cyan]{__version__}[/bold cyan]")


@app.command()
def help(ctx: typer.Context):
    """Mostra esta mensagem de ajuda."""
    banner()
    console.print(ctx.parent.get_help())


def banner():
    console.print("[bold cyan]    _    _____ ____ ___ ____   ___  _   _ [/bold cyan]")
    console.print(
        "[bold cyan]   / \\  | ____/ ___|_ _|  _ \\ / _ \\| \\ | |[/bold cyan]"
    )
    console.print(
        "[bold cyan]  / _ \\ |  _| \\___ \\| || |_) | | | |  \\| |[/bold cyan]"
    )
    console.print("[bold cyan] / ___ \\| |___ ___) | ||  _ <| |_| | |\\  |[/bold cyan]")
    console.print(
        "[bold cyan]/_/   \\_\\_____|____/___|_| \\_\\ ___/|_| \\_|[/bold cyan]"
    )


@app.command()
def init(
    path: Optional[str] = typer.Option(
        None, "--path", "-p", help="Caminho customizado para o Arsenal"
    ),
):
    """Inicializa um diretório como um ambiente Aesiron (Arsenal)."""
    banner()
    armory_path = core.get_armory_dir(path)
    console.print(
        f"[bold green]✓[/bold green] Arsenal inicializado no diretório atual: [cyan]{armory_path}[/cyan]"
    )


@app.command()
def forge(
    name: str,
    port: int = typer.Option(8501, help="Porta para o app."),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Caminho do Arsenal"),
):
    """Forja um novo app independente na Armaria."""
    banner()
    try:
        with console.status(f"[bold yellow]Forjando {name}...[/bold yellow]"):
            forge_path = core.forge_app(name, port, path)
        console.print(
            f"[bold green]✓[/bold green] App [bold]{name}[/bold] forjado com sucesso em [cyan]{forge_path}[/cyan] na porta [yellow]{port}[/yellow]!"
        )
    except Exception as e:
        console.print(f"[bold red]Erro:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def list(
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Caminho do Arsenal"),
):
    """Lista todos os apps forjados na Armaria."""
    banner()
    apps = core.list_apps(path)
    if not apps:
        console.print("[yellow]Nenhum app encontrado na Armaria.[/yellow]")
        return

    table = Table(title="Apps no Arsenal")
    table.add_column("Nome", style="cyan")
    table.add_column("Status", style="green")

    running = [
        c.name.replace("app-aesiron-", "") for c in core.get_running_containers()
    ]

    for app_name in apps:
        status = "[bold green]Rodando[/bold green]" if app_name in running else "Parado"
        table.add_row(app_name, status)

    console.print(table)


@app.command()
def run(
    name: Optional[str] = typer.Argument(None),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Caminho do Arsenal"),
):
    """Inicia os apps (todos ou um específico)."""
    apps = [name] if name else core.list_apps(path)
    if not apps:
        console.print("[yellow]Nenhum app para rodar.[/yellow]")
        return

    for app_name in apps:
        console.print(f"🚀 Iniciando [bold]{app_name}[/bold]...")
        output = core.run_docker_command(app_name, "run", path)
        console.print(output)

    urls()


@app.command()
def stop(
    name: Optional[str] = typer.Argument(None),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Caminho do Arsenal"),
):
    """Para os apps (todos ou um específico)."""
    apps = [name] if name else core.list_apps(path)
    if not apps:
        console.print("[yellow]Nenhum app para parar.[/yellow]")
        return

    for app_name in apps:
        console.print(f"🛑 Parando [bold]{app_name}[/bold]...")
        output = core.run_docker_command(app_name, "down", path)
        console.print(output)


@app.command()
def urls():
    """Mostra as URLs de acesso local para os apps rodando."""

    def get_ip():
        import os

        # Se estamos rodando dentro de um container Docker (onde a CLI foi chamada via imagem)
        if os.path.exists("/.dockerenv"):
            try:
                import docker

                client = docker.from_env()
                # Roda um container rápido na rede host para descobrir o IP real da LAN
                script = "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(('10.255.255.255', 1)); print(s.getsockname()[0], end='')"
                out = client.containers.run(
                    "python:3.11-slim",
                    f'python -c "{script}"',
                    network_mode="host",
                    remove=True,
                )
                return out.decode("utf-8").strip()
            except Exception:
                pass  # Fallback caso a API do Docker não esteja disponível

        # Comportamento padrão (p/ quando instalada via pip no host ou fallback)
        import socket

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("10.255.255.255", 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = "127.0.0.1"
        finally:
            s.close()
        return IP

    ip = get_ip()
    containers = core.get_running_containers()

    if not containers:
        console.print(
            "\n[bold red][!] Nenhuma aplicação está rodando no momento.[/bold red]\n"
        )
        return

    console.print(
        "\n[bold cyan]┌──────────────────────────────────────────────────────────┐[/bold cyan]"
    )
    console.print(
        "[bold cyan]│          🚀 APLICATIVOS DISPONÍVEIS NA REDE              │[/bold cyan]"
    )
    console.print(
        "[bold cyan]└──────────────────────────────────────────────────────────┘[/bold cyan]"
    )

    for container in containers:
        app_name = container.name.replace("app-aesiron-", "")
        # Extrair porta do container (docker-py)
        ports = container.attrs["NetworkSettings"]["Ports"]
        port = ""
        for p in ports:
            if ports[p]:
                port = ports[p][0]["HostPort"]
                break

        console.print(
            f"  [bold yellow]{app_name:15}[/bold yellow] [bold green]➜[/bold green]  http://{ip}:{port}"
        )
    console.print("")


@app.command()
def destroy(
    name: str,
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Caminho do Arsenal"),
):
    """Remove um app permanentemente da Armaria."""
    if typer.confirm(f"Tem certeza que deseja DESTRUIR o app '{name}'?"):
        try:
            core.destroy_app(name, path)
            console.print(
                f"[bold green]✓[/bold green] App [bold]{name}[/bold] destruído com sucesso."
            )
        except Exception as e:
            console.print(f"[bold red]Erro:[/bold red] {e}")


if __name__ == "__main__":
    app()
