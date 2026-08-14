import requests

from app.config import settings


def generate_answer(prompt: str) -> str:
    url = f"{settings.ollama_host}/api/generate"

    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": False,
    }

    response = requests.post(
        url,
        json=payload,
        timeout=120,
    )

    response.raise_for_status()

    data = response.json()

    return data["response"]