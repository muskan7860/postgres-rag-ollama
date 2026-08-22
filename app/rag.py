import requests
from psycopg2 import sql

from app.config import settings
from app.database import get_connection
from app.embeddings import generate_embedding


# ==========================================================
# VECTOR STORE
# ==========================================================

def ensure_vector_store(connection):
    """
    Enable pgvector and create the table used by the RAG system.
    """

    with connection.cursor() as cursor:

        cursor.execute(
            """
            CREATE EXTENSION IF NOT EXISTS vector;
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS rag_documents (
                id BIGSERIAL PRIMARY KEY,
                source_table TEXT NOT NULL,
                content TEXT NOT NULL,
                embedding vector(384)
            );
            """
        )

    connection.commit()


# ==========================================================
# TABLE DISCOVERY
# ==========================================================

def get_tables(connection, schema="public"):
    """
    Discover application tables from PostgreSQL.

    rag_documents itself is excluded because it is our
    vector index table.
    """

    with connection.cursor() as cursor:

        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
              AND table_type = 'BASE TABLE'
              AND table_name != 'rag_documents'
            ORDER BY table_name;
            """,
            (schema,),
        )

        return [
            row[0]
            for row in cursor.fetchall()
        ]


# ==========================================================
# BUILD / REFRESH VECTOR INDEX
# ==========================================================

def refresh_index(
    host,
    port,
    database,
    user,
    password,
    schema="public",
):
    """
    Complete indexing workflow:

    PostgreSQL rows
        ↓
    text documents
        ↓
    Ollama all-minilm embeddings
        ↓
    PostgreSQL pgvector
    """

    connection = get_connection(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
    )

    indexed_rows = 0
    indexed_tables = []

    try:

        ensure_vector_store(connection)

        tables = get_tables(
            connection,
            schema=schema,
        )

        # Rebuild index from current database contents.
        with connection.cursor() as cursor:

            cursor.execute(
                "TRUNCATE TABLE rag_documents;"
            )

        connection.commit()


        for table in tables:

            # ----------------------------------------------
            # Read source table
            # ----------------------------------------------

            with connection.cursor() as cursor:

                query = sql.SQL(
                    "SELECT * FROM {}.{}"
                ).format(
                    sql.Identifier(schema),
                    sql.Identifier(table),
                )

                cursor.execute(query)

                column_names = [
                    description[0]
                    for description in cursor.description
                ]

                rows = cursor.fetchall()


            # ----------------------------------------------
            # Convert every PostgreSQL row into RAG document
            # ----------------------------------------------

            for row in rows:

                row_data = dict(
                    zip(
                        column_names,
                        row,
                    )
                )

                content_parts = [
                    f"{key}: {value}"
                    for key, value in row_data.items()
                ]

                content = (
                    f"Table: {table}\n"
                    + "\n".join(content_parts)
                )


                # Generate vector using Ollama all-minilm
                embedding = generate_embedding(
                    content
                )


                # Store document + vector
                with connection.cursor() as cursor:

                    cursor.execute(
                        """
                        INSERT INTO rag_documents
                        (
                            source_table,
                            content,
                            embedding
                        )
                        VALUES
                        (
                            %s,
                            %s,
                            %s
                        );
                        """,
                        (
                            table,
                            content,
                            embedding,
                        ),
                    )

                indexed_rows += 1


            indexed_tables.append(
                table
            )


        connection.commit()


        return {
            "tables": indexed_tables,
            "indexed_rows": indexed_rows,
        }


    except Exception:

        connection.rollback()
        raise


    finally:

        connection.close()


# ==========================================================
# VECTOR SEARCH
# ==========================================================

def search_documents(
    query,
    host,
    port,
    database,
    user,
    password,
    limit=5,
):
    """
    Semantic search against PostgreSQL pgvector.
    """

    query_embedding = generate_embedding(
        query
    )


    connection = get_connection(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
    )


    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    source_table,
                    content,
                    1 - (
                        embedding <=> %s::vector
                    ) AS similarity
                FROM rag_documents
                ORDER BY
                    embedding <=> %s::vector
                LIMIT %s;
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


# ==========================================================
# OLLAMA ANSWER GENERATION
# ==========================================================

def generate_answer(
    question: str,
    context: str,
    model: str | None = None,
) -> str:
    """
    Generate a direct natural-language answer using only
    retrieved PostgreSQL context.
    """

    prompt = f"""
You are an enterprise PostgreSQL RAG assistant.

Your task is to answer the user's question using ONLY the
retrieved PostgreSQL records supplied below.

STRICT RULES:

1. Answer the question directly in natural language.

2. NEVER generate SQL.

3. NEVER return SELECT, INSERT, UPDATE, DELETE,
   CREATE, DROP, ALTER, or any other SQL statement.

4. Do NOT tell the user how to query the database.

5. Do NOT invent information.

6. Use only facts contained in the retrieved
   PostgreSQL records.

7. When multiple records answer the question,
   include all relevant records.

8. If the requested information does not exist
   in the retrieved data, respond exactly:

   I don't have enough information in the retrieved PostgreSQL data.


Example:

Question:
Who is the DevOps Engineer?

Retrieved record:
name: Muskan Patel
role: DevOps Engineer
location: Pune

Correct answer:
Muskan Patel is the DevOps Engineer.

Incorrect answer:
SELECT name FROM employees WHERE role = 'DevOps Engineer';


Retrieved PostgreSQL Records:
================================

{context}

================================

User Question:

{question}

Return ONLY the direct natural-language answer.

Answer:
"""


    response = requests.post(
        f"{settings.ollama_host}/api/generate",
        json={
            "model": model or settings.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.0,
            },
        },
        timeout=180,
    )


    response.raise_for_status()


    answer = (
        response
        .json()["response"]
        .strip()
    )


    return answer


# ==========================================================
# COMPLETE RAG PIPELINE
# ==========================================================

def answer_question(
    question,
    host,
    port,
    database,
    user,
    password,
    model=None,
):
    """
    Complete RAG workflow:

    Question
        ↓
    Ollama embedding
        ↓
    pgvector similarity search
        ↓
    Retrieve PostgreSQL rows
        ↓
    Construct context
        ↓
    Ollama llama3.2
        ↓
    Natural-language answer
    """

    results = search_documents(
        query=question,
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
        limit=5,
    )


    if not results:

        return {
            "answer":
                "I don't have enough information "
                "in the retrieved PostgreSQL data.",
            "sources": [],
        }


    context_blocks = []

    sources = []


    for (
        source_table,
        content,
        similarity,
    ) in results:

        context_blocks.append(
            content
        )

        sources.append(
            {
                "table": source_table,
                "similarity": round(
                    float(similarity),
                    4,
                ),
                "content": content,
            }
        )


    context = "\n\n---\n\n".join(
        context_blocks
    )


    answer = generate_answer(
        question=question,
        context=context,
        model=model,
    )


    return {
        "answer": answer,
        "sources": sources,
    }