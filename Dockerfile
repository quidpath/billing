# Use a lightweight Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies (including bash so the script works properly)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements/ /app/requirements/
RUN pip install --no-cache-dir -r requirements/prod.txt

# Copy project files
COPY . /app

# Copy and set up start script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Default for production; stage deploy must set DJANGO_SETTINGS_MODULE=billing_service.settings.stage
# (e.g. in docker-compose.stage.yml) so the image uses stage settings and deploy secrets, not this default.
ENV DJANGO_SETTINGS_MODULE=billing_service.settings.prod

# Expose Django port
EXPOSE 8000

# Run using bash (not sh)
CMD ["/bin/bash", "/start.sh"]






