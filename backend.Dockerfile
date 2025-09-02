FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Upgrade pip
RUN pip install --upgrade pip

# Install dependencies
COPY services/bases/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --timeout=100 -r requirements.txt
COPY services/gateway/requirements.txt /app/gateway-requirements.txt
RUN pip install --no-cache-dir --timeout=100 -r gateway-requirements.txt

# Create static directory for audio files
RUN mkdir -p /tmp/static/audio

# Copy application code
COPY common /app/common
COPY prompts /app/prompts
COPY services/gateway /app

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"] 