from typing import Optional, Union
import re
import itertools
import time
import io
import multiprocessing as mp

import requests
import bs4
import retrying
import PyPDF2

GSCHOLAR_URL = (
    "https://scholar.google.com/scholar?start={start}&q={query}&hl=en&as_sdt=0,5"
)


class ResearchPaper:
    def __init__(
        self,
        title: str,
        link: str,
        citation_count: int,
        authors: list[str],
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
        self.content: Optional[str] = None


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

        time.sleep(0.2)

        response = requests.get(url)
        response.raise_for_status()
        return (
            response.content.decode("utf-8", "ignore")
            if not is_pdf
            else io.BytesIO(response.content)
        )


class PaperScraper(Scraper):
    def __init__(self, papers: list[ResearchPaper]) -> None:
        """
        Initializes the GScholarScraper with a list of research papers.

        Args:
            papers (list[ResearchPaper]): A list of ResearchPaper objects to be processed.
        """

        self.papers = papers

    def _fetch_paper_content(self, paper: ResearchPaper) -> ResearchPaper:
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

        paper.content = text

        return paper

    def scrape(self, max_processes: Optional[int]) -> list[ResearchPaper]:
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


class GScholarScraper(Scraper):
    def __init__(self, query: str, pages: int) -> None:
        """
        Initializes the GScholarScraper with a search query and number of pages to scrape.

        Args:
            query (str): The search query to use for scraping Google Scholar.
            pages (int): The number of pages to scrape.
        """

        self.query = query
        self.base_url = GSCHOLAR_URL
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
            self.base_url.format(start=10 * i, query=self.query)
            for i in range(self.pages)
        ]
        return urls

    def _fetch_papers(self, url: str) -> list[ResearchPaper]:
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
        return link.a["href"]  # type: ignore

    def __extract_citation_counts(self, citation: bs4.BeautifulSoup) -> int:
        try:
            count_el = [el for el in citation.find_all("a") if "Cited by" in el.text]
            return int(count_el[0].text.split()[-1]) if count_el else 0
        except IndexError:
            # Not all papers have citation counts
            return 0

    def __extract_authors(self, author: bs4.BeautifulSoup) -> list[str]:
        return author.text.split("-")[0].split(",")

    def _parse_html(self, html: str) -> list[ResearchPaper]:
        """
        Parses the provided HTML content and extracts research paper details.

        Args:
            html (str): The HTML content to parse.

        Returns:
            list[ResearchPaper]: A list of ResearchPaper objects containing the extracted details.
        """

        soup = bs4.BeautifulSoup(html, "html.parser")

        titles = list(map(self.__extract_titles, soup.find_all("h3", class_="gs_rt")))
        links = list(map(self.__extract_links, soup.find_all("div", class_="gs_ggsd")))
        citation_counts = list(
            map(self.__extract_citation_counts, soup.find_all("div", class_="gs_flb"))
        )
        authors = list(map(self.__extract_authors, soup.find_all("div", class_="gs_a")))

        return [
            ResearchPaper(
                title=title,
                link=link,
                authors=authors_,
                citation_count=count,
            )
            for title, link, count, authors_ in zip(
                titles, links, citation_counts, authors
            )
        ]

    def scrape(self, max_processes: Optional[int]) -> list[ResearchPaper]:
        """
        Scrapes Google Scholar from the provided URLs using multiprocessing.

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
    QUERY = "lithium+ion"  # Query to search
    PAGES = 2  # Number of pages to scrape
    MAX_PROCESSES = 2  # Number of processes to use for scraping

    QUERY = QUERY + "+site%3Aarxiv.org"  # Search only on arxiv

    # Scrape papers metadata from google scholar
    gscholar_scraper = GScholarScraper(query=QUERY, pages=PAGES)
    papers = gscholar_scraper.scrape(max_processes=MAX_PROCESSES)

    # Scrape content of papers
    paper_scraper = PaperScraper(papers)
    scanned_papers = paper_scraper.scrape(max_processes=MAX_PROCESSES)


if __name__ == "__main__":
    main()
