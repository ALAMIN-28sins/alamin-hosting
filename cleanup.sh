#!/bin/bash
DATA_DIR="${DATA_DIR:-/data}"
find "$DATA_DIR" -name "*.log" -type f -mtime +7 -delete
find "$DATA_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find "$DATA_DIR" -name "*.pyc" -delete 2>/dev/null
find "$DATA_DIR" -name "*.zip" -type f -mtime +30 -delete 2>/dev/null
pip cache purge 2>/dev/null || true
echo "[$(date)] Cleanup done"