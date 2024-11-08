import os
import time

from openai import OpenAI
import psycopg2
import tiktoken

import helper
import utils


def create_db_cursor() -> tuple:
    # Connect to the PostgreSQL database
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
    enc = tiktoken.get_encoding("cl100k_base")
    encodings = enc.encode(doc)

    if len(encodings) < 8100:
        return doc
    else:
        doc_ = doc.split()
        return truncate_docs(" ".join(doc_[: len(doc_) - 500]))


def create_embeddings(papers: list[helper.ResearchPaper]) -> list[list[float]]:
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

    DEBUG = False
    CHUNKSIZE = 500

    conn, cur = create_db_cursor()

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
    # os.environ["RUN_EMBED_GEN"] = "true"
    # os.environ["POSTGRES_HOST"] = "127.0.0.1"
    # os.environ["POSTGRES_DB"] = "lithium_ion_content"
    # os.environ["POSTGRES_USER"] = "postgres"
    # os.environ["POSTGRES_PASSWORD"] = "password"
    # os.environ["ARXIV_TABLE"] = "arxiv"
    # os.environ["POSTGRES_HOST"] = "127.0.0.1"
    # os.environ["OPENAI_API_KEY"] = (
    #     "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"
    # )
    main()
