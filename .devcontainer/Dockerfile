# Use official Python image
FROM python:3.11-slim

# Set root user (to avoid permission issues)
USER root

# Set working directory
WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    python3-dev \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    libffi-dev \
    libssl-dev \
    git \
    unzip \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project (including agents/)
COPY . .

# Install project in editable mode (so Python recognizes agents/ as a package)
RUN pip install -e .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/workspace:${PYTHONPATH}"

# (Optional) Set default command to run your script
# CMD ["python", "main_OAIAgentic.py"]