"""
SysAdmin Toolkit CLI - Parancssori felület.

Command-line interface for system administration tasks.

Parancssori felület rendszergazda feladatokhoz.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from . import disk_analyzer, log_analyzer, service_manager, system_health
from .models import ServiceState

# Typer alkalmazás
app = typer.Typer(
    name="sysadmin-toolkit",
    help="SysAdmin Toolkit - Rendszergazda eszköztár / System Administration Toolkit",
    add_completion=False,
)

console = Console()


# ============================================
# System Health Commands
# ============================================


@app.command("health")
def show_system_health() -> None:
    """
    Rendszer egészségi állapot megjelenítése.

    Show system health status including CPU, memory, disk, and load.
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Rendszer állapot lekérdezése...", total=None)
        health = system_health.get_system_health()

    # Fejléc
    console.print(
        Panel(
            f"[bold cyan]{health.hostname}[/bold cyan] - System Health Report",
            subtitle=f"Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        )
    )

    # CPU és Load táblázat
    cpu_table = Table(title="CPU & Load", show_header=True, header_style="bold magenta")
    cpu_table.add_column("Metric", style="cyan")
    cpu_table.add_column("Value", justify="right")

    cpu_color = "green" if health.cpu_percent < 70 else "yellow" if health.cpu_percent < 90 else "red"
    cpu_table.add_row("CPU Usage", f"[{cpu_color}]{health.cpu_percent:.1f}%[/{cpu_color}]")
    cpu_table.add_row("CPU Cores", str(health.cpu_count))
    if health.cpu_freq_mhz:
        cpu_table.add_row("CPU Frequency", f"{health.cpu_freq_mhz:.0f} MHz")
    cpu_table.add_row("Load Average (1m)", f"{health.load_avg_1m:.2f}")
    cpu_table.add_row("Load Average (5m)", f"{health.load_avg_5m:.2f}")
    cpu_table.add_row("Load Average (15m)", f"{health.load_avg_15m:.2f}")

    # Memória táblázat
    mem_table = Table(title="Memory", show_header=True, header_style="bold magenta")
    mem_table.add_column("Metric", style="cyan")
    mem_table.add_column("Value", justify="right")

    mem_color = "green" if health.memory_percent < 70 else "yellow" if health.memory_percent < 90 else "red"
    mem_table.add_row("Memory Usage", f"[{mem_color}]{health.memory_percent:.1f}%[/{mem_color}]")
    mem_table.add_row("Total", _format_bytes(health.memory_total_bytes))
    mem_table.add_row("Used", _format_bytes(health.memory_used_bytes))
    mem_table.add_row("Available", _format_bytes(health.memory_available_bytes))
    mem_table.add_row("Swap Usage", f"{health.swap_percent:.1f}%")
    mem_table.add_row("Swap Used", _format_bytes(health.swap_used_bytes))

    console.print(cpu_table)
    console.print(mem_table)

    # Disk táblázat
    if health.disk_partitions:
        disk_table = Table(title="Disk Partitions", show_header=True, header_style="bold magenta")
        disk_table.add_column("Mount Point", style="cyan")
        disk_table.add_column("Device")
        disk_table.add_column("Type")
        disk_table.add_column("Total", justify="right")
        disk_table.add_column("Used", justify="right")
        disk_table.add_column("Free", justify="right")
        disk_table.add_column("Usage", justify="right")

        for disk in health.disk_partitions:
            usage_color = "green" if disk.percent_used < 70 else "yellow" if disk.percent_used < 90 else "red"
            disk_table.add_row(
                disk.mountpoint,
                disk.device,
                disk.fstype,
                _format_bytes(disk.total_bytes),
                _format_bytes(disk.used_bytes),
                _format_bytes(disk.free_bytes),
                f"[{usage_color}]{disk.percent_used:.1f}%[/{usage_color}]",
            )

        console.print(disk_table)

    # Egyéb információk
    info_table = Table(title="System Info", show_header=True, header_style="bold magenta")
    info_table.add_column("Metric", style="cyan")
    info_table.add_column("Value", justify="right")

    info_table.add_row("Uptime", _format_uptime(health.uptime_seconds))
    info_table.add_row("Boot Time", health.boot_time.strftime("%Y-%m-%d %H:%M:%S"))
    info_table.add_row("Running Processes", str(health.process_count))
    info_table.add_row("Logged In Users", str(health.users_logged_in))

    console.print(info_table)


@app.command("processes")
def show_top_processes(
    count: int = typer.Option(10, "--count", "-n", help="Megjelenítendő folyamatok száma"),
    sort_by: str = typer.Option("cpu", "--sort", "-s", help="Rendezés: cpu vagy memory"),
) -> None:
    """
    Top folyamatok megjelenítése.

    Show top processes by CPU or memory usage.
    """
    processes = system_health.get_top_processes(count=count, sort_by=sort_by)

    table = Table(title=f"Top {count} Processes (sorted by {sort_by})", show_header=True)
    table.add_column("PID", style="cyan", justify="right")
    table.add_column("Name")
    table.add_column("User")
    table.add_column("Status")
    table.add_column("CPU %", justify="right")
    table.add_column("Memory %", justify="right")
    table.add_column("RSS", justify="right")

    for proc in processes:
        table.add_row(
            str(proc.pid),
            proc.name[:20],
            proc.username[:10],
            proc.status,
            f"{proc.cpu_percent:.1f}",
            f"{proc.memory_percent:.1f}",
            _format_bytes(proc.memory_rss_bytes),
        )

    console.print(table)


# ============================================
# Log Analysis Commands
# ============================================


@app.command("logs")
def analyze_log_file(
    path: Path = typer.Argument(..., help="Log fájl útvonala"),
    year: Optional[int] = typer.Option(None, "--year", "-y", help="Év a timestamp-ekhez"),
) -> None:
    """
    Log fájl elemzése.

    Analyze a log file and show statistics.
    """
    if not path.exists():
        console.print(f"[red]Error:[/red] File not found: {path}")
        raise typer.Exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Log fájl elemzése...", total=None)
        result = log_analyzer.analyze_logs(path, year=year)

    console.print(Panel(f"[bold]Log Analysis Report: {path}[/bold]"))

    # Összefoglaló
    summary_table = Table(title="Summary", show_header=True, header_style="bold magenta")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", justify="right")

    summary_table.add_row("Total Entries", str(result.total_entries))
    summary_table.add_row("[red]Errors[/red]", str(result.error_count))
    summary_table.add_row("[yellow]Warnings[/yellow]", str(result.warning_count))
    summary_table.add_row("[green]Successful Logins[/green]", str(result.successful_logins))
    summary_table.add_row("[red]Failed Logins[/red]", str(result.failed_logins))

    if result.time_range_start:
        summary_table.add_row("Time Range Start", result.time_range_start.strftime("%Y-%m-%d %H:%M:%S"))
    if result.time_range_end:
        summary_table.add_row("Time Range End", result.time_range_end.strftime("%Y-%m-%d %H:%M:%S"))

    console.print(summary_table)

    # Bejegyzések programonként
    if result.entries_by_program:
        program_table = Table(title="Entries by Program (Top 10)", show_header=True)
        program_table.add_column("Program", style="cyan")
        program_table.add_column("Count", justify="right")

        sorted_programs = sorted(
            result.entries_by_program.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        for program, count in sorted_programs:
            program_table.add_row(program, str(count))

        console.print(program_table)

    # Bejegyzések szintenként
    if result.entries_by_level:
        level_table = Table(title="Entries by Level", show_header=True)
        level_table.add_column("Level", style="cyan")
        level_table.add_column("Count", justify="right")

        for level, count in result.entries_by_level.items():
            color = "red" if level in ("error", "critical", "emergency") else "yellow" if level == "warning" else "white"
            level_table.add_row(f"[{color}]{level}[/{color}]", str(count))

        console.print(level_table)

    # Top hibaüzenetek
    if result.top_error_messages:
        console.print("\n[bold]Top Error Messages:[/bold]")
        for i, msg in enumerate(result.top_error_messages[:5], 1):
            console.print(f"  {i}. [red]{msg[:80]}[/red]")


# ============================================
# Disk Analysis Commands
# ============================================


@app.command("disk")
def show_disk_usage(
    path: Path = typer.Argument("/", help="Elemzendő útvonal"),
) -> None:
    """
    Lemezterület használat megjelenítése.

    Show disk usage for a path.
    """
    usage = disk_analyzer.get_filesystem_usage(str(path))

    console.print(Panel(f"[bold]Disk Usage: {usage.mountpoint}[/bold]"))

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    usage_color = "green" if usage.percent_used < 70 else "yellow" if usage.percent_used < 90 else "red"
    table.add_row("Device", usage.device)
    table.add_row("Filesystem Type", usage.fstype)
    table.add_row("Total", _format_bytes(usage.total_bytes))
    table.add_row("Used", _format_bytes(usage.used_bytes))
    table.add_row("Free", _format_bytes(usage.free_bytes))
    table.add_row("Usage", f"[{usage_color}]{usage.percent_used:.1f}%[/{usage_color}]")

    console.print(table)


@app.command("large-files")
def find_large_files_cmd(
    path: Path = typer.Argument(".", help="Keresési könyvtár"),
    min_size: int = typer.Option(100, "--min-size", "-s", help="Minimum méret MB-ban"),
    count: int = typer.Option(20, "--count", "-n", help="Maximum eredmények száma"),
) -> None:
    """
    Nagy fájlok keresése.

    Find large files in a directory.
    """
    min_size_bytes = min_size * 1024 * 1024

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Nagy fájlok keresése...", total=None)
        files = disk_analyzer.find_large_files(path, min_size_bytes=min_size_bytes, max_results=count)

    if not files:
        console.print(f"[yellow]No files found larger than {min_size} MB[/yellow]")
        return

    table = Table(title=f"Large Files (> {min_size} MB)", show_header=True)
    table.add_column("Size", justify="right", style="cyan")
    table.add_column("Modified")
    table.add_column("Owner")
    table.add_column("Path")

    for file in files:
        table.add_row(
            _format_bytes(file.size_bytes),
            file.modified_time.strftime("%Y-%m-%d %H:%M"),
            file.owner or "unknown",
            str(file.path)[:60],
        )

    console.print(table)


@app.command("dir-sizes")
def show_directory_sizes(
    path: Path = typer.Argument(".", help="Elemzendő könyvtár"),
) -> None:
    """
    Könyvtár méretek megjelenítése.

    Show directory sizes for immediate subdirectories.
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Könyvtár méretek számítása...", total=None)
        results = disk_analyzer.analyze_directory(path)

    if not results:
        console.print("[yellow]No directories found[/yellow]")
        return

    table = Table(title=f"Directory Sizes: {path}", show_header=True)
    table.add_column("Size", justify="right", style="cyan")
    table.add_column("Files", justify="right")
    table.add_column("Dirs", justify="right")
    table.add_column("Path")

    for item in results[:20]:
        table.add_row(
            _format_bytes(item.size_bytes),
            str(item.file_count),
            str(item.dir_count),
            str(item.path)[:50],
        )

    console.print(table)


# ============================================
# Service Management Commands
# ============================================


@app.command("services")
def list_services_cmd(
    state: Optional[str] = typer.Option(None, "--state", "-s", help="Szűrés állapot alapján (running, stopped, failed)"),
    enabled_only: bool = typer.Option(False, "--enabled", "-e", help="Csak enabled szolgáltatások"),
) -> None:
    """
    Szolgáltatások listázása.

    List system services with optional filtering.
    """
    filter_state = None
    if state:
        try:
            filter_state = ServiceState(state.lower())
        except ValueError:
            console.print(f"[red]Invalid state: {state}[/red]")
            raise typer.Exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Szolgáltatások lekérdezése...", total=None)
        services = service_manager.list_services(
            filter_state=filter_state,
            filter_enabled=True if enabled_only else None,
        )

    if not services:
        console.print("[yellow]No services found[/yellow]")
        return

    table = Table(title="System Services", show_header=True)
    table.add_column("Name", style="cyan")
    table.add_column("State")
    table.add_column("Enabled")
    table.add_column("PID", justify="right")
    table.add_column("Memory", justify="right")

    for svc in services[:50]:
        state_color = {
            ServiceState.RUNNING: "green",
            ServiceState.STOPPED: "white",
            ServiceState.FAILED: "red",
            ServiceState.INACTIVE: "yellow",
        }.get(svc.state, "white")

        table.add_row(
            svc.name[:30],
            f"[{state_color}]{svc.state.value}[/{state_color}]",
            "[green]yes[/green]" if svc.is_enabled else "[red]no[/red]",
            str(svc.pid) if svc.pid else "-",
            _format_bytes(svc.memory_bytes) if svc.memory_bytes else "-",
        )

    console.print(table)


@app.command("service")
def show_service_status(
    name: str = typer.Argument(..., help="Szolgáltatás neve"),
) -> None:
    """
    Szolgáltatás részletes státusza.

    Show detailed status of a specific service.
    """
    status = service_manager.get_service_status(name)

    state_color = {
        ServiceState.RUNNING: "green",
        ServiceState.STOPPED: "white",
        ServiceState.FAILED: "red",
        ServiceState.INACTIVE: "yellow",
    }.get(status.state, "white")

    console.print(Panel(f"[bold]Service: {status.name}[/bold]"))

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Property", style="cyan")
    table.add_column("Value")

    table.add_row("State", f"[{state_color}]{status.state.value}[/{state_color}]")
    table.add_row("Active", "[green]yes[/green]" if status.is_active else "[red]no[/red]")
    table.add_row("Enabled", "[green]yes[/green]" if status.is_enabled else "[red]no[/red]")
    if status.description:
        table.add_row("Description", status.description)
    if status.pid:
        table.add_row("PID", str(status.pid))
    if status.memory_bytes:
        table.add_row("Memory", _format_bytes(status.memory_bytes))
    if status.load_state:
        table.add_row("Load State", status.load_state)
    if status.sub_state:
        table.add_row("Sub State", status.sub_state)

    console.print(table)


@app.command("check-services")
def check_critical_services_cmd(
    services: Optional[list[str]] = typer.Argument(None, help="Ellenőrizendő szolgáltatások"),
) -> None:
    """
    Kritikus szolgáltatások ellenőrzése.

    Check status of critical services.
    """
    results = service_manager.check_critical_services(services)

    table = Table(title="Critical Services Check", show_header=True)
    table.add_column("Service", style="cyan")
    table.add_column("Status")
    table.add_column("Enabled")

    all_ok = True
    for name, status in results.items():
        if status.is_active:
            status_str = "[green]RUNNING[/green]"
        elif status.state == ServiceState.FAILED:
            status_str = "[red]FAILED[/red]"
            all_ok = False
        else:
            status_str = f"[yellow]{status.state.value.upper()}[/yellow]"
            all_ok = False

        table.add_row(
            name,
            status_str,
            "[green]yes[/green]" if status.is_enabled else "[yellow]no[/yellow]",
        )

    console.print(table)

    if all_ok:
        console.print("\n[green]All critical services are running![/green]")
    else:
        console.print("\n[red]Warning: Some services are not running![/red]")


# ============================================
# Helper Functions
# ============================================


def _format_bytes(size_bytes: int) -> str:
    """Bájtok formázása ember-olvasható formátumba."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def _format_uptime(seconds: float) -> str:
    """Uptime formázása ember-olvasható formátumba."""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)

    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes or not parts:
        parts.append(f"{minutes}m")

    return " ".join(parts)


def main() -> None:
    """CLI belépési pont."""
    app()


if __name__ == "__main__":
    main()
