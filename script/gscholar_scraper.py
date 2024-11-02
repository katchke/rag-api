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
        is_core: bool = False,
    ) -> None:
        self.title = title
        self.link = link
        self.citation_count = citation_count
        self.authors = authors
        self.is_core = is_core
        self.content: Optional[str] = None


class Scraper:
    @retrying.retry(
        wait_fixed=3000, stop_max_attempt_number=3, retry_on_result=lambda x: x is None
    )
    def _fetch_page(
        self, url: str, is_pdf: bool = False
    ) -> Optional[Union[str, io.BytesIO]]:
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
        self.papers = papers

    def _fetch_paper_content(self, paper: ResearchPaper) -> ResearchPaper:
        try:
            if paper.is_core:
                pass
            else:
                pdf_content = self._fetch_page(paper.link, is_pdf=True)
            reader = PyPDF2.PdfReader(pdf_content)  # type: ignore
            text = ""
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text()

            paper.content = text
        except:
            print(paper.link)

        return paper

    def scrape(self, max_processes: Optional[int]) -> list[ResearchPaper]:
        pool = mp.Pool(processes=max_processes or mp.cpu_count())
        papers = pool.imap_unordered(self._fetch_paper_content, self.papers)

        return list(papers)


class GScholarScraper(Scraper):
    def __init__(self, query: str, pages: int) -> None:
        self.query = query
        self.base_url = GSCHOLAR_URL
        self.pages = pages
        self.urls = self._generate_urls()

    def _generate_urls(self) -> list[str]:
        # Assuming that google scholar will usually 10 search results for every request
        urls = [
            self.base_url.format(start=10 * i, query=self.query)
            for i in range(self.pages)
        ]
        return urls

    def _fetch_papers(self, url: str) -> list[ResearchPaper]:
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
                is_core="core.ac.uk" in link,
            )
            for title, link, count, authors_ in zip(
                titles, links, citation_counts, authors
            )
        ]

    def scrape(self, max_processes: Optional[int]) -> list[ResearchPaper]:
        pool = mp.Pool(processes=max_processes or mp.cpu_count())
        papers = pool.imap_unordered(self._fetch_papers, self.urls)
        papers = list(
            itertools.chain.from_iterable([paper for paper in papers if paper])
        )
        return papers


def main():
    QUERY = "lithium+ion"
    PAGES = 2
    MAX_PROCESSES = 2

    QUERY = QUERY + "+site%3Aarxiv.org"
    gscholar_scraper = GScholarScraper(query=QUERY, pages=PAGES)
    papers = gscholar_scraper.scrape(max_processes=MAX_PROCESSES)

    paper_scraper = PaperScraper(papers)
    scanned_papers = paper_scraper.scrape(max_processes=MAX_PROCESSES)


if __name__ == "__main__":
    main()
