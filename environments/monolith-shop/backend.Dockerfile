FROM python:3.11-slim

RUN pip install flask psycopg2-binary redis --quiet

WORKDIR /app
COPY app/app.py .

CMD ["python", "app.py"]