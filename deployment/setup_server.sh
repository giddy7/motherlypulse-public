#!/bin/bash
# ==============================================================
# MotherlyPulse Production VPS Server Setup Script
# Target: Ubuntu 22.04/24.04 LTS / Debian 11/12 Linux (Netcup VPS)
# Hardened for unprivileged execution & persistent SQLite storage
# ==============================================================
set -e

REPO_URL="git@github.com:giddy7/motherlypulse.git"
INSTALL_DIR="/opt/motherlypulse"
DATA_DIR="/var/lib/motherlypulse"
BACKUP_DIR="/var/backups/motherlypulse"
SERVICE_USER="motherlypulse"

echo "=== Setting up MotherlyPulse on Host $(hostname) ==="

# 1. Update packages and install prerequisites
echo "[1/8] Installing system prerequisites..."
apt-get update -y
apt-get install -y python3 python3-venv python3-pip git curl sqlite3

# 2. Create unprivileged system service user
echo "[2/8] Configuring unprivileged service account ($SERVICE_USER)..."
if ! id -u "$SERVICE_USER" &>/dev/null; then
    useradd -r -s /bin/false -d "$DATA_DIR" "$SERVICE_USER"
    echo "Created system user '$SERVICE_USER'."
fi

# 3. Create persistent data and backup directories outside Git
echo "[3/8] Setting up persistent data and backup directories..."
mkdir -p "$DATA_DIR"
chown -R "$SERVICE_USER:$SERVICE_USER" "$DATA_DIR"
chmod 750 "$DATA_DIR"

mkdir -p "$BACKUP_DIR"
chown -R "$SERVICE_USER:$SERVICE_USER" "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

# 4. Clone or update repository in /opt/motherlypulse
echo "[4/8] Preparing application code in $INSTALL_DIR..."
if [ ! -d "$INSTALL_DIR" ]; then
    git clone "$REPO_URL" "$INSTALL_DIR"
else
    cd "$INSTALL_DIR"
    git pull origin main
fi

cd "$INSTALL_DIR"

# 5. Database migration check (preserve existing records if present)
if [ ! -f "$DATA_DIR/motherlypulse_user_store.db" ] && [ -f "$INSTALL_DIR/motherlypulse_app/motherlypulse_user_store.db" ]; then
    echo "Migrating existing database to persistent location $DATA_DIR..."
    cp "$INSTALL_DIR/motherlypulse_app/motherlypulse_user_store.db" "$DATA_DIR/motherlypulse_user_store.db"
    chown "$SERVICE_USER:$SERVICE_USER" "$DATA_DIR/motherlypulse_user_store.db"
    chmod 640 "$DATA_DIR/motherlypulse_user_store.db"
fi

# 6. Configure Python virtual environment & dependencies
echo "[5/8] Configuring Python virtual environment..."
if [ ! -d "$INSTALL_DIR/venv" ]; then
    python3 -m venv "$INSTALL_DIR/venv"
fi

"$INSTALL_DIR/venv/bin/pip" install --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

# 7. Environment & Secrets setup
echo "[6/8] Configuring environment secrets..."
if [ ! -f "$INSTALL_DIR/.env" ]; then
    if [ -n "$TELEGRAM_BOT_TOKEN" ]; then
        echo "TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN" > "$INSTALL_DIR/.env"
        echo "MOTHERLYPULSE_DB_PATH=$DATA_DIR/motherlypulse_user_store.db" >> "$INSTALL_DIR/.env"
    else
        cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
        echo "MOTHERLYPULSE_DB_PATH=$DATA_DIR/motherlypulse_user_store.db" >> "$INSTALL_DIR/.env"
        echo "NOTICE: Created $INSTALL_DIR/.env from template. Please set your TELEGRAM_BOT_TOKEN."
    fi
fi
chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/.env"
chmod 600 "$INSTALL_DIR/.env"

# Ensure code ownership
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"

# 8. Install automated daily backup cron job
echo "[7/8] Installing daily SQLite backup cron job..."
chmod +x "$INSTALL_DIR/deployment/backup_db.sh"
ln -sf "$INSTALL_DIR/deployment/backup_db.sh" /etc/cron.daily/motherlypulse_backup

# 9. Register & Start systemd service
echo "[8/8] Installing and starting systemd service..."
cp "$INSTALL_DIR/deployment/motherlypulse.service" /etc/systemd/system/motherlypulse.service
systemctl daemon-reload
systemctl enable motherlypulse
systemctl restart motherlypulse
sleep 2

if systemctl is-active --quiet motherlypulse; then
    echo "=========================================================="
    echo " SUCCESS: MotherlyPulse Telegram Bot is running live 24/7!"
    echo " Running unprivileged under user '$SERVICE_USER'"
    echo " Database persistent at $DATA_DIR/motherlypulse_user_store.db"
    echo " Daily backups configured at $BACKUP_DIR"
    echo "=========================================================="
    systemctl status motherlypulse --no-pager -n 10
else
    echo "ERROR: Service failed to start. Journal logs:"
    journalctl -u motherlypulse -n 25 --no-pager
    exit 1
fi
