import os

from openai import OpenAI
import psycopg2
import tiktoken

import helper
import utils


def create_db_cursor() -> tuple:
    # Connect to the PostgreSQL database
    conn = psycopg2.connect(utils.create_conn_string())
    cur = conn.cursor()

    TABLE_NAME = os.getenv("GSCHOLAR_TABLE")

    if not TABLE_NAME:
        raise ValueError("Table name not found in environment variables")

    cur.execute(
        f"SELECT title, link, authors, content, citation_count FROM {TABLE_NAME} ORDER BY citation_count DESC;"
    )

    return conn, cur


def fetch_papers(cur, chunksize: int, debug: bool) -> list[helper.ResearchPaper]:
    cur_ = cur.fetchmany(chunksize) if not debug else cur.fetchmany(5)

    return [
        helper.ResearchPaper(
            title=paper[0],
            link=paper[1],
            authors=paper[2],
            content=paper[3],
            citation_count=paper[4],
        )
        for paper in cur_
    ]


def truncate_docs(doc: str) -> str:
    enc = tiktoken.get_encoding("cl100k_base")
    encodings = enc.encode(doc)

    if len(encodings) < 8100:
        return doc
    else:
        key = enc.decode(encodings[8000:8100])
        return doc[: doc.index(key)]


def create_embeddings(papers: list[helper.ResearchPaper]) -> list[list[float]]:
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
    cur, papers: list[helper.ResearchPaper], embeds: list[list[float]]
) -> None:
    TABLE_NAME = os.getenv("GSCHOLAR_TABLE")

    if not TABLE_NAME:
        raise ValueError("Table name not found in environment variables")

    for paper, embed in zip(papers, embeds):
        cur.execute(
            f"UPDATE {TABLE_NAME} SET embedding = %s WHERE link = %s",
            (embed, paper.link),
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

    DEBUG = True
    CHUNKSIZE = 2048

    conn, cur = create_db_cursor()

    while True:
        papers = fetch_papers(cur, chunksize=CHUNKSIZE, debug=DEBUG)
        embeds = create_embeddings(papers)

        update_papers(cur, papers, embeds)
        conn.commit()

        if not papers or DEBUG:
            break

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
