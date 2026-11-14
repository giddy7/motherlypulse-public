"""
MotherlyPulse Telegram Bot Launcher
Run this script to connect MotherlyPulse directly to your live Telegram bot.

Usage:
  python run_telegram_bot.py
  python run_telegram_bot.py <TELEGRAM_BOT_TOKEN>
  or set TELEGRAM_BOT_TOKEN in your environment or a .env file.
"""

import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from motherlypulse_app.telegram_bot import run_bot

if __name__ == "__main__":
    run_bot()

