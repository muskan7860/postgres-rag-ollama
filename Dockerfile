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
# ==========================================================

COPY requirements.txt .

RUN pip install \
    --no-cache-dir \
    --timeout 300 \
    --retries 5 \
    -r requirements.txt


# ==========================================================
# APPLICATION FILES
# ==========================================================

COPY app ./app
COPY frontend.py .
COPY documents ./documents
COPY postgres ./postgres


# ==========================================================
# NON-ROOT USER
# ==========================================================

RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app

USER appuser


# ==========================================================
# PORTS
# ==========================================================

EXPOSE 8000
EXPOSE 8501


# ==========================================================
# DEFAULT BACKEND COMMAND
# Kubernetes overrides this for Streamlit frontend container.
# ==========================================================

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]