import requests

from app.config import settings
from app.database import get_connection
from app.embeddings import generate_embedding


def store_document(content: str):
    """
    Generate an embedding for the document and store
    both the document content and embedding in PostgreSQL.
    """

    embedding = generate_embedding(content)
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO documents (content, embedding)
                VALUES (%s, %s)
                """,
                (content, embedding),
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def search_documents(query: str, limit: int = 3):
    """
    Generate an embedding for the user's query and search
    PostgreSQL for the most similar documents using pgvector.
    """

    query_embedding = generate_embedding(query)
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    content,
                    1 - (embedding <=> %s::vector) AS similarity
                FROM documents
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (
                    query_embedding,
                    query_embedding,
                    limit,
                ),
            )

            return cursor.fetchall()

    finally:
        connection.close()


def generate_answer(question: str, context: str) -> str:
    """
    Send the retrieved document context and user's question
    to the Ollama model.
    """

    prompt = f"""
You are a helpful RAG assistant.

Answer the user's question using ONLY the provided context.

If the answer is not present in the context, say:
"I don't have enough information in the provided documents."

Context:
{context}

Question:
{question}

Answer:
"""

    response = requests.post(
        f"{settings.ollama_host}/api/generate",
        json={
            "model": settings.ollama_model,
            "prompt": prompt,
            "stream": False,
        },
        timeout=120,
    )

    response.raise_for_status()

    response_data = response.json()

    return response_data["response"]


def answer_question(question: str) -> str:
    """
    Complete RAG pipeline:

    1. Receive user's question
    2. Generate query embedding
    3. Search PostgreSQL using pgvector
    4. Retrieve the most relevant documents
    5. Build context from retrieved documents
    6. Send context + question to Ollama
    7. Return the generated answer
    """

    results = search_documents(question)

    if not results:
        return "I don't have enough information in the provided documents."

    context = "\n\n".join(
        content
        for content, similarity in results
    )

    return generate_answer(
        question=question,
        context=context,
    )