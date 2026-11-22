from html.parser import HTMLParser
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


_MONTH_ROW = re.compile(r"^[A-Za-z]{3}\s+\d{4}$")
_DOI = re.compile(r"^10\.1101/[A-Za-z0-9._/-]+$")


class _MetricsTableParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows = []
        self._in_table = False
        self._in_row = False
        self._cell_tag = None
        self._cell_parts = []
        self._row = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "table" and not self._in_table:
            classes = attributes.get("class", "").split()
            self._in_table = "highwire-stats" in classes
        elif self._in_table and tag == "tr":
            self._in_row = True
            self._row = []
        elif self._in_table and self._in_row and tag in ("th", "td"):
            self._cell_tag = tag
            self._cell_parts = []

    def handle_data(self, data):
        if self._cell_tag is not None:
            self._cell_parts.append(data)

    def handle_endtag(self, tag):
        if self._in_table and self._cell_tag == tag:
            self._row.append(" ".join("".join(self._cell_parts).split()))
            self._cell_tag = None
            self._cell_parts = []
        elif self._in_table and tag == "tr" and self._in_row:
            if self._row:
                self.rows.append(self._row)
            self._in_row = False
        elif tag == "table" and self._in_table:
            self._in_table = False


def parse_metrics_html(html):
    parser = _MetricsTableParser()
    parser.feed(html)
    if not parser.rows:
        raise ValueError("bioRxiv metrics table was not found")

    headers = [cell.casefold() for cell in parser.rows[0]]
    columns = {}
    for metric, names in {
        "abstract_views": ("abstract",),
        "full_text_views": ("full", "full-text html", "html"),
        "pdf_downloads": ("pdf",),
    }.items():
        column = next((i for i, header in enumerate(headers) if header in names), None)
        if column is None:
            raise ValueError(f"bioRxiv metrics table is missing the {metric} column")
        columns[metric] = column

    totals = {metric: 0 for metric in columns}
    monthly_rows = 0
    for row in parser.rows[1:]:
        if not row or not _MONTH_ROW.fullmatch(row[0]):
            continue
        monthly_rows += 1
        for metric, column in columns.items():
            if column >= len(row):
                raise ValueError(f"bioRxiv usage row is missing the {metric} value")
            value = row[column].replace(",", "").strip()
            if not value.isdigit():
                raise ValueError(
                    f"bioRxiv usage value for {metric} is not a non-negative integer: {row[column]!r}"
                )
            totals[metric] += int(value)

    if monthly_rows == 0:
        raise ValueError("bioRxiv metrics table contains no monthly usage rows")
    return totals


def scrape(article):
    doi = article.get("doi")
    version = article.get("version")
    if not isinstance(doi, str) or not _DOI.fullmatch(doi):
        raise ValueError(f"Invalid bioRxiv DOI: {doi!r}")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        raise ValueError(f"Invalid bioRxiv version: {version!r}")

    article_url = f"https://www.biorxiv.org/content/{doi}v{version}"
    metrics_url = f"{article_url}.article-metrics"
    request = Request(
        metrics_url,
        headers={"User-Agent": "Article-Metrics-Scraper/1.0"},
    )
    try:
        with urlopen(request, timeout=30) as response:
            html = response.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError, TimeoutError) as error:
        raise RuntimeError(f"Could not fetch bioRxiv metrics page {metrics_url}: {error}") from error

    return {
        "source": "biorxiv",
        "doi": doi,
        "version": version,
        "article_url": article_url,
        **parse_metrics_html(html),
    }
