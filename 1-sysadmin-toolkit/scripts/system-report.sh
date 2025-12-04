#!/bin/bash
# =============================================================================
# System Report Generator / Rendszer Riport Generátor
# =============================================================================
# Generates a comprehensive system report with hardware, software, and
# performance information.
#
# Átfogó rendszer riportot generál hardver, szoftver és teljesítmény
# információkkal.
#
# Usage / Használat:
#   ./system-report.sh [output_file]
#
# Example / Példa:
#   ./system-report.sh /tmp/system-report.txt
# =============================================================================

set -euo pipefail

# Colors / Színek
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Output file / Kimeneti fájl
OUTPUT_FILE="${1:-/dev/stdout}"

# Print header / Fejléc nyomtatása
print_header() {
    echo "=============================================="
    echo " SYSTEM REPORT / RENDSZER RIPORT"
    echo " Generated: $(date '+%Y-%m-%d %H:%M:%S')"
    echo " Hostname: $(hostname)"
    echo "=============================================="
    echo ""
}

# Print section / Szekció nyomtatása
print_section() {
    echo ""
    echo "----------------------------------------------"
    echo " $1"
    echo "----------------------------------------------"
}

# System information / Rendszer információ
system_info() {
    print_section "SYSTEM INFORMATION / RENDSZER INFORMÁCIÓ"

    echo "Hostname: $(hostname)"
    echo "Kernel: $(uname -r)"
    echo "OS: $(cat /etc/os-release 2>/dev/null | grep "PRETTY_NAME" | cut -d'"' -f2 || echo "Unknown")"
    echo "Architecture: $(uname -m)"
    echo "Uptime: $(uptime -p 2>/dev/null || uptime)"
    echo "Boot Time: $(who -b 2>/dev/null | awk '{print $3, $4}' || echo "Unknown")"
}

# CPU information / CPU információ
cpu_info() {
    print_section "CPU INFORMATION / CPU INFORMÁCIÓ"

    echo "CPU Model: $(grep "model name" /proc/cpuinfo 2>/dev/null | head -1 | cut -d':' -f2 | xargs || echo "Unknown")"
    echo "CPU Cores: $(nproc 2>/dev/null || echo "Unknown")"
    echo "CPU MHz: $(grep "cpu MHz" /proc/cpuinfo 2>/dev/null | head -1 | cut -d':' -f2 | xargs || echo "Unknown")"

    if command -v lscpu &> /dev/null; then
        echo ""
        echo "CPU Details:"
        lscpu | grep -E "^(Thread|Core|Socket|CPU\(s\)|Vendor|Model name)" | sed 's/^/  /'
    fi

    echo ""
    echo "Load Average: $(cat /proc/loadavg 2>/dev/null | awk '{print $1, $2, $3}' || echo "Unknown")"
}

# Memory information / Memória információ
memory_info() {
    print_section "MEMORY INFORMATION / MEMÓRIA INFORMÁCIÓ"

    if command -v free &> /dev/null; then
        free -h
    else
        cat /proc/meminfo | head -10
    fi
}

# Disk information / Lemez információ
disk_info() {
    print_section "DISK INFORMATION / LEMEZ INFORMÁCIÓ"

    echo "Filesystem Usage / Fájlrendszer használat:"
    df -h --output=source,size,used,avail,pcent,target 2>/dev/null | grep -v "tmpfs\|loop" || df -h

    echo ""
    echo "Block Devices / Blokk eszközök:"
    lsblk -o NAME,SIZE,TYPE,MOUNTPOINT 2>/dev/null || echo "lsblk not available"
}

# Network information / Hálózati információ
network_info() {
    print_section "NETWORK INFORMATION / HÁLÓZATI INFORMÁCIÓ"

    echo "IP Addresses / IP címek:"
    ip -4 addr show 2>/dev/null | grep inet | awk '{print "  " $2, $NF}' || hostname -I

    echo ""
    echo "Default Gateway / Alapértelmezett átjáró:"
    ip route show default 2>/dev/null | awk '{print "  " $3}' || echo "  Unknown"

    echo ""
    echo "DNS Servers / DNS szerverek:"
    grep "nameserver" /etc/resolv.conf 2>/dev/null | awk '{print "  " $2}' || echo "  Unknown"

    echo ""
    echo "Network Interfaces / Hálózati interfészek:"
    ip link show 2>/dev/null | grep -E "^[0-9]" | awk '{print "  " $2}' | sed 's/:$//' || ls /sys/class/net
}

# Services status / Szolgáltatások állapota
services_status() {
    print_section "KEY SERVICES STATUS / KULCS SZOLGÁLTATÁSOK ÁLLAPOTA"

    if command -v systemctl &> /dev/null; then
        echo "Running Services / Futó szolgáltatások: $(systemctl list-units --type=service --state=running --no-legend 2>/dev/null | wc -l)"
        echo "Failed Services / Hibás szolgáltatások: $(systemctl list-units --type=service --state=failed --no-legend 2>/dev/null | wc -l)"

        echo ""
        echo "Failed Services List / Hibás szolgáltatások listája:"
        systemctl list-units --type=service --state=failed --no-legend 2>/dev/null | awk '{print "  " $1, $4}' || echo "  None"
    else
        echo "systemctl not available"
    fi
}

# Top processes / Top folyamatok
top_processes() {
    print_section "TOP PROCESSES / TOP FOLYAMATOK"

    echo "Top 10 by CPU / Top 10 CPU szerint:"
    ps aux --sort=-%cpu 2>/dev/null | head -11 | awk '{print $1, $2, $3 "%", $11}' | column -t || echo "ps not available"

    echo ""
    echo "Top 10 by Memory / Top 10 memória szerint:"
    ps aux --sort=-%mem 2>/dev/null | head -11 | awk '{print $1, $2, $4 "%", $11}' | column -t || echo "ps not available"
}

# Security information / Biztonsági információ
security_info() {
    print_section "SECURITY INFORMATION / BIZTONSÁGI INFORMÁCIÓ"

    echo "Logged in Users / Bejelentkezett felhasználók:"
    who 2>/dev/null || echo "  None"

    echo ""
    echo "Last 5 Logins / Utolsó 5 bejelentkezés:"
    last -5 2>/dev/null || echo "  Unknown"

    echo ""
    echo "Failed Login Attempts (last 10) / Sikertelen bejelentkezések (utolsó 10):"
    lastb -10 2>/dev/null || echo "  Requires root access"
}

# Docker status / Docker állapot
docker_status() {
    print_section "DOCKER STATUS / DOCKER ÁLLAPOT"

    if command -v docker &> /dev/null; then
        echo "Docker Version / Docker verzió:"
        docker --version 2>/dev/null || echo "  Unknown"

        echo ""
        echo "Running Containers / Futó konténerek:"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}" 2>/dev/null || echo "  Cannot access docker"

        echo ""
        echo "Docker Disk Usage / Docker lemezhasználat:"
        docker system df 2>/dev/null || echo "  Cannot access docker"
    else
        echo "Docker not installed"
    fi
}

# Main function / Fő függvény
main() {
    {
        print_header
        system_info
        cpu_info
        memory_info
        disk_info
        network_info
        services_status
        top_processes
        docker_status
        security_info

        echo ""
        echo "=============================================="
        echo " END OF REPORT / RIPORT VÉGE"
        echo "=============================================="
    } > "$OUTPUT_FILE"

    if [ "$OUTPUT_FILE" != "/dev/stdout" ]; then
        echo -e "${GREEN}Report saved to: $OUTPUT_FILE${NC}"
    fi
}

main
