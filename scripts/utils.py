from typing import Optional
import os

import psycopg2
import psycopg2.extras


class ResearchPaper:
    def __init__(
        self,
        title: str,
        link: str,
        citation_count: int,
        authors: str,
        content: Optional[str] = None,
    ) -> None:
        """
        Initializes a new instance of the class.

        Args:
            title (str): The title of the scholarly article.
            link (str): The URL link to the scholarly article.
            citation_count (int): The number of citations the article has received.
            authors (list[str]): A list of authors of the scholarly article.
        """
        self.title = title
        self.link = link
        self.citation_count = citation_count
        self.authors = authors
        self.content = content


def create_conn_string() -> str:
    return (
        "postgresql://"
        "%(POSTGRES_USER)s:%(POSTGRES_PASSWORD)s"
        "@%(POSTGRES_HOST)s:%(POSTGRES_PORT)s/"
        "%(POSTGRES_DB)s"
    ) % {
        "POSTGRES_HOST": os.getenv("POSTGRES_HOST"),
        "POSTGRES_PORT": 5432,
        "POSTGRES_DB": os.getenv("POSTGRES_DB"),
        "POSTGRES_USER": os.getenv("POSTGRES_USER"),
        "POSTGRES_PASSWORD": os.getenv("POSTGRES_PASSWORD"),
    }


def insert_papers_to_db(papers: list[ResearchPaper]):
    # Connect to the PostgreSQL database
    conn = psycopg2.connect(create_conn_string())
    cur = conn.cursor()

    TABLE_NAME = os.getenv("GSCHOLAR_TABLE")

    if not TABLE_NAME:
        raise ValueError("Table name not found in environment variables")

    # Insert scanned papers into the database
    insert_query = f"""
    INSERT INTO {TABLE_NAME} (title, link, citation_count, authors, content)
    VALUES %s;
    """

    # Prepare data for insertion
    data = [
        (paper.title, paper.link, paper.citation_count, paper.authors, paper.content)
        for paper in papers
    ]

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
