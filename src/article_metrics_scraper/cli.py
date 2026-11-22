import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
import sys
from urllib.error import URLError
from urllib.request import HTTPError

from .scrapers import biorxiv, edmond, figshare, mdpi, preprints_org, springer_nature, ssrn


_SCRAPERS = {
    "biorxiv": biorxiv.scrape,
    "edmond": edmond.scrape,
    "figshare": figshare.scrape,
    "mdpi": mdpi.scrape,
    "preprints_org": preprints_org.scrape,
    "springer_nature": springer_nature.scrape,
    "ssrn": ssrn.scrape,
}
_ARTICLE_ID = re.compile(r"^[a-z0-9_]+$")


def _load_articles(config_path):
    with config_path.open(encoding="utf-8") as file:
        config = json.load(file)
    articles = config.get("articles") if isinstance(config, dict) else None
    if not isinstance(articles, list) or not articles:
        raise ValueError("Configuration must contain a non-empty 'articles' list")

    identifiers = set()
    for article in articles:
        if not isinstance(article, dict):
            raise ValueError("Each configured article must be an object")
        article_id = article.get("id")
        if not isinstance(article_id, str) or not _ARTICLE_ID.fullmatch(article_id):
            raise ValueError(f"Invalid article id: {article_id!r}; use lowercase letters, digits, and underscores")
        if article_id in identifiers:
            raise ValueError(f"Duplicate article id: {article_id}")
        identifiers.add(article_id)
        if article.get("source") not in _SCRAPERS:
            raise ValueError(f"Unsupported scraper source for {article_id}: {article.get('source')!r}")
    return articles


def _is_due(output_path, interval_hours, now):
    if not output_path.exists():
        return True
    with output_path.open(encoding="utf-8") as file:
        existing = json.load(file)
    generated_at = existing.get("generated_at") if isinstance(existing, dict) else None
    if not isinstance(generated_at, str):
        raise ValueError(f"{output_path} has no valid generated_at timestamp")
    timestamp = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
    if timestamp.tzinfo is None:
        raise ValueError(f"{output_path} generated_at timestamp must include a timezone")
    return now - timestamp >= timedelta(hours=interval_hours)


def _load_previous_results(output_path):
    if not output_path.exists():
        return {}
    with output_path.open(encoding="utf-8") as file:
        existing = json.load(file)
    results = existing.get("articles") if isinstance(existing, dict) else None
    if not isinstance(results, dict):
        raise ValueError(f"{output_path} has no valid articles object")
    if any(not isinstance(result, dict) for result in results.values()):
        raise ValueError(f"{output_path} contains an invalid article result")
    return results


def _write_metrics(output_path, articles, now):
    previous_results = _load_previous_results(output_path)
    results = {}
    failed_articles = []
    successful_scrapes = 0
    for article in articles:
        article_id = article["id"]
        scraper = _SCRAPERS[article["source"]]
        try:
            results[article_id] = scraper(article)
            successful_scrapes += 1
        except (ValueError, RuntimeError, OSError) as error:
            previous = previous_results.get(article_id)
            if (
                previous is not None
                and previous.get("source") == article.get("source")
                and previous.get("doi") == article.get("doi")
            ):
                results[article_id] = previous
                retention = "retaining previous metrics"
            else:
                retention = "no matching previous metrics are available"
            print(
                f"Scrape warning for {article_id}: {error}; {retention}.",
                file=sys.stderr,
            )
            failed_articles.append(article_id)

    if successful_scrapes == 0:
        raise RuntimeError("No article metrics were refreshed; existing output was left unchanged")

    output = {
        "schema_version": 1,
        "generated_at": now.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "articles": results,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")
    try:
        temporary_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
        temporary_path.replace(output_path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
    print(
        f"Wrote metrics for {successful_scrapes} of {len(articles)} configured article(s) "
        f"to {output_path}"
    )
    if failed_articles:
        print(
            f"Completed with {len(failed_articles)} scraper warning(s); "
            "previous metrics were retained where available.",
            file=sys.stderr,
        )


def main(argv=None):
    parser = argparse.ArgumentParser(description="Scrape publication article usage metrics")
    parser.add_argument("--config", type=Path, default=Path("config/articles.json"))
    parser.add_argument("--output", type=Path, default=Path("data/metrics.json"))
    parser.add_argument("--check-interval-hours", type=int, default=48)
    parser.add_argument("--force", action="store_true", help="scrape even if the interval has not elapsed")
    args = parser.parse_args(argv)
    if args.check_interval_hours < 1:
        parser.error("--check-interval-hours must be at least 1")

    try:
        now = datetime.now(timezone.utc)
        articles = _load_articles(args.config)
        if not args.force and not _is_due(args.output, args.check_interval_hours, now):
            print(f"Skipping scrape; metrics were updated less than {args.check_interval_hours} hours ago")
            return 0
        _write_metrics(args.output, articles, now)
        return 0
    except (OSError, ValueError, json.JSONDecodeError, HTTPError, URLError, RuntimeError) as error:
        print(f"Scrape failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
