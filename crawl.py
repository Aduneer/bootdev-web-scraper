import asyncio
import posixpath
from typing import TypedDict
from urllib.parse import urljoin, urlsplit

import aiohttp
from bs4 import BeautifulSoup, Tag


def normalize_url(url):
    parts = urlsplit(url)
    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower()

    if scheme == 'http' and netloc.endswith(':80'):
        netloc = netloc[:-3]
    elif scheme == 'https' and netloc.endswith(':443'):
        netloc = netloc[:-4]

    path = posixpath.normpath(parts.path)
    if path == '.':
        path = ''

    return f"{netloc}{path}"


def is_same_domain(base_url: str, candidate_url: str) -> bool:
    base_host = (urlsplit(base_url).hostname or "").lower()
    candidate_host = (urlsplit(candidate_url).hostname or "").lower()
    return bool(base_host) and candidate_host == base_host


def get_heading_from_html(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    heading = soup.find('h1')
    if not isinstance(heading, Tag):
        heading = soup.find('h2')
    return heading.get_text(strip=True) if isinstance(heading, Tag) else ""


def get_first_paragraph_from_html(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    main = soup.find('main')
    paragraph = main.find('p') if isinstance(main, Tag) else soup.find('p')
    return paragraph.get_text(strip=True) if isinstance(paragraph, Tag) else ""


def get_urls_from_html(html, base_url):
    soup = BeautifulSoup(html, 'html.parser')
    return [
        urljoin(base_url, anchor.get('href'))
        for anchor in soup.find_all('a', href=True)
        if anchor.get('href')
    ]


def get_images_from_html(html, base_url):
    soup = BeautifulSoup(html, 'html.parser')
    return [
        urljoin(base_url, image.get('src'))
        for image in soup.find_all('img', src=True)
        if image.get('src')
    ]


class PageData(TypedDict):
    url: str
    heading: str
    first_paragraph: str
    outgoing_links: list[str]
    image_urls: list[str]


def extract_page_data(html: str, page_url: str) -> PageData:
    return PageData(
        url=page_url,
        heading=get_heading_from_html(html),
        first_paragraph=get_first_paragraph_from_html(html),
        outgoing_links=get_urls_from_html(html, page_url),
        image_urls=get_images_from_html(html, page_url),
    )


class AsyncCrawler:
    def __init__(
        self, base_url: str, max_concurrency: int = 10, max_pages: int = 1000
    ):
        self.base_url = base_url
        self.page_data = {}
        self.visited = set()
        self.lock = asyncio.Lock()
        self.max_concurrency = max_concurrency
        self.max_pages = max_pages
        self.should_stop = False
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def add_page_visit(self, normalized_url: str) -> bool:
        async with self.lock:
            if self.should_stop:
                return False
            if normalized_url in self.visited:
                return False
            if len(self.visited) >= self.max_pages:
                self.should_stop = True
                print("Reached maximum number of pages to crawl.")
                return False
            self.visited.add(normalized_url)
            return True

    async def get_html(self, url: str) -> str:
        async with self.session.get(
            url, headers={"User-Agent": "BootCrawler/1.0"}
        ) as response:
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "")
            media_type = content_type.split(";", 1)[0].strip().lower()
            if media_type != "text/html":
                raise ValueError(
                    f"Expected text/html response, got {content_type or 'no Content-Type header'}"
                )
            return await response.text()

    async def crawl_page(self, current_url: str):
        if self.should_stop:
            return
        if not is_same_domain(self.base_url, current_url):
            return

        normalized_url = normalize_url(current_url)
        if not await self.add_page_visit(normalized_url):
            return

        print(f"Crawling {current_url}")
        try:
            async with self.semaphore:
                html = await self.get_html(current_url)
        except Exception as e:
            print(f"Failed to fetch {current_url}: {e}")
            return

        data = extract_page_data(html, current_url)
        async with self.lock:
            self.page_data[normalized_url] = data

        tasks = []
        for link in dict.fromkeys(data["outgoing_links"]):
            if self.should_stop:
                break
            if is_same_domain(self.base_url, link):
                tasks.append(asyncio.create_task(self.crawl_page(link)))
        await asyncio.gather(*tasks)

    async def crawl(self):
        await self.crawl_page(self.base_url)
        return self.page_data


async def crawl_site_async(base_url: str, max_concurrency: int = 10, max_pages: int = 1000):
    async with AsyncCrawler(base_url, max_concurrency, max_pages) as crawler:
        return await crawler.crawl()
