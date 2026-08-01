#!/bin/bash
# VidRush Cron Runner

cd /home/junglee01/youtube-viral-machine

# Activate virtual environment
source venv/bin/activate 2>/dev/null || true

# Run the pipeline (without --dry-run so it uploads)
python3 vidrush_pipeline.py

# Check if today is Sunday (day 0) for the weekly audit
DAY_OF_WEEK=$(date +%w)
if [ "$DAY_OF_WEEK" -eq 0 ]; then
    echo "Running weekly audit..."
    python3 weekly_audit.py
fi
