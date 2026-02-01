# Llama 3 + PostgreSQL (pgvector) RAG

Use state-of-the-art open source **Llama 3** models from Hugging Face to query and interact with your **PostgreSQL** database using **pgvector** for semantic search.

This project demonstrates a Retrieval-Augmented Generation (RAG) pipeline where knowledge is stored as vector embeddings in Postgres, enabling Llama 3 to answer semantic questions about your data with high accuracy.

## 🚀 Features

-   **LLM Power**: Integration with Meta's **Llama 3** (8B) via Hugging Face.
-   **Vector Database**: High-performance vector similarity search using **pgvector** on PostgreSQL.
-   **RAG Pipeline**: Semantic retrieval of context to ground the LLM's answers.
-   **Open Source Stack**: Built entirely on open frameworks (LangChain, Hugging Face, Postgres).

## 🛠️ Tech Stack

-   **Python 3.10+**
-   **Language Model**: [Meta-Llama-3-8B](https://huggingface.co/meta-llama/Meta-Llama-3-8B) (via `huggingface_hub`)
-   **Orchestration**: [LangChain](https://www.langchain.com/)
-   **Database**: PostgreSQL with `pgvector` extension
-   **Embeddings**: Hugging Face Embeddings (e.g., `sentence-transformers/all-mpnet-base-v2`)

## 📋 Prerequisites

1.  **Hugging Face Account**:
    -   You must have a Hugging Face account and accept the license terms for [Meta-Llama-3](https://huggingface.co/meta-llama/Meta-Llama-3-8B).
    -   Create a **User Access Token** (Read).
2.  **PostgreSQL with pgvector**:
    -   You can run this via Docker:
        ```bash
        docker run --name postgres-vector -e POSTGRES_PASSWORD=mysecretpassword -p 5432:5432 -d ankane/pgvector
        ```

## 📦 Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/sh1vkumar/LlamaIndex-pgvector.git
    cd LlamaIndex-pgvector
    ```

2.  **Create a virtual environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: Ensure you include `langchain`, `langchain-postgres`, `huggingface_hub`, `psycopg2-binary`, etc.)*

4.  **Configure Credentials**:
    Create a `secrets.ini` or `.env` file (do not commit this!):
    ```ini
    [huggingface]
    api_key = hf_YOUR_TOKEN_HERE

    [database]
    connection_string = postgresql+psycopg2://postgres:mysecretpassword@localhost:5432/postgres
    ```

## 🏃 Usage

1.  **Ingest Data**:
    Run the ingestion script to load your documents, chunk them, and save embeddings to Postgres.
    ```bash
    python ingest.py
    ```

2.  **Query the System**:
    Start the chat interface to ask questions against your data.
    ```bash
    python main.py
    ```

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements.

## 📄 License

[MIT](LICENSE)
