import requests

from app.config import settings


def generate_embedding(text: str) -> list[float]:
    """
    Generate embeddings using the Ollama embedding model.

    This avoids PyTorch and sentence-transformers
    inside the application container.
    """

    url = f"{settings.ollama_host}/api/embed"

    payload = {
        "model": settings.ollama_embedding_model,
        "input": text,
    }

    response = requests.post(
        url,
        json=payload,
        timeout=120,
    )

    response.raise_for_status()

    data = response.json()

    return data["embeddings"][0]