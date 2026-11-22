from html.parser import HTMLParser
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


_DOI = re.compile(r"^10\.17617/3\.[A-Z0-9]+$", re.IGNORECASE)
_DOWNLOADS = re.compile(r"\b([0-9][0-9,]*)\s+Downloads\b", re.IGNORECASE)
_VALID_COUNT = re.compile(r"(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)$")


class _DatasetMetricsParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._metrics_body_depth = 0
        self._text = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "div":
            if self._metrics_body_depth:
                self._metrics_body_depth += 1
            elif attributes.get("id") == "metrics-body":
                self._metrics_body_depth = 1

    def handle_data(self, data):
        if self._metrics_body_depth:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag == "div" and self._metrics_body_depth:
            self._metrics_body_depth -= 1


def parse_metrics_html(html):
    if "making sure you're not a bot" in html.casefold():
        raise RuntimeError("EDMOND returned an anti-bot challenge instead of the dataset page")

    parser = _DatasetMetricsParser()
    parser.feed(html)
    metrics_text = " ".join(" ".join(parser._text).split())
    if not metrics_text:
        raise ValueError("EDMOND Dataset Metrics section was not found")

    matches = _DOWNLOADS.findall(metrics_text)
    if len(matches) != 1:
        raise ValueError(
            f"Expected one aggregate downloads count in EDMOND Dataset Metrics, found {len(matches)}"
        )
    count = matches[0]
    if not _VALID_COUNT.fullmatch(count):
        raise ValueError(f"EDMOND downloads count is not a non-negative integer: {count!r}")
    return {"downloads": int(count.replace(",", ""))}


def scrape(article):
    doi = article.get("doi")
    if not isinstance(doi, str) or not _DOI.fullmatch(doi):
        raise ValueError(f"Invalid EDMOND DOI: {doi!r}")

    query = urlencode({"persistentId": f"doi:{doi}"})
    article_url = f"https://edmond.mpg.de/dataset.xhtml?{query}"
    request = Request(
        article_url,
        headers={"User-Agent": "Article-Metrics-Scraper/1.0"},
    )
    try:
        with urlopen(request, timeout=30) as response:
            html = response.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError, TimeoutError) as error:
        raise RuntimeError(f"Could not fetch EDMOND dataset page {article_url}: {error}") from error

    return {
        "source": "edmond",
        "doi": doi,
        "article_url": article_url,
        **parse_metrics_html(html),
    }
