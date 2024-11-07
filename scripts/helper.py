import os

import psycopg2
import psycopg2.extras

import utils


class ResearchPaper:
    def __init__(
        self,
        title: str,
        link: str,
        citation_count: int,
        authors: str,
        content: str = "",
    ) -> None:
        """
        Initializes a new instance of the class.

        Args:
            title (str): The title of the article.
            link (str): The URL link to the article.
            citation_count (int): The number of citations the article has received.
            authors (list[str]): A list of authors of the article.
            content (str): The content of the article.
        """
        self.title = title
        self.link = link
        self.citation_count = citation_count
        self.authors = authors
        self.content = content


def insert_papers_to_db(papers: list[ResearchPaper]):
    # Connect to the PostgreSQL database
    conn = psycopg2.connect(utils.create_conn_string())
    cur = conn.cursor()

    TABLE_NAME = os.getenv("GSCHOLAR_TABLE")

    if not TABLE_NAME:
        raise ValueError("Table name not found in environment variables")

    # Insert scanned papers into the database
    insert_query = f"""
    INSERT INTO {TABLE_NAME} (title, link, citation_count, authors, content, chunk_num)
    VALUES %s;
    """

    # Prepare data for insertion
    data = []
    chunk_size = 1000

    for paper in papers:
        tokens = paper.content.split()
        chunks = [
            " ".join(tokens[i : i + chunk_size])
            for i in range(0, len(tokens), chunk_size)
        ]
        data.extend(
            [
                (paper.title, paper.link, paper.citation_count, paper.authors, chunk, i)
                for i, chunk in enumerate(chunks)
            ]
        )

    # Execute the insertion query and check if the commit was successful
    try:
        psycopg2.extras.execute_values(cur, insert_query, data)
        conn.commit()
        print("Commit successful")
    except Exception as e:
        conn.rollback()
        print(f"Commit failed: {e}")

    # Close the database connection
    cur.close()
    conn.close()
