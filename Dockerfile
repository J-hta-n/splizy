# Stage 1: Build
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --target=/app/libs -r requirements.txt

COPY . .

# Stage 2: Runtime
FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /app /app

ENV PYTHONPATH="/app/libs"

CMD ["python3", "main.py"]
