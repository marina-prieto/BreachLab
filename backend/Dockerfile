FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY api.py .
EXPOSE 5000
# 1 worker: mantiene coherentes el contador de intentos y la BD SQLite del laboratorio.
CMD ["gunicorn", "-b", "0.0.0.0:5000", "--workers", "1", "api:app"]
