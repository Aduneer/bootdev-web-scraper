import unittest

from crawl import (
    get_first_paragraph_from_html,
    get_heading_from_html,
    get_images_from_html,
    get_urls_from_html,
    normalize_url, extract_page_data,
)


class TestCrawl(unittest.TestCase):
    def test_normalize_url(self):
        input_url = "https://www.boot.dev/blog/path"
        actual = normalize_url(input_url)
        expected = "www.boot.dev/blog/path"
        self.assertEqual(actual, expected)


    def test_normalize_url_with_trailing_slash(self):
        input_url = "https://www.boot.dev/blog/path/"
        actual = normalize_url(input_url)
        expected = "www.boot.dev/blog/path"
        self.assertEqual(actual, expected)

    def test_normalize_url_with_default_port(self):
        input_url = "https://www.boot.dev:443/blog/path"
        actual = normalize_url(input_url)
        expected = "www.boot.dev/blog/path"
        self.assertEqual(actual, expected)

    def test_get_heading_from_html_basic(self):
        input_body = "<html><body><h1>Test Title</h1></body></html>"
        actual = get_heading_from_html(input_body)
        expected = "Test Title"
        self.assertEqual(actual, expected)

    def test_get_heading_from_html_h2_fallback(self):
        input_body = "<html><body><h2>Fallback Title</h2></body></html>"
        self.assertEqual(get_heading_from_html(input_body), "Fallback Title")

    def test_get_heading_from_html_prefers_h1(self):
        input_body = "<h2>Earlier h2</h2><h1>Main title</h1>"
        self.assertEqual(get_heading_from_html(input_body), "Main title")

    def test_get_heading_from_html_missing(self):
        self.assertEqual(get_heading_from_html("<p>No heading</p>"), "")


    def test_get_first_paragraph_from_html_main_priority(self):
        input_body = """<html><body>
            <p>Outside paragraph.</p>
            <main>
                <p>Main paragraph.</p>
            </main>
        </body></html>"""
        actual = get_first_paragraph_from_html(input_body)
        expected = "Main paragraph."
        self.assertEqual(actual, expected)

    def test_get_first_paragraph_from_html_fallback(self):
        input_body = "<html><body><p>First paragraph.</p><p>Second paragraph.</p></body></html>"
        self.assertEqual(get_first_paragraph_from_html(input_body), "First paragraph.")

    def test_get_first_paragraph_from_html_missing(self):
        self.assertEqual(get_first_paragraph_from_html("<html><body><main>No paragraph</main></body></html>"), "")

    def test_get_urls_from_html_absolute(self):
        input_url = "https://crawler-test.com"
        input_body = '<html><body><a href="https://crawler-test.com"><span>Boot.dev</span></a></body></html>'
        actual = get_urls_from_html(input_body, input_url)
        expected = ["https://crawler-test.com"]
        self.assertEqual(actual, expected)

    def test_get_urls_from_html_relative(self):
        actual = get_urls_from_html(
            '<a href="/about">About</a><a href="articles/1">Article</a>',
            "https://crawler-test.com/blog/",
        )
        self.assertEqual(actual, [
            "https://crawler-test.com/about",
            "https://crawler-test.com/blog/articles/1",
        ])

    def test_get_urls_from_html_finds_all_links_and_skips_missing_href(self):
        actual = get_urls_from_html(
            '<a href="/one">One</a><a>Missing</a><div><a href="/two">Two</a></div>',
            "https://crawler-test.com",
        )
        self.assertEqual(actual, ["https://crawler-test.com/one", "https://crawler-test.com/two"])

    def test_get_images_from_html_relative(self):
        input_url = "https://crawler-test.com"
        input_body = '<html><body><img src="/logo.png" alt="Logo"></body></html>'
        actual = get_images_from_html(input_body, input_url)
        expected = ["https://crawler-test.com/logo.png"]
        self.assertEqual(actual, expected)

    def test_get_images_from_html_absolute_and_relative(self):
        actual = get_images_from_html(
            '<img src="https://cdn.example.com/a.png"><img src="/b.png">',
            "https://crawler-test.com",
        )
        self.assertEqual(actual, ["https://cdn.example.com/a.png", "https://crawler-test.com/b.png"])

    def test_get_images_from_html_skips_missing_or_empty_src(self):
        actual = get_images_from_html(
            '<img alt="missing"><img src=""><img src="/present.png">',
            "https://crawler-test.com",
        )
        self.assertEqual(actual, ["https://crawler-test.com/present.png"])

    def test_extract_page_data_basic(self):
        input_url = "https://crawler-test.com"
        input_body = """<html><body>
            <h1>Test Title</h1>
            <p>This is the first paragraph.</p>
            <a href="/link1">Link 1</a>
            <img src="/image1.jpg" alt="Image 1">
        </body></html>"""
        actual = extract_page_data(input_body, input_url)
        expected = {
            "url": "https://crawler-test.com",
            "heading": "Test Title",
            "first_paragraph": "This is the first paragraph.",
            "outgoing_links": ["https://crawler-test.com/link1"],
            "image_urls": ["https://crawler-test.com/image1.jpg"],
        }
        self.assertEqual(actual, expected)

if __name__ == "__main__":
    unittest.main()
