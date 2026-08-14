from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Postgres RAG Ollama"
    app_env: str = "development"
    app_port: int = 8000

    # PostgreSQL
    #postgres_host: str = "postgres-rag-db"
    postgres_host: str = "localhost"

    postgres_port: int = 5432
    postgres_db: str = "postgres_rag"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres123"

    # Ollama
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()