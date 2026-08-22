def generate_answer(question: str, context: str) -> str:
    prompt = f"""
You are a PostgreSQL RAG assistant.

Your job is to answer the user's question using ONLY the retrieved PostgreSQL context below.

IMPORTANT RULES:
- Do NOT generate SQL.
- Do NOT explain SQL.
- Do NOT suggest a query.
- Return a direct natural-language answer.
- Use only the retrieved context.
- If the answer is not present, say:
  "I don't have enough information in the retrieved PostgreSQL data."

Retrieved PostgreSQL Context:
{context}

User Question:
{question}

Direct Answer:
"""

    response = requests.post(
        f"{settings.ollama_host}/api/generate",
        json={
            "model": settings.ollama_model,
            "prompt": prompt,
            "stream": False,
        },
        timeout=180,
    )

    response.raise_for_status()

    return response.json()["response"].strip()