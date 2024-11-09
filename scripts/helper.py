"""
This script provides a helper class and function to manage research papers and insert them into a PostgreSQL database.

Classes:
    ResearchPaper: A class representing a research paper with attributes such as title, link, 
    authors, content, and chunk number.

Functions:
    insert_papers_to_db(papers: list[ResearchPaper]): Connects to a PostgreSQL database and 
    inserts a list of ResearchPaper instances into a specified table.

"""

from typing import Optional
import os

import psycopg2
import psycopg2.extras

import utils


class ResearchPaper:
    def __init__(
        self,
        title: str,
        link: str,
        authors: str,
        content: str = "",
        chunk_num: Optional[int] = None,
    ) -> None:
        """
        Initializes a new instance of the class.

        Args:
            title (str): The title of the article.
            link (str): The URL link to the article.
            authors (list[str]): A list of authors of the article.
            content (str): The content of the article.
            chunk_num (int, optional): The chunk number of the content.
        """
        self.title = title
        self.link = link
        self.authors = authors
        self.content = content
        self.chunk_num = chunk_num


def insert_papers_to_db(papers: list[ResearchPaper]):
    """
    Inserts a list of ResearchPaper instances into a PostgreSQL database.
    """
    conn = psycopg2.connect(utils.create_conn_string())
    cur = conn.cursor()

    TABLE_NAME = os.getenv("ARXIV_TABLE")

    if not TABLE_NAME:
        raise ValueError("Table name not found in environment variables")

    # Insert scanned papers into the database
    insert_query = f"""
    INSERT INTO {TABLE_NAME} (title, link, authors, content, chunk_num)
    VALUES %s ON CONFLICT (link, chunk_num) DO NOTHING;
    """

    # Prepare data for insertion
    data = []
    chunk_size = (
        1000  # Split content into chunks of 1000 words for better embedding quality
    )

    for paper in papers:
        tokens = paper.content.split()
        chunks = [
            " ".join(tokens[i : i + chunk_size])
            .encode("utf-8", "replace")
            .decode("utf-8")
            for i in range(0, len(tokens), chunk_size)
        ]
        data.extend(
            [
                (paper.title, paper.link, paper.authors, chunk, i)
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
