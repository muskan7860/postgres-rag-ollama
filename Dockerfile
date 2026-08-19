FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DEFAULT_TIMEOUT=300

WORKDIR /app


# ==========================================================
# RUNTIME SYSTEM DEPENDENCIES
# ==========================================================

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*


# ==========================================================
# PYTHON DEPENDENCIES
#
# requirements.txt is copied separately so Docker/Kaniko
# can reuse this layer when only application code changes.
# ==========================================================

COPY requirements.txt .

RUN pip install \
    --no-cache-dir \
    --timeout 300 \
    --retries 5 \
    -r requirements.txt


# ==========================================================
# APPLICATION
# ==========================================================

COPY app ./app
COPY frontend.py .
COPY documents ./documents
COPY postgres ./postgres


# ==========================================================
# NON-ROOT USER
# ==========================================================

RUN useradd \
      --create-home \
      --shell /bin/bash \
      appuser \
    && chown -R appuser:appuser /app

USER appuser


# FastAPI
EXPOSE 8000

# Streamlit
EXPOSE 8501


# Default container command.
# Kubernetes overrides this for the Streamlit container.
CMD [
    "uvicorn",
    "app.main:app",
    "--host",
    "0.0.0.0",
    "--port",
    "8000"
]