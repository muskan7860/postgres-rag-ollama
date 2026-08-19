import os

import requests
import streamlit as st


BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://localhost:8000",
)


st.set_page_config(
    page_title="PostgreSQL RAG Ollama",
    page_icon="🤖",
    layout="wide",
)


st.title("PostgreSQL RAG Chatbot")

st.caption(
    "Ollama + PostgreSQL + pgvector + "
    "Sentence Transformers"
)


# ==========================================================
# SIDEBAR
# ==========================================================

with st.sidebar:

    st.header("Database Connection")

    db_host = st.text_input(
        "DB Host",
        value="postgres-rag-db",
    )

    db_port = st.number_input(
        "DB Port",
        value=5432,
    )

    db_name = st.text_input(
        "DB Name",
        value="postgres_rag",
    )

    db_user = st.text_input(
        "DB User",
        value="postgres",
    )

    db_password = st.text_input(
        "DB Password",
        value="postgres123",
        type="password",
    )

    schema = st.text_input(
        "Schema",
        value="public",
    )

    st.divider()

    st.header("AI Configuration")

    ollama_model = st.selectbox(
        "Ollama Model",
        [
            "llama3.2:3b",
            "llama3.2:1b",
            "mistral",
            "phi3",
        ],
    )


    connection_payload = {
        "host": db_host,
        "port": int(db_port),
        "database": db_name,
        "user": db_user,
        "password": db_password,
        "schema_name": schema,
    }


    if st.button(
        "Test Database Connection",
        use_container_width=True,
    ):

        try:

            response = requests.post(
                f"{BACKEND_URL}/connect",
                json=connection_payload,
                timeout=20,
            )

            if response.ok:

                st.success(
                    "PostgreSQL connected successfully"
                )

            else:

                st.error(
                    response.json().get(
                        "detail",
                        response.text,
                    )
                )

        except Exception as exc:

            st.error(
                f"Backend connection failed: {exc}"
            )


    if st.button(
        "Connect / Refresh Index",
        type="primary",
        use_container_width=True,
    ):

        with st.spinner(
            "Reading PostgreSQL tables and "
            "generating embeddings..."
        ):

            try:

                response = requests.post(
                    f"{BACKEND_URL}/index",
                    json=connection_payload,
                    timeout=600,
                )

                if response.ok:

                    data = response.json()

                    st.success(
                        "RAG index created successfully"
                    )

                    st.info(
                        f"Tables indexed: "
                        f"{len(data['tables'])}\n\n"
                        f"Rows indexed: "
                        f"{data['indexed_rows']}"
                    )

                else:

                    st.error(
                        response.json().get(
                            "detail",
                            response.text,
                        )
                    )

            except Exception as exc:

                st.error(
                    f"Indexing failed: {exc}"
                )


# ==========================================================
# MAIN CHAT
# ==========================================================

st.subheader("Ask Your PostgreSQL Database")

st.write(
    "Ask questions in natural language. "
    "The application retrieves relevant PostgreSQL "
    "records using pgvector and sends only the "
    "retrieved context to Ollama."
)


if "messages" not in st.session_state:

    st.session_state.messages = []


for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


question = st.chat_input(
    "Example: Which employees work in Engineering?"
)


if question:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    with st.chat_message("user"):

        st.markdown(question)


    request_payload = {
        **connection_payload,
        "question": question,
        "model": ollama_model,
    }


    with st.chat_message("assistant"):

        with st.spinner(
            "Searching PostgreSQL and asking Ollama..."
        ):

            try:

                response = requests.post(
                    f"{BACKEND_URL}/ask",
                    json=request_payload,
                    timeout=240,
                )

                if response.ok:

                    data = response.json()

                    answer = data["answer"]

                    st.markdown(answer)


                    with st.expander(
                        "Retrieved PostgreSQL Context"
                    ):

                        for index, source in enumerate(
                            data.get("sources", []),
                            start=1,
                        ):

                            st.markdown(
                                f"### Source {index}"
                            )

                            st.write(
                                f"Table: "
                                f"`{source['table']}`"
                            )

                            st.write(
                                f"Similarity: "
                                f"`{source['similarity']}`"
                            )

                            st.code(
                                source["content"]
                            )


                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": answer,
                        }
                    )

                else:

                    error = response.json().get(
                        "detail",
                        response.text,
                    )

                    st.error(error)

            except Exception as exc:

                st.error(
                    f"RAG request failed: {exc}"
                )


st.divider()

st.caption(
    "PostgreSQL RAG powered locally by Ollama • "
    "No OpenAI API required"
)