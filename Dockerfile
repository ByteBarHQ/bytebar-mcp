FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .
COPY data ./data

EXPOSE 8000

# Honors $PORT (set by Railway / Render / Fly.io), defaults to 8000.
CMD ["sh", "-c", "python server.py --transport streamable-http --host 0.0.0.0 --port ${PORT:-8000}"]
