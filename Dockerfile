FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DEFAULT_TIMEOUT=300

WORKDIR /app

# PostgreSQL runtime library
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install CPU-only PyTorch
RUN pip install \
    --no-cache-dir \
    --timeout 300 \
    --retries 10 \
    --index-url https://download.pytorch.org/whl/cpu \
    torch

# Install remaining application dependencies
RUN pip install \
    --no-cache-dir \
    --timeout 300 \
    --retries 10 \
    -r requirements.txt

COPY app ./app
COPY frontend.py .
COPY documents ./documents
COPY postgres ./postgres

RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000
EXPOSE 8501

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
