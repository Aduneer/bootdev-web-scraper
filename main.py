import asyncio
import sys
from urllib.parse import urlsplit

from crawl import crawl_site_async
from json_report import write_json_report


async def main():
    if len(sys.argv) != 4:
        print("usage: uv run main.py URL max_concurrency max_pages", file=sys.stderr)
        sys.exit(1)
    url = sys.argv[1]
    try:
        parsed_url = urlsplit(url)
    except ValueError:
        print("URL must be an absolute http:// or https:// URL", file=sys.stderr)
        sys.exit(1)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.hostname:
        print("URL must be an absolute http:// or https:// URL", file=sys.stderr)
        sys.exit(1)
    try:
        max_concurrency = int(sys.argv[2])
        max_pages = int(sys.argv[3])
        if max_concurrency < 1 or max_pages < 1:
            raise ValueError
    except ValueError:
        print("max_concurrency and max_pages must be positive integers", file=sys.stderr)
        sys.exit(1)

    print(f"starting crawl {url}")
    page_data = await crawl_site_async(url, max_concurrency, max_pages)
    write_json_report(page_data)


if __name__ == "__main__":
    asyncio.run(main())
