#!/bin/bash
# =============================================================================
# Log Cleanup Script / Log Tisztító Script
# =============================================================================
# Cleans up old log files based on retention policy.
#
# Régi log fájlok tisztítása megőrzési szabályok alapján.
#
# Usage / Használat:
#   ./log-cleanup.sh [--dry-run] [--days N] [--size M]
#
# Options / Opciók:
#   --dry-run    Preview changes without deleting / Előnézet törlés nélkül
#   --days N     Delete files older than N days / N napnál régebbi fájlok törlése
#   --size M     Delete files larger than M MB / M MB-nál nagyobb fájlok törlése
#
# Example / Példa:
#   ./log-cleanup.sh --dry-run --days 30
#   ./log-cleanup.sh --days 7 --size 100
# =============================================================================

set -euo pipefail

# Configuration / Konfiguráció
LOG_DIRS=("/var/log" "/var/log/journal" "/var/log/nginx" "/var/log/apache2")
DEFAULT_DAYS=30
DEFAULT_SIZE_MB=500
DRY_RUN=false
DAYS=$DEFAULT_DAYS
SIZE_MB=$DEFAULT_SIZE_MB

# Colors / Színek
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Parse arguments / Argumentumok feldolgozása
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --days)
            DAYS="$2"
            shift 2
            ;;
        --size)
            SIZE_MB="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [--dry-run] [--days N] [--size M]"
            echo ""
            echo "Options:"
            echo "  --dry-run    Preview changes without deleting"
            echo "  --days N     Delete files older than N days (default: $DEFAULT_DAYS)"
            echo "  --size M     Delete files larger than M MB (default: $DEFAULT_SIZE_MB)"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Counters / Számlálók
TOTAL_FILES=0
TOTAL_SIZE=0
DELETED_FILES=0
DELETED_SIZE=0

# Print header / Fejléc nyomtatása
echo "=============================================="
echo " LOG CLEANUP SCRIPT / LOG TISZTÍTÓ SCRIPT"
echo "=============================================="
echo ""
echo "Settings / Beállítások:"
echo "  - Days threshold: $DAYS days"
echo "  - Size threshold: $SIZE_MB MB"
echo "  - Dry run mode: $DRY_RUN"
echo ""

# Function to format size / Méret formázó függvény
format_size() {
    local size=$1
    if [ "$size" -ge 1073741824 ]; then
        echo "$(echo "scale=2; $size / 1073741824" | bc) GB"
    elif [ "$size" -ge 1048576 ]; then
        echo "$(echo "scale=2; $size / 1048576" | bc) MB"
    elif [ "$size" -ge 1024 ]; then
        echo "$(echo "scale=2; $size / 1024" | bc) KB"
    else
        echo "$size B"
    fi
}

# Function to clean old files / Régi fájlok tisztító függvény
clean_old_files() {
    local dir=$1
    local days=$2

    echo -e "${BLUE}Scanning for files older than $days days in: $dir${NC}"

    if [ ! -d "$dir" ]; then
        echo -e "${YELLOW}  Directory does not exist, skipping...${NC}"
        return
    fi

    # Find old files / Régi fájlok keresése
    while IFS= read -r -d '' file; do
        local size
        size=$(stat -c%s "$file" 2>/dev/null || echo 0)
        TOTAL_FILES=$((TOTAL_FILES + 1))
        TOTAL_SIZE=$((TOTAL_SIZE + size))

        if [ "$DRY_RUN" = true ]; then
            echo -e "  ${YELLOW}[DRY RUN]${NC} Would delete: $file ($(format_size $size))"
        else
            rm -f "$file" && echo -e "  ${GREEN}Deleted:${NC} $file ($(format_size $size))"
        fi

        DELETED_FILES=$((DELETED_FILES + 1))
        DELETED_SIZE=$((DELETED_SIZE + size))
    done < <(find "$dir" -type f -name "*.log*" -mtime +"$days" -print0 2>/dev/null)

    # Also find old .gz files / Régi .gz fájlok keresése
    while IFS= read -r -d '' file; do
        local size
        size=$(stat -c%s "$file" 2>/dev/null || echo 0)
        TOTAL_FILES=$((TOTAL_FILES + 1))
        TOTAL_SIZE=$((TOTAL_SIZE + size))

        if [ "$DRY_RUN" = true ]; then
            echo -e "  ${YELLOW}[DRY RUN]${NC} Would delete: $file ($(format_size $size))"
        else
            rm -f "$file" && echo -e "  ${GREEN}Deleted:${NC} $file ($(format_size $size))"
        fi

        DELETED_FILES=$((DELETED_FILES + 1))
        DELETED_SIZE=$((DELETED_SIZE + size))
    done < <(find "$dir" -type f -name "*.gz" -mtime +"$days" -print0 2>/dev/null)
}

# Function to clean large files / Nagy fájlok tisztító függvény
clean_large_files() {
    local dir=$1
    local size_mb=$2
    local size_bytes=$((size_mb * 1024 * 1024))

    echo -e "${BLUE}Scanning for files larger than ${size_mb}MB in: $dir${NC}"

    if [ ! -d "$dir" ]; then
        echo -e "${YELLOW}  Directory does not exist, skipping...${NC}"
        return
    fi

    while IFS= read -r -d '' file; do
        local size
        size=$(stat -c%s "$file" 2>/dev/null || echo 0)

        if [ "$size" -ge "$size_bytes" ]; then
            TOTAL_FILES=$((TOTAL_FILES + 1))
            TOTAL_SIZE=$((TOTAL_SIZE + size))

            if [ "$DRY_RUN" = true ]; then
                echo -e "  ${YELLOW}[DRY RUN]${NC} Would truncate: $file ($(format_size $size))"
            else
                # Truncate instead of delete for active logs
                # Csonkítás törlés helyett aktív logokhoz
                if [[ "$file" == *.log ]]; then
                    truncate -s 0 "$file" && echo -e "  ${GREEN}Truncated:${NC} $file ($(format_size $size))"
                else
                    rm -f "$file" && echo -e "  ${GREEN}Deleted:${NC} $file ($(format_size $size))"
                fi
            fi

            DELETED_FILES=$((DELETED_FILES + 1))
            DELETED_SIZE=$((DELETED_SIZE + size))
        fi
    done < <(find "$dir" -type f \( -name "*.log*" -o -name "*.gz" \) -print0 2>/dev/null)
}

# Clean journal logs / Journal logok tisztítása
clean_journal_logs() {
    echo -e "${BLUE}Cleaning systemd journal logs...${NC}"

    if command -v journalctl &> /dev/null; then
        local journal_size
        journal_size=$(journalctl --disk-usage 2>/dev/null | grep -oP '\d+\.?\d*[KMG]' || echo "unknown")
        echo "  Current journal size: $journal_size"

        if [ "$DRY_RUN" = true ]; then
            echo -e "  ${YELLOW}[DRY RUN]${NC} Would vacuum journal to keep only $DAYS days"
        else
            journalctl --vacuum-time="${DAYS}d" 2>/dev/null && echo -e "  ${GREEN}Journal cleaned${NC}"
        fi
    else
        echo -e "  ${YELLOW}journalctl not available, skipping...${NC}"
    fi
}

# Main execution / Fő végrehajtás
echo "Starting cleanup / Tisztítás indítása..."
echo ""

# Clean old files in each directory / Régi fájlok tisztítása minden könyvtárban
for dir in "${LOG_DIRS[@]}"; do
    clean_old_files "$dir" "$DAYS"
    clean_large_files "$dir" "$SIZE_MB"
    echo ""
done

# Clean journal logs / Journal logok tisztítása
clean_journal_logs

# Summary / Összefoglaló
echo ""
echo "=============================================="
echo " SUMMARY / ÖSSZEFOGLALÓ"
echo "=============================================="
echo "  Files processed: $TOTAL_FILES"
echo "  Total size found: $(format_size $TOTAL_SIZE)"
echo "  Files cleaned: $DELETED_FILES"
echo "  Space freed: $(format_size $DELETED_SIZE)"

if [ "$DRY_RUN" = true ]; then
    echo ""
    echo -e "${YELLOW}This was a dry run. No files were actually deleted.${NC}"
    echo -e "${YELLOW}Run without --dry-run to perform actual cleanup.${NC}"
fi

echo ""
echo "Done! / Kész!"
