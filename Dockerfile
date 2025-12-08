# Use official Python runtime as base image
FROM python:3.13-slim

# Set working directory in container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory for JSON files
RUN mkdir -p /app/data

# Expose port for FastAPI (if using public port, otherwise ngrok handles it)
EXPOSE 8000

# Set environment variables (can be overridden at runtime)
ENV PYTHONUNBUFFERED=1

# Run the bot with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
