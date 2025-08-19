FROM python:3.11-slim

# Build argument to specify the service directory
ARG SERVICE_DIR

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 

# Copy and install common requirements from the 'bases' directory
COPY services/bases/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the shared common module and prompts into the app directory
COPY common /app/common
COPY prompts /app/prompts

# Copy the specific service's code into the app directory
COPY ${SERVICE_DIR} /app

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
