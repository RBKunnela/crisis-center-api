FROM python:3.9-slim-buster

# Add debugging information during build
RUN echo "Starting build process..."

WORKDIR /app

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser

# Install dependencies and add debug output
COPY requirements.txt .
RUN echo "Installing dependencies..." && \
    pip install --no-cache-dir -r requirements.txt && \
    echo "Dependencies installed successfully"

# Copy application files
COPY . .
RUN echo "Application files copied"

# Set ownership and show debug info
RUN chown -R appuser:appuser /app && \
    echo "Permissions set for appuser"

USER appuser

EXPOSE 5000

# Add environment variable to enable Flask debugging
ENV FLASK_DEBUG=1

# Modify the CMD to include more logging
CMD echo "Starting Gunicorn server..." && \
    gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 --log-level debug app:app