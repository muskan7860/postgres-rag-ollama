def generate_answer(question: str, context: str) -> str:
    """
    Generate a direct natural-language answer from retrieved PostgreSQL context.
    """

    prompt = f"""
You are a PostgreSQL RAG assistant.

Answer the user's question using ONLY the retrieved PostgreSQL data below.

STRICT RULES:
1. Give a direct natural-language answer.
2. NEVER generate SQL.
3. NEVER return SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, or any SQL statement.
4. Do not explain how to query the database.
5. Do not mention SQL unless the user specifically asks about SQL.
6. Use only facts present in the retrieved context.
7. If the answer is not present in the context, reply exactly:
   I don't have enough information in the retrieved PostgreSQL data.

Retrieved PostgreSQL Data:
-------------------------
{context}
-------------------------

User Question:
{question}

Return only the final answer in plain English.

Final Answer:
"""

    response = requests.post(
        f"{settings.ollama_host}/api/generate",
        json={
            "model": settings.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1
            }
        },
        timeout=180,
    )

    response.raise_for_status()

    answer = response.json()["response"].strip()

    return answer