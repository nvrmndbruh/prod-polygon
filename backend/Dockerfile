FROM python:3.12-slim

# Устанавливаем Docker CLI через официальный скрипт
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && curl -fsSL https://get.docker.com | sh \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", \
     "--port", "8000", "--reload"]