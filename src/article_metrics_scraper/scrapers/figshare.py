import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


_DOI = re.compile(r"^10\.6084/m9\.figshare\.(\d+)(?:\.v\d+)?$", re.IGNORECASE)


def _parse_total(payload, metric):
    value = payload.get("totals") if isinstance(payload, dict) else None
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"Figshare {metric} total must be a non-negative integer, got {value!r}")
    return value


def _parse_citations(payload):
    value = payload.get("cited_by_count") if isinstance(payload, dict) else None
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"OpenAlex cited_by_count must be a non-negative integer, got {value!r}")
    return value


def parse_metrics_payload(views_payload, downloads_payload, citations_payload):
    return {
        "views": _parse_total(views_payload, "views"),
        "downloads": _parse_total(downloads_payload, "downloads"),
        "citations": _parse_citations(citations_payload),
    }


def _fetch_json(url, provider):
    request = Request(
        url,
        headers={"User-Agent": "Article-Metrics-Scraper/1.0"},
    )
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError) as error:
        raise RuntimeError(f"Could not fetch {provider} metrics from {url}: {error}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"{provider} returned invalid JSON from {url}: {error}") from error


def scrape(article):
    doi = article.get("doi")
    match = _DOI.fullmatch(doi) if isinstance(doi, str) else None
    if not match:
        raise ValueError(f"Invalid Figshare DOI: {doi!r}")

    article_id = match.group(1)
    stats_url = f"https://stats.figshare.com/total/{{}}/article/{article_id}"
    doi_url = doi.split(".v", 1)[0]
    citations_url = f"https://api.openalex.org/works/https://doi.org/{doi_url}"
    views = _fetch_json(stats_url.format("views"), "Figshare")
    downloads = _fetch_json(stats_url.format("downloads"), "Figshare")
    citations = _fetch_json(citations_url, "OpenAlex")

    return {
        "source": "figshare",
        "metrics_provider": "figshare_stats_and_openalex",
        "doi": doi,
        "article_url": article.get("article_url", f"https://doi.org/{doi}"),
        **parse_metrics_payload(views, downloads, citations),
    }
