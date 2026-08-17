FROM python:3.12-slim

# Prevent Python from creating .pyc files
# and make logs appear immediately
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System dependency required by psycopg2
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency file
COPY requirements.txt .

# Install CPU-only PyTorch first.
# This prevents pip from downloading NVIDIA CUDA packages.
RUN pip install --no-cache-dir \
    --index-url https://download.pytorch.org/whl/cpu \
    torch

# Install application dependencies.
# --extra-index-url allows pip to use PyPI for packages
# other than torch.
RUN pip install --no-cache-dir \
    --extra-index-url https://pypi.org/simple \
    -r requirements.txt

# Copy application source
COPY app ./app

# Copy documents
COPY documents ./documents

# Copy PostgreSQL initialization files
COPY postgres ./postgres

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
