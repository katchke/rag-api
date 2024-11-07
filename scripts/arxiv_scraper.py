from typing import Optional, Union
import os
import re
import itertools
import time
import io
import multiprocessing as mp
import random

import requests
import bs4
import retrying
import PyPDF2

import helper


ARXIV_URL = "https://arxiv.org/search/?searchtype=all&query=lithium+ion+battery&abstracts=hide&size=200&order=&start={start}"
USER_AGENT_LIST = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
]


class Scraper:
    @retrying.retry(
        wait_fixed=3000, stop_max_attempt_number=3, retry_on_result=lambda x: x is None
    )
    def _fetch_page(
        self, url: str, is_pdf: bool = False
    ) -> Optional[Union[str, io.BytesIO]]:
        """
        Fetches the content of a web page or a PDF file from the given URL.

        Args:
            url (str): The URL of the web page or PDF file to fetch.
            is_pdf (bool, optional): If True, fetches the content as a PDF file. Defaults to False.

         Returns:
            Optional[Union[str, io.BytesIO]]: The content of the web page as a string if is_pdf is False,
                              otherwise the content as a BytesIO object.
        """

        headers = {
            "User-Agent": random.choice(USER_AGENT_LIST),
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip,deflate,br",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Connection": "keep-alive",
        }

        time.sleep(random.randint(10, 30) / 10)

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        return (
            response.content.decode("utf-8", "ignore")
            if not is_pdf
            else io.BytesIO(response.content)
        )


class PaperScraper(Scraper):
    def __init__(self, papers: list[helper.ResearchPaper]) -> None:
        """
        Initialize with a list of research papers.

        Args:
            papers (list[ResearchPaper]): A list of ResearchPaper objects to be processed.
        """
        super().__init__()

        self.papers = papers

    def _fetch_paper_content(self, paper: helper.ResearchPaper) -> helper.ResearchPaper:
        """
        Fetches the content of a research paper from its PDF link and updates the paper object with the extracted text.

        Args:
            paper (ResearchPaper): The research paper object containing the link to the PDF.

        Returns:
            ResearchPaper: The updated research paper object with the extracted text content.
        """
        pdf_content = self._fetch_page(paper.link, is_pdf=True)
        reader = PyPDF2.PdfReader(pdf_content)  # type: ignore
        text = ""
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text += page.extract_text()

        paper.content = text.replace("\x00", "\uFFFD")

        return paper

    def scrape(self, max_processes: Optional[int]) -> list[helper.ResearchPaper]:
        """
        Scrapes the content of research papers using multiprocessing.

        Args:
            max_processes (Optional[int]): The maximum number of processes to use for scraping.
                           If None, the number of processes will be set to the number of CPU cores.

        Returns:
            list[ResearchPaper]: A list of ResearchPaper objects containing the scraped content.
        """

        pool = mp.Pool(processes=max_processes or mp.cpu_count())
        papers = pool.imap_unordered(self._fetch_paper_content, self.papers)

        return list(papers)


class ArxivScraper(Scraper):
    def __init__(self, query: str, pages: int) -> None:
        """
        Initializes the ArxivScraper with a search query and number of pages to scrape.

        Args:
            query (str): The search query to use for scraping Arxiv.
            pages (int): The number of pages to scrape.
        """
        super().__init__()

        self.query = query
        self.base_url = ARXIV_URL
        self.pages = pages
        self.urls = self._generate_urls()

    def _generate_urls(self) -> list[str]:
        """
        Generates a list of URLs for Google Scholar search results based on the query and number of pages.

        Returns:
            list[str]: A list of URLs for the Google Scholar search results.
        """

        # Assuming that google scholar will usually 10 search results for every request
        urls = [
            self.base_url.format(start=200 * i, query=self.query)
            for i in range(self.pages)
        ]
        return urls

    def _fetch_papers(self, url: str) -> list[helper.ResearchPaper]:
        """
        Fetches research papers from the given URL.
        This method fetches the HTML content of the page at the specified URL,
        parses the HTML to extract research papers, and returns a list of
        ResearchPaper objects.

        Args:
            url (str): The URL of the page to fetch research papers from.

        Returns:
            list[ResearchPaper]: A list of ResearchPaper objects extracted from
            the HTML content of the page. If the HTML content could not be
            fetched or parsed, an empty list is returned.
        """

        html = self._fetch_page(url)

        if isinstance(html, str):
            papers = self._parse_html(html)
            return papers
        else:
            return []

    def __extract_titles(self, title: bs4.BeautifulSoup) -> str:
        return re.sub(r"\[.*?\]", "", title.text).strip()

    def __extract_links(self, link: bs4.BeautifulSoup) -> str:
        return link.a["href"] if link.a else None  # type: ignore

    def __extract_authors(self, authors: bs4.BeautifulSoup) -> str:
        return ", ".join(
            [
                author.strip()
                for author in authors.text.replace("Authors:", "").split(",")
            ]
        )

    def _parse_html(self, html: str) -> list[helper.ResearchPaper]:
        """
        Parses the provided HTML content and extracts research paper details.

        Args:
            html (str): The HTML content to parse.

        Returns:
            list[ResearchPaper]: A list of ResearchPaper objects containing the extracted details.
        """

        soup = bs4.BeautifulSoup(html, "html.parser")

        titles = list(map(self.__extract_titles, soup.find_all("p", class_="title")))
        links = list(
            map(
                self.__extract_links,
                [el.find("span") for el in soup.find_all("p", class_="list-title")],
            )
        )
        authors = list(
            map(
                self.__extract_authors,
                soup.find_all("p", class_="authors"),
            )
        )

        return [
            helper.ResearchPaper(
                title=title,
                link=link,
                authors=authors_,
            )
            for title, link, authors_ in zip(titles, links, authors)
            if link
        ]

    def scrape(self, max_processes: Optional[int]) -> list[helper.ResearchPaper]:
        """
        Scrapes Arxiv from the provided URLs using multiprocessing.

        Args:
            max_processes (Optional[int]): The maximum number of processes to use for scraping.
                           If None, the number of processes will be set to the number of CPU cores.

        Returns:
            list[ResearchPaper]: A list of ResearchPaper objects obtained from the scraping process.
        """
        pool = mp.Pool(processes=max_processes or mp.cpu_count())
        papers = pool.imap_unordered(self._fetch_papers, self.urls)
        papers = list(
            itertools.chain.from_iterable([paper for paper in papers if paper])
        )
        return papers


def main():
    if not os.getenv("RUN_SCRAPER"):
        print("Environment variable 'RUN_SCRAPER' is not set.")
        return
    elif os.environ["RUN_SCRAPER"].lower() != "true":
        print("Not running Google Scholar scraper.")
        print('Set the environment variable "RUN_SCRAPER=true" to run the scraper.')
        return

    print("Running Google Scholar scraper...")
    QUERY = "lithium+ion"  # Query to search
    PAGES = 4  # Number of pages to scrape
    MAX_PROCESSES = 1  # Number of processes to use for scraping

    DB_INSERT_CHUNK = 100

    # Scrape papers metadata from google scholar
    print(f"Query: {QUERY}, Pages: {PAGES}")
    arxiv_scraper = ArxivScraper(query=QUERY, pages=PAGES)
    papers = arxiv_scraper.scrape(max_processes=MAX_PROCESSES)
    print(f"Done fetching paper metadata. Found {len(papers)} papers.")

    # Scrape content of papers
    print("Scraping paper content...")

    for i in range(0, len(papers), DB_INSERT_CHUNK):
        paper_scraper = PaperScraper(papers[i : i + DB_INSERT_CHUNK])
        scanned_papers = paper_scraper.scrape(max_processes=MAX_PROCESSES)
        helper.insert_papers_to_db(scanned_papers)


if __name__ == "__main__":
    main()
