FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install flask psycopg2-binary redis --quiet

WORKDIR /app
COPY app/app.py .

CMD ["python", "app.py"]