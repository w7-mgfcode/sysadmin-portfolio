"""
Network Health Checker CLI.

Typer alapú parancssori interfész a hálózati diagnosztikai eszközökhöz.

Használat:
    $ python -m network_health_checker ping 8.8.8.8
    $ python -m network_health_checker scan 192.168.1.1 --ports 22,80,443
    $ python -m network_health_checker dns google.com --type MX
"""

import asyncio
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .models import HostStatus
from .network_tools import (
    calculate_subnet,
    get_active_connections,
    get_local_interfaces,
    get_mx_records,
    get_nameservers,
    is_host_reachable,
    is_private_ip,
    is_valid_ip,
    lookup_all_records,
    lookup_dns,
    ping_host,
    reverse_lookup,
    scan_common_ports,
    scan_ports,
    split_subnet,
)
from .network_tools.snmp_query import get_interfaces, get_system_info

# Typer app létrehozása
app = typer.Typer(
    name="netcheck",
    help="Network Health Checker - Hálózati diagnosztikai eszközök.",
    add_completion=False,
)

# Rich console a formázott kimenethez
console = Console()


# =============================================================================
# PING PARANCSOK
# =============================================================================


@app.command()
def ping(
    host: str = typer.Argument(..., help="Pingelendő host (IP vagy hostname)"),
    count: int = typer.Option(3, "--count", "-c", help="Ping-ek száma"),
    timeout: float = typer.Option(2.0, "--timeout", "-t", help="Timeout másodpercben"),
):
    """
    Host pingelése és válaszidő mérése.

    Példa:
        netcheck ping 8.8.8.8
        netcheck ping google.com -c 5 -t 1
    """
    console.print(f"\n[bold]Pinging {host}...[/bold]\n")

    result = ping_host(host, timeout=timeout, count=count)

    if result.status == HostStatus.UP:
        console.print(
            Panel(
                f"[green]✓ Host is UP[/green]\n\n"
                f"Host: {result.host}\n"
                f"IP: {result.ip_address or 'N/A'}\n"
                f"Latency: [cyan]{result.latency_ms}ms[/cyan]\n"
                f"Packets: {count}",
                title="Ping Result",
                border_style="green",
            )
        )
    elif result.status == HostStatus.TIMEOUT:
        console.print(
            Panel(
                f"[yellow]⚠ Host timed out[/yellow]\n\n"
                f"Host: {result.host}\n"
                f"IP: {result.ip_address or 'N/A'}",
                title="Ping Result",
                border_style="yellow",
            )
        )
    else:
        console.print(
            Panel(
                f"[red]✗ Error[/red]\n\n"
                f"Host: {result.host}\n"
                f"Error: {result.error_message or 'Unknown error'}",
                title="Ping Result",
                border_style="red",
            )
        )


@app.command()
def check(
    hosts: List[str] = typer.Argument(..., help="Ellenőrizendő hostok (szóközzel elválasztva)"),
    timeout: float = typer.Option(2.0, "--timeout", "-t", help="Timeout másodpercben"),
):
    """
    Több host gyors elérhetőség ellenőrzése.

    Példa:
        netcheck check 8.8.8.8 1.1.1.1 google.com
    """
    console.print(f"\n[bold]Checking {len(hosts)} hosts...[/bold]\n")

    table = Table(title="Host Availability")
    table.add_column("Host", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Latency", justify="right")

    for host in hosts:
        result = ping_host(host, timeout=timeout, count=1)
        if result.status == HostStatus.UP:
            status = "[green]UP[/green]"
            latency = f"{result.latency_ms}ms"
        elif result.status == HostStatus.TIMEOUT:
            status = "[yellow]TIMEOUT[/yellow]"
            latency = "-"
        else:
            status = "[red]ERROR[/red]"
            latency = "-"
        table.add_row(host, status, latency)

    console.print(table)


# =============================================================================
# PORT SCANNER PARANCSOK
# =============================================================================


@app.command()
def scan(
    host: str = typer.Argument(..., help="Szkennelendő host"),
    ports: str = typer.Option("22,80,443,8080", "--ports", "-p", help="Portok (pl. '22,80' vagy '20-25,80,443')"),
    timeout: float = typer.Option(1.0, "--timeout", "-t", help="Timeout portonként"),
    banner: bool = typer.Option(False, "--banner", "-b", help="Banner információ lekérése"),
):
    """
    TCP portok szkennelése.

    Példa:
        netcheck scan 192.168.1.1 -p "22,80,443"
        netcheck scan example.com -p "1-1024" --banner
    """
    console.print(f"\n[bold]Scanning {host}...[/bold]\n")

    results = scan_ports(host, ports, timeout=timeout, grab_banner=banner)

    table = Table(title=f"Port Scan Results: {host}")
    table.add_column("Port", style="cyan", justify="right")
    table.add_column("Status", justify="center")
    table.add_column("Service", style="dim")
    table.add_column("Latency", justify="right")
    if banner:
        table.add_column("Banner")

    open_count = 0
    for result in results:
        if result.is_open:
            open_count += 1
            status = "[green]OPEN[/green]"
            latency = f"{result.latency_ms}ms" if result.latency_ms else "-"
        else:
            status = "[red]CLOSED[/red]"
            latency = "-"

        row = [
            str(result.port),
            status,
            result.service_name or "-",
            latency,
        ]
        if banner:
            row.append(result.banner[:50] if result.banner else "-")

        table.add_row(*row)

    console.print(table)
    console.print(f"\n[bold]Summary:[/bold] {open_count} open, {len(results) - open_count} closed")


@app.command("scan-common")
def scan_common(
    host: str = typer.Argument(..., help="Szkennelendő host"),
    timeout: float = typer.Option(1.0, "--timeout", "-t", help="Timeout portonként"),
):
    """
    Gyakori szolgáltatás portok szkennelése.

    Példa:
        netcheck scan-common 192.168.1.1
    """
    console.print(f"\n[bold]Scanning common ports on {host}...[/bold]\n")

    results = scan_common_ports(host, timeout=timeout)

    table = Table(title=f"Common Port Scan: {host}")
    table.add_column("Port", style="cyan", justify="right")
    table.add_column("Service")
    table.add_column("Status", justify="center")
    table.add_column("Latency", justify="right")

    open_ports = []
    for result in results:
        if result.is_open:
            open_ports.append(result)
            status = "[green]OPEN[/green]"
            latency = f"{result.latency_ms}ms" if result.latency_ms else "-"
            table.add_row(
                str(result.port),
                result.service_name or "-",
                status,
                latency,
            )

    if open_ports:
        console.print(table)
    else:
        console.print("[yellow]No open ports found[/yellow]")

    console.print(f"\n[bold]Summary:[/bold] {len(open_ports)} open ports found")


# =============================================================================
# DNS PARANCSOK
# =============================================================================


@app.command()
def dns(
    domain: str = typer.Argument(..., help="Lekérdezendő domain"),
    record_type: str = typer.Option("A", "--type", "-t", help="Rekord típus (A, AAAA, MX, TXT, CNAME, NS, SOA)"),
    nameserver: Optional[str] = typer.Option(None, "--ns", help="Egyedi DNS szerver"),
):
    """
    DNS rekord lekérdezése.

    Példa:
        netcheck dns google.com
        netcheck dns google.com -t MX
        netcheck dns example.com -t NS --ns 8.8.8.8
    """
    console.print(f"\n[bold]DNS lookup: {domain} ({record_type})[/bold]\n")

    try:
        result = lookup_dns(domain, record_type, nameserver=nameserver)

        if result.values:
            table = Table(title=f"DNS {record_type} Records")
            table.add_column("Value", style="cyan")
            table.add_column("TTL", justify="right", style="dim")

            for value in result.values:
                table.add_row(value, str(result.ttl) if result.ttl else "-")

            console.print(table)
        else:
            console.print(f"[yellow]No {record_type} records found for {domain}[/yellow]")

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")


@app.command("dns-all")
def dns_all(
    domain: str = typer.Argument(..., help="Lekérdezendő domain"),
):
    """
    Összes DNS rekord típus lekérdezése.

    Példa:
        netcheck dns-all google.com
    """
    console.print(f"\n[bold]Full DNS lookup: {domain}[/bold]\n")

    results = lookup_all_records(domain)

    if results:
        for result in results:
            table = Table(title=f"{result.record_type} Records")
            table.add_column("Value", style="cyan")
            table.add_column("TTL", justify="right", style="dim")

            for value in result.values:
                table.add_row(value, str(result.ttl) if result.ttl else "-")

            console.print(table)
            console.print()
    else:
        console.print(f"[yellow]No DNS records found for {domain}[/yellow]")


@app.command("reverse-dns")
def reverse_dns(
    ip: str = typer.Argument(..., help="IP cím a reverse lookup-hoz"),
):
    """
    Reverse DNS lookup (IP -> hostname).

    Példa:
        netcheck reverse-dns 8.8.8.8
    """
    console.print(f"\n[bold]Reverse DNS lookup: {ip}[/bold]\n")

    result = reverse_lookup(ip)

    if result.values:
        console.print(f"[green]Hostname: {result.values[0]}[/green]")
    else:
        console.print(f"[yellow]No PTR record found for {ip}[/yellow]")


@app.command("mx")
def mx_records(
    domain: str = typer.Argument(..., help="Domain a mail szerverek lekérdezéséhez"),
):
    """
    Mail szerverek (MX rekordok) lekérdezése.

    Példa:
        netcheck mx gmail.com
    """
    console.print(f"\n[bold]Mail servers for {domain}[/bold]\n")

    records = get_mx_records(domain)

    if records:
        table = Table(title="MX Records")
        table.add_column("Priority", justify="right", style="cyan")
        table.add_column("Mail Server")

        for record in records:
            parts = record.split(" ", 1)
            if len(parts) == 2:
                table.add_row(parts[0], parts[1])
            else:
                table.add_row("-", record)

        console.print(table)
    else:
        console.print(f"[yellow]No MX records found for {domain}[/yellow]")


@app.command("ns")
def ns_records(
    domain: str = typer.Argument(..., help="Domain a nameserverek lekérdezéséhez"),
):
    """
    Authoritative nameserverek lekérdezése.

    Példa:
        netcheck ns google.com
    """
    console.print(f"\n[bold]Nameservers for {domain}[/bold]\n")

    records = get_nameservers(domain)

    if records:
        for ns in records:
            console.print(f"  • {ns}")
    else:
        console.print(f"[yellow]No NS records found for {domain}[/yellow]")


# =============================================================================
# SUBNET CALCULATOR PARANCSOK
# =============================================================================


@app.command()
def subnet(
    cidr: str = typer.Argument(..., help="CIDR notation (pl. 192.168.1.0/24)"),
):
    """
    Alhálózat információk kiszámítása.

    Példa:
        netcheck subnet 192.168.1.0/24
        netcheck subnet 10.0.0.0/8
    """
    console.print(f"\n[bold]Subnet Calculator: {cidr}[/bold]\n")

    try:
        info = calculate_subnet(cidr)

        table = Table(title="Subnet Information", show_header=False)
        table.add_column("Property", style="cyan")
        table.add_column("Value")

        table.add_row("Network", info.network)
        table.add_row("Netmask", info.netmask)
        table.add_row("CIDR", f"/{info.cidr}")
        table.add_row("Broadcast", info.broadcast)
        table.add_row("First Host", info.first_host)
        table.add_row("Last Host", info.last_host)
        table.add_row("Total Hosts", str(info.total_hosts))

        console.print(table)

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")


@app.command("subnet-split")
def subnet_split(
    cidr: str = typer.Argument(..., help="Felosztandó alhálózat CIDR-ben"),
    new_prefix: int = typer.Argument(..., help="Új prefix hossz"),
):
    """
    Alhálózat felosztása kisebb alhálózatokra.

    Példa:
        netcheck subnet-split 192.168.0.0/24 26
    """
    console.print(f"\n[bold]Splitting {cidr} to /{new_prefix}[/bold]\n")

    try:
        subnets = split_subnet(cidr, new_prefix)

        table = Table(title=f"Subnet Split: {cidr} -> /{new_prefix}")
        table.add_column("#", justify="right", style="dim")
        table.add_column("Network", style="cyan")
        table.add_column("Range")
        table.add_column("Hosts", justify="right")

        for i, s in enumerate(subnets, 1):
            table.add_row(
                str(i),
                f"{s.network}/{s.cidr}",
                f"{s.first_host} - {s.last_host}",
                str(s.total_hosts),
            )

        console.print(table)
        console.print(f"\n[bold]Total subnets:[/bold] {len(subnets)}")

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")


@app.command("ip-info")
def ip_info(
    ip: str = typer.Argument(..., help="IP cím az elemzéshez"),
):
    """
    IP cím információk megjelenítése.

    Példa:
        netcheck ip-info 192.168.1.100
    """
    console.print(f"\n[bold]IP Information: {ip}[/bold]\n")

    if not is_valid_ip(ip):
        console.print(f"[red]Invalid IP address: {ip}[/red]")
        return

    is_private = is_private_ip(ip)

    table = Table(show_header=False)
    table.add_column("Property", style="cyan")
    table.add_column("Value")

    table.add_row("IP Address", ip)
    table.add_row("Type", "[yellow]Private[/yellow]" if is_private else "[blue]Public[/blue]")
    table.add_row("Valid IPv4", "[green]Yes[/green]")

    console.print(table)


# =============================================================================
# LOCAL NETWORK PARANCSOK
# =============================================================================


@app.command("interfaces")
def list_interfaces(
    all_interfaces: bool = typer.Option(False, "--all", "-a", help="Loopback is megjelenítése"),
):
    """
    Helyi hálózati interfészek listázása.

    Példa:
        netcheck interfaces
        netcheck interfaces --all
    """
    console.print("\n[bold]Local Network Interfaces[/bold]\n")

    interfaces = get_local_interfaces(include_loopback=all_interfaces)

    table = Table(title="Network Interfaces")
    table.add_column("Name", style="cyan")
    table.add_column("IPv4 Address")
    table.add_column("Netmask")
    table.add_column("MAC Address", style="dim")
    table.add_column("Status", justify="center")
    table.add_column("Speed")

    for iface in interfaces:
        status = "[green]UP[/green]" if iface.is_up else "[red]DOWN[/red]"
        speed = f"{iface.speed_mbps} Mbps" if iface.speed_mbps else "-"

        table.add_row(
            iface.name,
            iface.ipv4_address or "-",
            iface.ipv4_netmask or "-",
            iface.mac_address or "-",
            status,
            speed,
        )

    console.print(table)


@app.command("connections")
def list_connections(
    kind: str = typer.Option("tcp", "--kind", "-k", help="Típus: tcp, udp, inet, all"),
    listening: bool = typer.Option(False, "--listening", "-l", help="Csak LISTEN portok"),
):
    """
    Aktív hálózati kapcsolatok listázása.

    Példa:
        netcheck connections
        netcheck connections -l
        netcheck connections -k udp
    """
    console.print("\n[bold]Active Network Connections[/bold]\n")

    if listening:
        connections = [c for c in get_active_connections(kind) if c.status == "LISTEN"]
    else:
        connections = get_active_connections(kind, include_listening=True)

    if not connections:
        console.print("[yellow]No connections found[/yellow]")
        return

    table = Table(title="Connections")
    table.add_column("Proto", style="cyan")
    table.add_column("Local Address")
    table.add_column("Remote Address")
    table.add_column("Status")
    table.add_column("Process", style="dim")

    for conn in connections[:50]:  # Limit megjelenítés
        local = f"{conn.local_address}:{conn.local_port}" if conn.local_address else "-"
        remote = f"{conn.remote_address}:{conn.remote_port}" if conn.remote_address else "-"

        status_color = "green" if conn.status == "ESTABLISHED" else "yellow" if conn.status == "LISTEN" else "white"

        table.add_row(
            conn.protocol.upper(),
            local,
            remote,
            f"[{status_color}]{conn.status}[/{status_color}]",
            conn.process_name or "-",
        )

    console.print(table)

    if len(connections) > 50:
        console.print(f"\n[dim]Showing 50 of {len(connections)} connections[/dim]")


# =============================================================================
# SNMP PARANCSOK
# =============================================================================


@app.command("snmp-info")
def snmp_info(
    host: str = typer.Argument(..., help="SNMP eszköz IP címe"),
    community: str = typer.Option("public", "--community", "-c", help="SNMP community string"),
):
    """
    SNMP eszköz információk lekérdezése.

    Példa:
        netcheck snmp-info 192.168.1.1
        netcheck snmp-info 192.168.1.1 -c private
    """
    console.print(f"\n[bold]SNMP System Info: {host}[/bold]\n")

    # Async függvény futtatása
    device = asyncio.run(get_system_info(host, community))

    if device:
        table = Table(title="Device Information", show_header=False)
        table.add_column("Property", style="cyan")
        table.add_column("Value")

        table.add_row("Host", device.host)
        table.add_row("System Name", device.sys_name or "-")
        table.add_row("Description", device.sys_descr or "-")
        table.add_row("Location", device.sys_location or "-")
        table.add_row("Contact", device.sys_contact or "-")

        if device.uptime_seconds:
            days, remainder = divmod(device.uptime_seconds, 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, seconds = divmod(remainder, 60)
            uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
            table.add_row("Uptime", uptime_str)

        console.print(table)
    else:
        console.print(f"[red]Could not connect to {host} via SNMP[/red]")


@app.command("snmp-interfaces")
def snmp_interfaces(
    host: str = typer.Argument(..., help="SNMP eszköz IP címe"),
    community: str = typer.Option("public", "--community", "-c", help="SNMP community string"),
):
    """
    SNMP eszköz interfészeinek listázása.

    Példa:
        netcheck snmp-interfaces 192.168.1.1
    """
    console.print(f"\n[bold]SNMP Interfaces: {host}[/bold]\n")

    # Async függvény futtatása
    interfaces = asyncio.run(get_interfaces(host, community))

    if interfaces:
        table = Table(title="Network Interfaces")
        table.add_column("Index", justify="right", style="dim")
        table.add_column("Name", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Speed")
        table.add_column("In", justify="right")
        table.add_column("Out", justify="right")

        for iface in interfaces:
            status = "[green]UP[/green]" if iface.oper_status == "up" else "[red]DOWN[/red]"
            speed = f"{iface.speed // 1000000} Mbps" if iface.speed else "-"

            # Byte to human readable
            in_bytes = _format_bytes(iface.in_octets) if iface.in_octets else "-"
            out_bytes = _format_bytes(iface.out_octets) if iface.out_octets else "-"

            table.add_row(
                str(iface.index),
                iface.name or "-",
                status,
                speed,
                in_bytes,
                out_bytes,
            )

        console.print(table)
    else:
        console.print(f"[red]Could not get interfaces from {host}[/red]")


def _format_bytes(num_bytes: int) -> str:
    """Byte szám formázása olvasható formára."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"


# =============================================================================
# MAIN
# =============================================================================


def main():
    """CLI belépési pont."""
    app()


if __name__ == "__main__":
    main()
