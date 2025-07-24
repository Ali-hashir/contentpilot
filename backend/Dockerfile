# backend/Dockerfile
FROM python:3.11-slim

# Faster installs
ENV POETRY_VERSION=1.8.2 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy & install only requirements first (speeds rebuilds)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of the code
COPY backend/ .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
