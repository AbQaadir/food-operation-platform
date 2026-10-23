FROM python:3.12-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY tests/ ./tests/

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
ENV PYTHONPATH=/app
USER appuser

EXPOSE 8087
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8087"]
