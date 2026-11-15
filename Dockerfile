# Public-safe Dockerfile template for the MotherlyPulse Telegram bot service.
# Runs as a non-root user (UID/GID 10001) using Python standard-library runtime.
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MOTHERLYPULSE_DB_PATH=/var/lib/motherlypulse/motherlypulse_user_store.db

WORKDIR /app

RUN groupadd --gid 10001 motherlypulse \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin motherlypulse \
    && mkdir -p /var/lib/motherlypulse /var/backups/motherlypulse \
    && chown -R 10001:10001 /var/lib/motherlypulse /var/backups/motherlypulse

COPY motherlypulse_app/ /app/motherlypulse_app/
COPY MotherlyPulse_Data/ /app/MotherlyPulse_Data/
COPY run_telegram_bot.py /app/run_telegram_bot.py

USER 10001:10001

CMD ["python", "-u", "/app/run_telegram_bot.py"]
