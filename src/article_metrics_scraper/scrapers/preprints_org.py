from html.parser import HTMLParser
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


_DOI = re.compile(r"^10\.20944/(preprints\d{6}\.\d+)\.v(\d+)$", re.IGNORECASE)


class _MetricsParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.metrics = {}
        self._row_depth = 0
        self._row_cells = []
        self._in_paragraph = False
        self._paragraph_parts = []

    def handle_starttag(self, tag, attrs):
        if self._row_depth:
            if tag == "div":
                self._row_depth += 1
            elif tag == "p":
                self._in_paragraph = True
                self._paragraph_parts = []
            return

        if tag == "div":
            classes = dict(attrs).get("class", "").split()
            if "flex" in classes and "justify-between" in classes and "py-sm" in classes:
                self._row_depth = 1
                self._row_cells = []

    def handle_data(self, data):
        if self._in_paragraph:
            self._paragraph_parts.append(data)

    def handle_endtag(self, tag):
        if self._row_depth == 0:
            return
        if tag == "p" and self._in_paragraph:
            self._row_cells.append(" ".join("".join(self._paragraph_parts).split()))
            self._in_paragraph = False
            self._paragraph_parts = []
        elif tag == "div":
            self._row_depth -= 1
            if self._row_depth == 0 and len(self._row_cells) >= 2:
                label = self._row_cells[0].casefold()
                if label in ("downloads", "views"):
                    self.metrics[label] = self._row_cells[1]


def parse_metrics_html(html):
    parser = _MetricsParser()
    parser.feed(html)
    metrics = {}
    for label in ("downloads", "views"):
        value = parser.metrics.get(label)
        if value is None:
            raise ValueError(f"Preprints.org metrics are missing the {label!r} count")
        normalized = value.replace(",", "").strip()
        if not normalized.isdigit():
            raise ValueError(f"Preprints.org {label} count is not a non-negative integer: {value!r}")
        metrics[label] = int(normalized)
    return metrics


def scrape(article):
    doi = article.get("doi")
    match = _DOI.fullmatch(doi) if isinstance(doi, str) else None
    if not match:
        raise ValueError(f"Invalid Preprints.org DOI: {doi!r}")

    article_url = f"https://www.preprints.org/manuscript/{match.group(1)}"
    request = Request(
        article_url,
        headers={"User-Agent": "Article-Metrics-Scraper/1.0"},
    )
    try:
        with urlopen(request, timeout=30) as response:
            html = response.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError, TimeoutError) as error:
        raise RuntimeError(f"Could not fetch Preprints.org metrics page {article_url}: {error}") from error

    return {
        "source": "preprints_org",
        "doi": doi,
        "version": int(match.group(2)),
        "article_url": article_url,
        **parse_metrics_html(html),
    }
