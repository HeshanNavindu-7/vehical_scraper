# Use a lightweight Python image
FROM python:3.9-slim

# Install dependencies for Chromium
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    chromium \
    chromium-driver \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set Chrome binary environment variable
ENV CHROME_BIN=/usr/bin/chromium

# Set work directory
WORKDIR /app

# Copy only requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Add .env file to container (if needed) – optional but recommended
COPY .env .

# Command to run the scraper
CMD ["python", "main.py"]
