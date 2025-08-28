FROM python:3.11-slim

ARG SERVICE_DIR

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install base requirements (including uvicorn)
COPY services/bases/requirements.txt /app/requirements-base.txt
RUN pip install --no-cache-dir -r /app/requirements-base.txt

# Install service-specific requirements if they exist
COPY ${SERVICE_DIR}/requirements.txt /app/requirements-service.txt
RUN pip install --no-cache-dir -r /app/requirements-service.txt || echo "Failed to install service requirements"

# Copy application code
COPY common /app/common
COPY prompts /app/prompts
COPY ${SERVICE_DIR} /app/service

# Simple startup - run app.py directly from the service directory
WORKDIR /app/service
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
