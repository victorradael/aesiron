import typer
from typing import Optional
from rich.console import Console
from rich.table import Table
from .application import (
    configure_dns_client_command,
    destroy_app_command,
    forge_app_command,
    get_app_logs_command,
    get_apps_overview,
    get_app_status_view,
    get_app_urls_view,
    initialize_armory,
    rename_app_command,
    resolve_target_apps,
    reset_dns_client_command,
    restart_apps_command,
    run_apps_command,
    stop_apps_command,
)
from .domain.errors import AppNotFoundError

app = typer.Typer(
    help="Aesiron: Forje e gerencie múltiplos apps Streamlit com Docker.",
    rich_markup_mode="rich",
)
console = Console()


def get_version() -> str:
    import importlib.metadata

    try:
        return importlib.metadata.version("aesiron")
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def version_callback(value: bool):
    if value:
        console.print(f"Aesiron v[bold cyan]{get_version()}[/bold cyan]")
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
    console.print(f"Aesiron v[bold cyan]{get_version()}[/bold cyan]")


@app.command()
def help(ctx: typer.Context):
    """Mostra esta mensagem de ajuda."""
    banner()
    root = ctx.find_root()
    console.print(root.get_help() if root else ctx.get_help())


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
    armory_path = initialize_armory(path)
    console.print(
        f"[bold green]✓[/bold green] Arsenal inicializado no diretório atual: [cyan]{armory_path}[/cyan]"
    )


@app.command()
def forge(
    name: str,
    port: Optional[int] = typer.Option(None, help="Porta para o app. Se omitido, busca a próxima disponível a partir de 8501."),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Caminho do Arsenal"),
):
    """Forja um novo app independente na Armaria."""
    banner()
    from .services.docker import find_next_available_port

    if port is None:
        port = find_next_available_port(armory_path=path)

    try:
        with console.status(f"[bold yellow]Forjando {name}...[/bold yellow]"):
            forge_path = forge_app_command(name, port, path)
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
    app_overview = get_apps_overview(path)
    if not app_overview:
        console.print("[yellow]Nenhum app encontrado na Armaria.[/yellow]")
        return

    table = Table(title="Apps no Arsenal")
    table.add_column("Nome", style="cyan")
    table.add_column("Status", style="green")

    for app_data in app_overview:
        status = "[bold green]Rodando[/bold green]" if app_data.running else "Parado"
        table.add_row(app_data.name, status)

    console.print(table)


@app.command()
def run(
    name: Optional[str] = typer.Argument(None),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Caminho do Arsenal"),
):
    """Inicia os apps (todos ou um específico)."""
    try:
        executions = run_apps_command(name, path)
        if not executions:
            console.print("[yellow]Nenhum app para rodar.[/yellow]")
            return

        for execution in executions:
            console.print(f"🚀 Iniciando [bold]{execution.name}[/bold]...")
            console.print(execution.output)

        urls(path)
    except AppNotFoundError as e:
        console.print(f"[bold red]Erro:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def stop(
    name: Optional[str] = typer.Argument(None),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Caminho do Arsenal"),
):
    """Para os apps (todos ou um específico)."""
    try:
        executions = stop_apps_command(name, path)
        if not executions:
            console.print("[yellow]Nenhum app para parar.[/yellow]")
            return

        for execution in executions:
            console.print(f"🛑 Parando [bold]{execution.name}[/bold]...")
            console.print(execution.output)
    except AppNotFoundError as e:
        console.print(f"[bold red]Erro:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def urls(
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Caminho do Arsenal"),
):
    """Mostra as URLs de acesso local para os apps rodando."""
    app_urls = get_app_urls_view(path)

    if not app_urls:
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

    table = Table(border_style="cyan")
    table.add_column("App", style="bold yellow")
    table.add_column("LAN", style="green")
    table.add_column("DNS local", style="cyan")

    for app_data in app_urls:
        table.add_row(
            app_data.name,
            app_data.lan_url,
            app_data.dns_url or "[dim]Nao configurado[/dim]",
        )

    console.print(table)
    console.print(
        "\n[dim]Use `aesiron dns-setup` nesta maquina para configurar o resolvedor local automaticamente.[/dim]"
    )
    console.print("")


@app.command(name="dns-setup")
def dns_setup(
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Caminho do Arsenal"),
):
    """Configura apenas esta maquina para resolver hosts do Aesiron sem trocar o DNS global."""
    setup = configure_dns_client_command(path)
    console.print("[bold cyan]Configuracao local de DNS aplicada[/bold cyan]\n")
    for line in setup.lines:
        console.print(f"- {line}")
    console.print("")


@app.command(name="dns-reset")
def dns_reset(
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Caminho do Arsenal"),
):
    """Remove as entradas locais do Aesiron do /etc/hosts."""
    result = reset_dns_client_command(path)
    console.print("[bold cyan]Configuracao local de DNS removida[/bold cyan]\n")
    for line in result.lines:
        console.print(f"- {line}")
    console.print("")


@app.command()
def destroy(
    name: str,
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Caminho do Arsenal"),
):
    """Remove um app permanentemente da Armaria."""
    if typer.confirm(f"Tem certeza que deseja DESTRUIR o app '{name}'?"):
        try:
            destroy_app_command(name, path)
            console.print(
                f"[bold green]✓[/bold green] App [bold]{name}[/bold] destruído com sucesso."
            )
        except Exception as e:
            console.print(f"[bold red]Erro:[/bold red] {e}")


@app.command()
def restart(
    name: Optional[str] = typer.Argument(None),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Caminho do Arsenal"),
):
    """Reinicia os apps (todos ou um específico)."""
    apps = resolve_target_apps(name, path)
    if not apps:
        console.print("[yellow]Nenhum app encontrado para reiniciar.[/yellow]")
        return

    try:
        for app_name in apps:
            with console.status(f"[bold yellow]Reiniciando {app_name}...[/bold yellow]"):
                restart_apps_command(app_name, path)
            console.print(
                f"[bold green]✓[/bold green] App [bold]{app_name}[/bold] reiniciado com sucesso."
            )
    except Exception as e:
        console.print(f"[bold red]Erro:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def logs(
    name: str,
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Caminho do Arsenal"),
    tail: int = typer.Option(100, "--tail", "-n", help="Número de linhas a exibir."),
    follow: bool = typer.Option(False, "--follow", "-f", help="Seguir os logs em tempo real."),
):
    """Exibe os logs de um app."""
    try:
        logs_result = get_app_logs_command(name, path, tail=tail, follow=follow)
        if logs_result.follow:
            console.print(f"[dim]Seguindo logs de [bold]{name}[/bold] — Ctrl+C para sair[/dim]\n")
            try:
                for chunk in logs_result.output:
                    if isinstance(chunk, bytes):
                        chunk = chunk.decode("utf-8", errors="replace")
                    console.print(chunk, end="")
            except KeyboardInterrupt:
                console.print("\n[dim]Streaming encerrado.[/dim]")
        else:
            console.print(logs_result.output)
    except ValueError as e:
        console.print(f"[bold red]Erro:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def status(
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Caminho do Arsenal"),
):
    """Exibe um painel com métricas de todos os apps rodando."""
    status_view = get_app_status_view(path)
    app_list = status_view.apps

    if not app_list:
        console.print("[yellow]Nenhum app encontrado no Arsenal.[/yellow]")
        return

    statuses = status_view.statuses

    if not statuses:
        console.print(
            "\n[bold red][!] Nenhuma aplicação está rodando no momento.[/bold red]\n"
        )
        return

    running_names = status_view.running_names

    table = Table(title="Status do Arsenal", border_style="cyan")
    table.add_column("App", style="bold cyan", no_wrap=True)
    table.add_column("Status", justify="center")
    table.add_column("Porta", justify="center", style="yellow")
    table.add_column("Uptime", justify="right")
    table.add_column("CPU", justify="right", style="magenta")
    table.add_column("RAM", justify="right", style="green")

    status_map = status_view.status_map

    for app_name in app_list:
        if app_name in running_names:
            s = status_map[app_name]
            table.add_row(
                app_name,
                "[bold green]✅ Rodando[/bold green]",
                s.port,
                s.uptime,
                s.cpu_pct,
                s.ram_mb,
            )
        else:
            table.add_row(
                app_name,
                "[dim]⛔ Parado[/dim]",
                "—",
                "—",
                "—",
                "—",
            )

    console.print(table)


@app.command()
def rename(
    old_name: str,
    new_name: str,
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Caminho do Arsenal"),
):
    """Renomeia um app existente na Armaria."""
    if typer.confirm(f"Renomear '{old_name}' → '{new_name}'?"):
        try:
            with console.status(f"[bold yellow]Renomeando {old_name} → {new_name}...[/bold yellow]"):
                rename_app_command(old_name, new_name, path)
            console.print(
                f"[bold green]✓[/bold green] App renomeado: "
                f"[bold]{old_name}[/bold] → [bold cyan]{new_name}[/bold cyan]"
            )
        except Exception as e:
            console.print(f"[bold red]Erro:[/bold red] {e}")
            raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
