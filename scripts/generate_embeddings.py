"""
This script generates embeddings for research papers stored in a PostgreSQL database.
It fetches papers without embeddings, creates embeddings using OpenAI's API, and updates the database with 
the generated embeddings.

Functions:
- create_db_cursor: Connects to the PostgreSQL database and retrieves papers without embeddings.
- fetch_papers: Fetches a specified number of research papers from the database.
- truncate_docs: Truncates document content to fit within token limits for embedding generation.
- create_embeddings: Generates embeddings for a list of research papers using OpenAI's API.
- update_papers: Updates the database with the generated embeddings for the corresponding papers.
- main: Main function to control the flow of the script, including fetching papers, generating embeddings, 
and updating the database.

Environment Variables:
- RUN_EMBED_GEN: Flag to control whether the embedding generation process should run.
- POSTGRES_HOST: Host address of the PostgreSQL database.
- POSTGRES_DB: Name of the PostgreSQL database.
- POSTGRES_USER: Username for the PostgreSQL database.
- POSTGRES_PASSWORD: Password for the PostgreSQL database.
- ARXIV_TABLE: Name of the table containing research papers.
- OPENAI_API_KEY: API key for accessing OpenAI's services.
"""

import os
import time

from openai import OpenAI
import psycopg2
import tiktoken

import helper
import utils


def create_db_cursor() -> tuple:
    """
    Connects to the PostgreSQL database and retrieves papers without embeddings.
    """
    conn = psycopg2.connect(utils.create_conn_string())
    cur = conn.cursor()

    TABLE_NAME = os.getenv("ARXIV_TABLE")

    if not TABLE_NAME:
        raise ValueError("Table name not found in environment variables")

    cur.execute(
        f"SELECT title, link, authors, content, chunk_num FROM {TABLE_NAME} WHERE embedding IS NULL;"
    )

    return conn, cur


def fetch_papers(cur, chunksize: int, debug: bool) -> list[helper.ResearchPaper]:
    """
    Fetches a specified number of research papers from the database.
    """
    try:
        data = cur.fetchmany(chunksize) if not debug else cur.fetchmany(5)
    except psycopg2.ProgrammingError:
        return []

    return [
        helper.ResearchPaper(
            title=paper[0],
            link=paper[1],
            authors=paper[2],
            content=paper[3],
            chunk_num=paper[4],
        )
        for paper in data
    ]


def truncate_docs(doc: str) -> str:
    """
    Truncates document content to fit within token limits for embedding generation.
    """
    enc = tiktoken.get_encoding("cl100k_base")
    encodings = enc.encode(doc)

    if len(encodings) < 8100:
        return doc
    else:
        doc_ = doc.split()
        # Keep removing words until the length is less than 8100 tokens
        return truncate_docs(" ".join(doc_[: len(doc_) - 500]))


def create_embeddings(papers: list[helper.ResearchPaper]) -> list[list[float]]:
    """
    Generates embeddings for a list of research papers using OpenAI's API.
    """
    time.sleep(1)

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    docs = [
        truncate_docs(f"{paper.title} {paper.authors} {paper.content}")
        for paper in papers
    ]

    resp = client.embeddings.create(
        model="text-embedding-3-small",
        input=docs,
        encoding_format="float",
    )

    embeds = [emb.embedding for emb in resp.data]

    return embeds


def update_papers(
    conn, papers: list[helper.ResearchPaper], embeds: list[list[float]]
) -> None:
    """
    Updates the database with the generated embeddings for the corresponding papers.
    """
    cur = conn.cursor()
    TABLE_NAME = os.getenv("ARXIV_TABLE")

    if not TABLE_NAME:
        raise ValueError("Table name not found in environment variables")

    args_str = ",".join(
        cur.mogrify("(%s, %s, %s)", (embed, paper.link, paper.chunk_num)).decode(
            "utf-8"
        )
        for paper, embed in zip(papers, embeds)
    )
    cur.execute(
        f"UPDATE {TABLE_NAME} AS t SET embedding = v.embedding FROM (VALUES {args_str}) AS v(embedding, link, chunk_num) WHERE t.link = v.link AND t.chunk_num = v.chunk_num;"
    )


def main():
    if not os.getenv("RUN_EMBED_GEN"):
        print("Environment variable 'RUN_EMBED_GEN' is not set.")
        return
    elif os.environ["RUN_EMBED_GEN"].lower() != "true":
        print("Not running embedding generator.")
        print(
            'Set the environment variable "RUN_EMBED_GEN=true" to run the embedding generator.'
        )
        return

    DEBUG = False  # Set to True for running on a small subset of data
    CHUNKSIZE = 500  # Number of papers to process in each iteration

    conn, cur = create_db_cursor()

    # Process papers in chunks till all papers are processed
    while True:
        papers = fetch_papers(cur, chunksize=CHUNKSIZE, debug=DEBUG)

        if not papers:
            print("No more papers to process.")
            break

        embeds = create_embeddings(papers)

        update_papers(conn, papers, embeds)
        conn.commit()

        if DEBUG:
            break

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
