import unittest

from article_metrics_scraper.scrapers.figshare import parse_metrics_payload


class ParseFigshareMetricsTests(unittest.TestCase):
    def test_maps_figshare_and_openalex_fields_to_output_metrics(self):
        views = {"totals": 123}
        downloads = {"totals": 45}
        citations = {"cited_by_count": 6}

        self.assertEqual(
            parse_metrics_payload(views, downloads, citations),
            {"views": 123, "downloads": 45, "citations": 6},
        )

    def test_accepts_zero_counts(self):
        self.assertEqual(
            parse_metrics_payload(
                {"totals": 0},
                {"totals": 0},
                {"cited_by_count": 0},
            ),
            {"views": 0, "downloads": 0, "citations": 0},
        )

    def test_rejects_missing_or_invalid_counts(self):
        with self.assertRaisesRegex(ValueError, "views total must be a non-negative integer"):
            parse_metrics_payload(
                {},
                {"totals": 0},
                {"cited_by_count": 0},
            )
        with self.assertRaisesRegex(ValueError, "OpenAlex cited_by_count"):
            parse_metrics_payload(
                {"totals": 1},
                {"totals": 0},
                {"cited_by_count": None},
            )


if __name__ == "__main__":
    unittest.main()
