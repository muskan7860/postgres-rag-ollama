from fastapi import FastAPI

from app.config import settings


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "application": settings.app_name,
        "environment": settings.app_env,
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


@app.get("/config")
def config():
    return {
        "ollama_model": settings.ollama_model,
        "ollama_host": settings.ollama_host,
        "postgres_host": settings.postgres_host,
    }