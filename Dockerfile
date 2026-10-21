FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    curl rclone cron procps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .
RUN chmod +x start.sh cleanup.sh
EXPOSE 5001
CMD ["/start.sh"]