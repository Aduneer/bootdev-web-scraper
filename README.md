# Boot.dev Web Scraper

A command line web scraper that follows links on one website and extracts each visited HTML page's heading, first paragraph, outgoing links, and image URLs. It writes the results to a JSON report. Requests run concurrently with `aiohttp`, and Beautiful Soup parses the HTML.

I built this project for Boot.dev's [Build a Web Scraper in Python](https://www.boot.dev/courses/build-web-scraper-python) course.

## Requirements

- Python 3.13 or newer
- [uv](https://docs.astral.sh/uv/)

## Run

From the project directory:

```bash
uv run main.py https://example.com 5 25
```

The arguments are the starting URL, maximum number of simultaneous requests, and maximum number of pages to visit. Both limits must be positive integers. The URL must start with `http://` or `https://`.

The crawler follows links on the starting hostname, including links to subpaths, and skips links to other hostnames. It writes `report.json` in the current directory, replacing an existing report. The report contains one object per successfully fetched HTML page, sorted by URL:

```json
[
  {
    "url": "https://example.com/",
    "heading": "Example Domain",
    "first_paragraph": "Example text",
    "outgoing_links": ["https://example.com/about"],
    "image_urls": ["https://example.com/logo.png"]
  }
]
```

Failed requests and non-HTML responses are printed to the terminal and omitted from the report. The page limit counts attempted page visits, so the report can contain fewer pages than the limit. The tool does not check `robots.txt` or pause between requests; use modest limits and check the target site's crawling rules and terms before running it.

## Project files

- `main.py`: command line entry point
- `crawl.py`: URL handling, HTML extraction, and concurrent crawl
- `json_report.py`: JSON output
- `test_crawl.py`: extraction and URL normalization checks

## License

MIT License. See [LICENSE](LICENSE).
