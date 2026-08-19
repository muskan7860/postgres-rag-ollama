import requests

from app.config import settings


def generate_answer(
    prompt: str,
    model: str | None = None,
) -> str:
    url = f"{settings.ollama_host}/api/generate"

    payload = {
        "model": model or settings.ollama_model,
        "prompt": prompt,
        "stream": False,
    }

    response = requests.post(
        url,
        json=payload,
        timeout=180,
    )

    response.raise_for_status()

    data = response.json()

    return data["response"]


def check_ollama():
    response = requests.get(
        f"{settings.ollama_host}/api/tags",
        timeout=10,
    )

    response.raise_for_status()

    return response.json()