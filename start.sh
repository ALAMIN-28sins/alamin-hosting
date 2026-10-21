#!/bin/bash
# ক্রন জব
echo "0 3 * * * /app/cleanup.sh >> /var/log/cleanup.log 2>&1" | crontab -
service cron start

# Flask (Gunicorn)
gunicorn --bind 0.0.0.0:${PORT:-5001} --workers 2 --threads 4 --timeout 120 app:app &

# Telegram বট
python telegram_bot.py &

wait