from html.parser import HTMLParser
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


_DOI = re.compile(r"^10\.3390/[A-Za-z0-9._/-]+$", re.IGNORECASE)
_ARTICLE_VIEWS = re.compile(r"^article\s+views\s*:?\s*(\d+(?:,\d{3})*)$", re.IGNORECASE)
_COUNT = re.compile(r"^(?:\d+|\d{1,3}(?:,\d{3})+)$")
_OTHER_METRIC_LABEL = re.compile(
    r"^(?:downloads?|citations?|abstract views?|pdf downloads?)\s*:?\s*$",
    re.IGNORECASE,
)


class _ArticleViewsParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text_chunks = []
        self._ignored_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._ignored_depth += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data):
        if self._ignored_depth:
            return
        value = " ".join(data.split())
        if value:
            self.text_chunks.append(value)


def parse_metrics_html(html):
    parser = _ArticleViewsParser()
    parser.feed(html)

    for index, chunk in enumerate(parser.text_chunks):
        match = _ARTICLE_VIEWS.fullmatch(chunk)
        if match:
            count = match.group(1)
            if not _COUNT.fullmatch(count):
                raise ValueError(f"MDPI Article views count is invalid: {count!r}")
            return {"article_views": int(count.replace(",", ""))}

        if chunk.casefold().rstrip(":") != "article views":
            continue
        for value in parser.text_chunks[index + 1:index + 6]:
            if _OTHER_METRIC_LABEL.fullmatch(value):
                break
            if _COUNT.fullmatch(value):
                return {"article_views": int(value.replace(",", ""))}

    raise ValueError("MDPI Article views count was not found")


def scrape(article):
    doi = article.get("doi")
    if not isinstance(doi, str) or not _DOI.fullmatch(doi):
        raise ValueError(f"Invalid MDPI DOI: {doi!r}")

    article_url = f"https://doi.org/{doi}"
    request = Request(
        article_url,
        headers={"User-Agent": "Article-Metrics-Scraper/1.0"},
    )
    try:
        with urlopen(request, timeout=30) as response:
            html = response.read().decode("utf-8", errors="replace")
            resolved_url = response.geturl()
    except (HTTPError, URLError, TimeoutError) as error:
        raise RuntimeError(f"Could not fetch MDPI metrics page {article_url}: {error}") from error

    return {
        "source": "mdpi",
        "doi": doi,
        "article_url": resolved_url,
        **parse_metrics_html(html),
    }
