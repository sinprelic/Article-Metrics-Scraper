import json
import unittest
from unittest.mock import patch

from article_metrics_scraper.scrapers.frontiers import (
    parse_metrics_payload,
    scrape,
)


class ParseFrontiersMetricsTests(unittest.TestCase):
    def test_parses_citations_views_and_downloads(self):
        payload = {
            "articleId": 1677943,
            "totalViews": 4140,
            "totalDownloads": 695,
            "totalCitations": 2,
        }

        self.assertEqual(
            parse_metrics_payload(payload, 1677943),
            {"citations": 2, "views": 4140, "downloads": 695},
        )

    def test_rejects_mismatched_article_id(self):
        payload = {
            "articleId": 1,
            "totalViews": 2,
            "totalDownloads": 3,
            "totalCitations": 4,
        }

        with self.assertRaisesRegex(ValueError, "article ID does not match"):
            parse_metrics_payload(payload, 1677943)

    def test_rejects_invalid_metric_counts(self):
        payload = {
            "articleId": 1677943,
            "totalViews": True,
            "totalDownloads": 695,
            "totalCitations": 2,
        }

        with self.assertRaisesRegex(ValueError, "views count"):
            parse_metrics_payload(payload, 1677943)

    def test_scrapes_article_totals_endpoint(self):
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return json.dumps({
                    "articleId": 1677943,
                    "totalViews": 4140,
                    "totalDownloads": 695,
                    "totalCitations": 2,
                }).encode("utf-8")

        with patch(
            "article_metrics_scraper.scrapers.frontiers.urlopen",
            return_value=FakeResponse(),
        ) as urlopen_mock:
            result = scrape({
                "doi": "10.3389/fimmu.2025.1677943",
            })

        self.assertEqual(
            result,
            {
                "source": "frontiers",
                "doi": "10.3389/fimmu.2025.1677943",
                "article_url": "https://doi.org/10.3389/fimmu.2025.1677943",
                "citations": 2,
                "views": 4140,
                "downloads": 695,
            },
        )
        self.assertIn("articleId=1677943", urlopen_mock.call_args.args[0].full_url)

    def test_rejects_invalid_doi(self):
        with self.assertRaisesRegex(ValueError, "Invalid Frontiers DOI"):
            scrape({"doi": "10.3389/not-a-frontiers-doi"})


if __name__ == "__main__":
    unittest.main()
