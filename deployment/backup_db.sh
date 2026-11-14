#!/bin/bash
# ==============================================================
# MotherlyPulse Automated Database Backup Script (Cron-Ready)
# Uses SQLite Online Backup API / .backup for WAL-safe snapshots.
# ==============================================================
set -e

BACKUP_DIR="/var/backups/motherlypulse"
DEFAULT_DB="/var/lib/motherlypulse/motherlypulse_user_store.db"
DB_PATH="${MOTHERLYPULSE_DB_PATH:-$DEFAULT_DB}"

# 1. Verify database exists
if [ ! -f "$DB_PATH" ]; then
    echo "[$(date -u)] Database $DB_PATH not found. Skipping backup."
    exit 0
fi

# 2. Ensure backup directory exists with restricted permissions (700)
mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

# 3. Create timestamped backup file
TIMESTAMP=$(date -u +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/motherlypulse_backup_$TIMESTAMP.sqlite3"

echo "[$(date -u)] Starting online backup of $DB_PATH..."
# Uses sqlite3 CLI online backup command (non-blocking, handles WAL mode)
sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'"

# Set restrictive permissions (600: read/write only by owner)
chmod 600 "$BACKUP_FILE"
echo "[$(date -u)] Backup created successfully: $BACKUP_FILE"

# 4. Prune backups older than 14 days
find "$BACKUP_DIR" -type f -name "motherlypulse_backup_*.sqlite3" -mtime +14 -delete
echo "[$(date -u)] Pruned backups older than 14 days."

