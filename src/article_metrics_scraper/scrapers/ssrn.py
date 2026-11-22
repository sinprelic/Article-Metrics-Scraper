from html.parser import HTMLParser
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


_DOI = re.compile(r"^10\.2139/ssrn\.(\d+)$", re.IGNORECASE)


class _StatisticsParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.statistics = {}
        self._capture_class = None
        self._capture_parts = []
        self._label = None

    def handle_starttag(self, tag, attrs):
        if tag != "div":
            return
        classes = dict(attrs).get("class", "").split()
        if "lbl" in classes:
            self._capture_class = "label"
            self._capture_parts = []
        elif "number" in classes:
            self._capture_class = "number"
            self._capture_parts = []

    def handle_data(self, data):
        if self._capture_class:
            self._capture_parts.append(data)

    def handle_endtag(self, tag):
        if tag != "div" or not self._capture_class:
            return
        value = " ".join("".join(self._capture_parts).split())
        if self._capture_class == "label":
            self._label = value.casefold()
        elif self._label:
            self.statistics[self._label] = value
            self._label = None
        self._capture_class = None
        self._capture_parts = []


def parse_metrics_html(html):
    parser = _StatisticsParser()
    parser.feed(html)
    metrics = {}
    for label, key in (("downloads", "downloads"), ("abstract views", "abstract_views")):
        value = parser.statistics.get(label)
        if value is None:
            raise ValueError(f"SSRN statistics are missing the {label!r} count")
        normalized = value.replace(",", "").strip()
        if not normalized.isdigit():
            raise ValueError(f"SSRN {label} count is not a non-negative integer: {value!r}")
        metrics[key] = int(normalized)
    return metrics


def scrape(article):
    doi = article.get("doi")
    match = _DOI.fullmatch(doi) if isinstance(doi, str) else None
    if not match:
        raise ValueError(f"Invalid SSRN DOI: {doi!r}")

    paper_id = match.group(1)
    article_url = f"https://papers.ssrn.com/sol3/papers.cfm?abstract_id={paper_id}"
    request = Request(
        article_url,
        headers={"User-Agent": "Article-Metrics-Scraper/1.0"},
    )
    try:
        with urlopen(request, timeout=30) as response:
            html = response.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError, TimeoutError) as error:
        raise RuntimeError(f"Could not fetch SSRN metrics page {article_url}: {error}") from error

    return {
        "source": "ssrn",
        "doi": doi,
        "article_url": article_url,
        **parse_metrics_html(html),
    }
