#!/bin/bash
# scripts/run_daily_scraper.sh

# This script serves as the entrypoint for the Docker container or a simple
# shell-based cron job. It navigates to the source directory and executes
# the main Python scraping script.

echo "Starting daily vehicle scraper..."

# Navigate to the source directory inside the container's WORKDIR (/app)
cd /app/src

# Execute the main Python script.
# Ensure `python3` is available and points to the correct Python executable
# within your Docker image.
python3 main.py

echo "Daily vehicle scraper finished."