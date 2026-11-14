#!/bin/bash
# ==============================================================
# MotherlyPulse Automated Server Update & Deployment Script
# Safe update workflow: backup DB -> git pull -> update deps -> restart service
# ==============================================================
set -e

APP_DIR="/opt/motherlypulse"
SERVICE_NAME="motherlypulse"

echo "=== Updating MotherlyPulse on $(hostname) ==="
cd "$APP_DIR"

# 1. Pre-update safety database backup
echo "[1/5] Running pre-deployment safety database backup..."
if [ -f "$APP_DIR/deployment/backup_db.sh" ]; then
    bash "$APP_DIR/deployment/backup_db.sh"
fi

# 2. Fetch latest approved changes from GitHub
echo "[2/5] Pulling latest code from origin main..."
git pull origin main

# 3. Update Python dependencies if requirements changed
echo "[3/5] Verifying dependencies in virtualenv..."
if [ -f "$APP_DIR/requirements.txt" ]; then
    "$APP_DIR/venv/bin/pip" install -q -r "$APP_DIR/requirements.txt"
fi

# 4. Ensure systemd service file is up-to-date
if [ -f "$APP_DIR/deployment/motherlypulse.service" ]; then
    cp "$APP_DIR/deployment/motherlypulse.service" /etc/systemd/system/
    systemctl daemon-reload
fi

# 5. Restart the bot service
echo "[4/5] Restarting systemd service ($SERVICE_NAME)..."
systemctl restart "$SERVICE_NAME"

# 6. Check service status
echo "[5/5] Verifying bot service health..."
sleep 2
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "SUCCESS: $SERVICE_NAME is active and running!"
    systemctl status "$SERVICE_NAME" --no-pager -n 5
else
    echo "ERROR: $SERVICE_NAME failed to start! Checking logs:"
    journalctl -u "$SERVICE_NAME" -n 25 --no-pager
    exit 1
fi
