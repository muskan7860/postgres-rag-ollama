from app.database import get_connection
from app.embeddings import generate_embedding
from app.ollama import generate_answer


def ensure_vector_store(connection):
    """
    Ensure pgvector and the RAG documents table exist.
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
                source_table TEXT,
                content TEXT NOT NULL,
                embedding vector(384)
            );
            """
        )

    connection.commit()


def get_tables(connection, schema="public"):
    """
    Discover tables from the selected PostgreSQL schema.
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

        return [row[0] for row in cursor.fetchall()]


def refresh_index(
    host,
    port,
    database,
    user,
    password,
    schema="public",
):
    """
    Read PostgreSQL tables and build the pgvector RAG index.
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

        with connection.cursor() as cursor:

            cursor.execute(
                "TRUNCATE TABLE rag_documents;"
            )

        connection.commit()

        for table in tables:

            with connection.cursor() as cursor:

                cursor.execute(
                    f'SELECT * FROM "{schema}"."{table}"'
                )

                column_names = [
                    description[0]
                    for description in cursor.description
                ]

                rows = cursor.fetchall()

            for row in rows:

                row_data = dict(
                    zip(column_names, row)
                )

                content_parts = [
                    f"{key}: {value}"
                    for key, value in row_data.items()
                ]

                content = (
                    f"Table: {table}\n"
                    + "\n".join(content_parts)
                )

                embedding = generate_embedding(content)

                with connection.cursor() as cursor:

                    cursor.execute(
                        """
                        INSERT INTO rag_documents
                        (
                            source_table,
                            content,
                            embedding
                        )
                        VALUES (%s, %s, %s)
                        """,
                        (
                            table,
                            content,
                            embedding,
                        ),
                    )

                indexed_rows += 1

            indexed_tables.append(table)

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
    Search the PostgreSQL pgvector index.
    """

    query_embedding = generate_embedding(query)

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
                    1 - (embedding <=> %s::vector)
                    AS similarity
                FROM rag_documents
                ORDER BY embedding <=> %s::vector
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


def answer_question(
    question,
    host,
    port,
    database,
    user,
    password,
    model,
):
    """
    Complete RAG pipeline.
    """

    results = search_documents(
        query=question,
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
    )

    if not results:

        return {
            "answer":
                "I don't have enough information "
                "in the indexed PostgreSQL data.",
            "sources": [],
        }

    context_blocks = []

    sources = []

    for source_table, content, similarity in results:

        context_blocks.append(content)

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

    prompt = f"""
You are an enterprise PostgreSQL RAG assistant.

Your job is to answer questions using ONLY the PostgreSQL
database context supplied below.

Do not invent values.

If the requested information does not exist in the supplied
context, clearly say that the indexed database does not contain
enough information to answer.

PostgreSQL Context:
-------------------
{context}

User Question:
--------------
{question}

Provide a clear and concise answer.
"""

    answer = generate_answer(
        prompt=prompt,
        model=model,
    )

    return {
        "answer": answer,
        "sources": sources,
    }