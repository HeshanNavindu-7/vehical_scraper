# Use a lightweight Python image
FROM python:3.9-slim

# Install cron and required tools
RUN apt-get update && apt-get install -y cron \
    wget \
    curl \
    unzip \
    chromium \
    chromium-driver \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set Chrome binary environment variable
ENV CHROME_BIN=/usr/bin/chromium

ENV TZ=Asia/Colombo
RUN apt-get install -y tzdata && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone

# Set work directory
WORKDIR /app

# Copy only requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Add .env file to container
COPY .env .

# Copy crontab file
COPY cronjob.txt /etc/cron.d/scraper-cron

# Give cronjob file correct permissions and register it
RUN chmod 0644 /etc/cron.d/scraper-cron && \
    crontab /etc/cron.d/scraper-cron

# Create log file for cron
RUN touch /var/log/cron.log

# Start cron and log output
CMD ["sh", "-c", "cron && tail -f /var/log/cron.log"]
