from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.database import test_connection
from app.ollama import check_ollama
from app.rag import refresh_index, answer_question


app = FastAPI(
    title=settings.app_name,
    description=(
        "PostgreSQL Retrieval-Augmented Generation "
        "using pgvector, Sentence Transformers and Ollama"
    ),
    version="2.0.0",
)


class DatabaseConfig(BaseModel):
    host: str
    port: int = 5432
    database: str
    user: str
    password: str
    schema_name: str = "public"


class AskRequest(DatabaseConfig):
    question: str
    model: str = "llama3.2:3b"


@app.get("/")
def root():

    return {
        "application": settings.app_name,
        "environment": settings.app_env,
        "version": "2.0.0",
        "status": "running",
        "stack": [
            "FastAPI",
            "PostgreSQL",
            "pgvector",
            "Sentence Transformers",
            "Ollama",
        ],
    }


@app.get("/health")
def health():

    return {
        "status": "healthy",
    }


@app.get("/ollama/health")
def ollama_health():

    try:

        result = check_ollama()

        return {
            "status": "connected",
            "ollama_host": settings.ollama_host,
            "models": result.get("models", []),
        }

    except Exception as exc:

        raise HTTPException(
            status_code=503,
            detail=f"Ollama unavailable: {exc}",
        )


@app.get("/config")
def config():

    return {
        "ollama_model": settings.ollama_model,
        "ollama_host": settings.ollama_host,
        "postgres_host": settings.postgres_host,
    }


@app.post("/connect")
def connect_database(config: DatabaseConfig):

    try:

        version = test_connection(
            host=config.host,
            port=config.port,
            database=config.database,
            user=config.user,
            password=config.password,
        )

        return {
            "status": "connected",
            "database": config.database,
            "server": version,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@app.post("/index")
def build_index(config: DatabaseConfig):

    try:

        result = refresh_index(
            host=config.host,
            port=config.port,
            database=config.database,
            user=config.user,
            password=config.password,
            schema=config.schema_name,
        )

        return {
            "status": "index_created",
            **result,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@app.post("/ask")
def ask_question(request: AskRequest):

    try:

        return answer_question(
            question=request.question,
            host=request.host,
            port=request.port,
            database=request.database,
            user=request.user,
            password=request.password,
            model=request.model,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )