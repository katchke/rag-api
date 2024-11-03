import os

from openai import OpenAI
import psycopg2
import tiktoken

import utils


def create_db_cursor() -> tuple:
    # Database connection parameters
    DB_HOST = os.getenv("POSTGRES_HOST")
    DB_NAME = os.getenv("POSTGRES_DB")
    DB_USER = os.getenv("POSTGRES_USER")
    DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    TABLE_NAME = os.getenv("GSCHOLAR_TABLE")

    # Connect to the PostgreSQL database
    conn = psycopg2.connect(
        host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )
    cur = conn.cursor()

    cur.execute(
        f"SELECT title, link, authors, content, citation_count FROM {TABLE_NAME} ORDER BY citation_count DESC;"
    )

    return conn, cur


def fetch_papers(cur, chunksize: int, debug: bool) -> list[utils.ResearchPaper]:
    cur_ = cur.fetchmany(chunksize) if not debug else cur.fetchmany(5)

    return [
        utils.ResearchPaper(
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


def create_embeddings(papers: list[utils.ResearchPaper]) -> list[list[float]]:
    client = OpenAI()

    docs = [
        truncate_docs(f"{paper.title} {paper.authors} {paper.content}")
        for paper in papers
    ]

    resp = client.embeddings.create(
        model="text-embedding-3-small",
        input=docs,
        encoding_format="float",
    )

    embeds = [d["embedding"] for d in resp["data"]]

    return embeds


def update_papers(
    cur, papers: list[utils.ResearchPaper], embeds: list[list[float]]
) -> None:
    TABLE_NAME = os.getenv("GSCHOLAR_TABLE")

    for paper, embed in zip(papers, embeds):
        cur.execute(
            f"UPDATE {TABLE_NAME} SET embedding = %s WHERE link = %s",
            (embed, paper.link),
        )


def main():
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
