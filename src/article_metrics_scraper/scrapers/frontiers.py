import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


_DOI = re.compile(r"^10\.3389/[A-Za-z0-9-]+\.\d{4}\.(\d+)$", re.IGNORECASE)
_METRICS = {
    "totalCitations": "citations",
    "totalViews": "views",
    "totalDownloads": "downloads",
}


def parse_metrics_payload(payload, article_id):
    if not isinstance(payload, dict):
        raise ValueError("Frontiers metrics response must be an object")
    if payload.get("articleId") != article_id:
        raise ValueError(
            f"Frontiers metrics response article ID does not match {article_id}"
        )

    metrics = {}
    for source_key, metric in _METRICS.items():
        value = payload.get(source_key)
        if type(value) is not int or value < 0:
            raise ValueError(
                f"Frontiers {metric} count must be a non-negative integer"
            )
        metrics[metric] = value
    return metrics


def scrape(article):
    doi = article.get("doi")
    match = _DOI.fullmatch(doi) if isinstance(doi, str) else None
    if not match:
        raise ValueError(f"Invalid Frontiers DOI: {doi!r}")

    article_id = int(match.group(1))
    stats_url = (
        "https://impact-ui.frontiersin.org/api/articleTotals"
        f"?articleId={article_id}"
    )
    request = Request(
        stats_url,
        headers={
            "Accept": "application/json",
            "User-Agent": "Article-Metrics-Scraper/1.0",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError(
            f"Could not fetch Frontiers metrics for article {article_id}: {error}"
        ) from error

    article_url = f"https://doi.org/{doi}"
    return {
        "source": "frontiers",
        "doi": doi,
        "article_url": article_url,
        **parse_metrics_payload(payload, article_id),
    }
