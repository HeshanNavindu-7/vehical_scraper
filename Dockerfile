# Use the official Python base image
FROM python:3.9-slim

# Install dependencies for Chrome and WebDriver
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    chromium \
    chromium-driver

# Set the environment variable for Chrome
ENV CHROME_BIN=/usr/bin/chromium

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project (including the src directory) into the container
COPY . .

# # Set environment variable to disable Python buffering (for logs)
# ENV PYTHONUNBUFFERED 1

# # Set the Python path to include the src directory
# ENV PYTHONPATH=/app/src

# Command to run the scraper when the container starts
CMD ["python", "main.py"]
