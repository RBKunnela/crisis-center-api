# Start with a specific Python version for stability
FROM python:3.9-slim-buster

# Set up a working directory for our application
WORKDIR /app

# Create a non-root user for security
RUN adduser --disabled-password --gecos '' appuser

# Install dependencies first to take advantage of Docker's cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of our application code
COPY . .

# Set proper ownership
RUN chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Open port 5000 for our Flask application
EXPOSE 5000

# Start the application using gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app:app"]