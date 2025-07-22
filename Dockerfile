# Use official Python image
FROM python:3.11-slim

# Set work directory
WORKDIR /workspace

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and setup files
COPY requirements.txt setup.py ./

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install .

# Copy the rest of the code
COPY . .

# Default command (can be overridden in devcontainer)
CMD ["python", "main_OAIAgentic.py"] 