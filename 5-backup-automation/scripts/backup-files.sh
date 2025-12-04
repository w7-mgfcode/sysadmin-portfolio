#!/bin/bash
# =============================================================================
# File Backup Script / Fájl Mentés Script
# =============================================================================
# Creates compressed tar backups of specified directories.
#
# Megadott könyvtárak tömörített tar mentését készíti.
#
# Usage / Használat:
#   ./backup-files.sh <source_dir> <backup_dir> [name]
#
# Example / Példa:
#   ./backup-files.sh /home/user /backups home-backup
# =============================================================================

set -euo pipefail

# Colors / Színek
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Parameters / Paraméterek
SOURCE_DIR="${1:-}"
BACKUP_DIR="${2:-}"
BACKUP_NAME="${3:-backup}"

# Validation / Validálás
if [ -z "$SOURCE_DIR" ] || [ -z "$BACKUP_DIR" ]; then
    echo -e "${RED}Usage: $0 <source_dir> <backup_dir> [name]${NC}"
    exit 1
fi

if [ ! -d "$SOURCE_DIR" ]; then
    echo -e "${RED}Error: Source directory does not exist: $SOURCE_DIR${NC}"
    exit 1
fi

# Create backup directory / Backup könyvtár létrehozása
mkdir -p "$BACKUP_DIR"

# Generate filename / Fájlnév generálása
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
HOSTNAME=$(hostname -s)
BACKUP_FILE="${BACKUP_DIR}/${BACKUP_NAME}_${HOSTNAME}_${TIMESTAMP}.tar.gz"

echo -e "${GREEN}Starting backup...${NC}"
echo "Source: $SOURCE_DIR"
echo "Destination: $BACKUP_FILE"

# Create backup / Mentés létrehozása
tar -czf "$BACKUP_FILE" \
    --exclude='*.tmp' \
    --exclude='*.log' \
    --exclude='.cache' \
    --exclude='node_modules' \
    -C "$(dirname "$SOURCE_DIR")" \
    "$(basename "$SOURCE_DIR")" 2>&1 | grep -v "Removing leading"

# Calculate size / Méret számítása
SIZE=$(du -h "$BACKUP_FILE" | cut -f1)

# Calculate checksum / Checksum számítása
CHECKSUM=$(sha256sum "$BACKUP_FILE" | cut -d' ' -f1)

echo -e "${GREEN}Backup completed successfully!${NC}"
echo "File: $BACKUP_FILE"
echo "Size: $SIZE"
echo "Checksum: $CHECKSUM"

# Save checksum / Checksum mentése
echo "$CHECKSUM  $(basename "$BACKUP_FILE")" > "${BACKUP_FILE}.sha256"

exit 0
