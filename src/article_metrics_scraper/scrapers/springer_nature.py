from html.parser import HTMLParser
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


_DOI = re.compile(r"^10\.1007/[A-Za-z0-9._/-]+$", re.IGNORECASE)
_METRICS = {
    "access-count": ("accesses", "Accesses"),
    "citation-count": ("citations", "Citations"),
}
_COUNT = re.compile(r"(?<![\d,])([0-9][0-9,]*)(?![\d,])")
_VALID_COUNT = re.compile(r"(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)$")


class _ArticleMetricsParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.metric_text = {selector: [] for selector in _METRICS}
        self._active_selector = None

    def handle_starttag(self, tag, attrs):
        if tag == "li":
            selector = dict(attrs).get("data-test")
            if selector in self.metric_text:
                self._active_selector = selector

    def handle_data(self, data):
        if self._active_selector is not None:
            self.metric_text[self._active_selector].append(data)

    def handle_endtag(self, tag):
        if tag == "li" and self._active_selector is not None:
            self._active_selector = None


def parse_metrics_html(html):
    lowered_html = html.casefold()
    if "client challenge" in lowered_html or "_fs-ch-" in lowered_html:
        raise RuntimeError(
            "Springer Nature returned a client challenge; automated access is unavailable"
        )

    parser = _ArticleMetricsParser()
    parser.feed(html)

    metrics = {}
    for selector, (metric, label) in _METRICS.items():
        text = " ".join(" ".join(parser.metric_text[selector]).split())
        if label.casefold() not in text.casefold():
            raise ValueError(f"Springer Nature metrics bar is missing the {label} count")
        matches = _COUNT.findall(text)
        if len(matches) != 1 or not _VALID_COUNT.fullmatch(matches[0]):
            raise ValueError(
                f"Springer Nature {label.lower()} count is not a non-negative integer: {text!r}"
            )
        metrics[metric] = int(matches[0].replace(",", ""))
    return metrics


def scrape(article):
    doi = article.get("doi")
    if not isinstance(doi, str) or not _DOI.fullmatch(doi):
        raise ValueError(f"Invalid Springer Nature DOI: {doi!r}")

    article_url = f"https://link.springer.com/article/{doi}"
    request = Request(
        article_url,
        headers={"User-Agent": "Article-Metrics-Scraper/1.0"},
    )
    try:
        with urlopen(request, timeout=30) as response:
            html = response.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError, TimeoutError) as error:
        raise RuntimeError(
            f"Could not fetch Springer Nature article page {article_url}: {error}"
        ) from error

    return {
        "source": "springer_nature",
        "doi": doi,
        "article_url": article_url,
        **parse_metrics_html(html),
    }
