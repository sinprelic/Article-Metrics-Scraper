import unittest
from unittest.mock import patch

from article_metrics_scraper.scrapers.preprints_org import parse_metrics_html, scrape


class ParsePreprintsMetricsTests(unittest.TestCase):
    def test_parses_downloads_and_views(self):
        html = """
        <div class="flex justify-between py-sm border-b border-color-default">
          <p>Downloads</p><p>1,139</p>
        </div>
        <div class="flex justify-between py-sm border-b border-color-default">
          <p>Views</p><p>213</p>
        </div>
        <div class="flex justify-between py-sm border-b border-color-default">
          <p>Comments</p><p>0</p>
        </div>
        """

        self.assertEqual(
            parse_metrics_html(html),
            {"downloads": 1139, "views": 213},
        )

    def test_rejects_missing_metric(self):
        html = """
        <div class="flex justify-between py-sm border-b">
          <p>Downloads</p><p>139</p>
        </div>
        """
        with self.assertRaisesRegex(ValueError, "views"):
            parse_metrics_html(html)

    def test_rejects_non_numeric_metric(self):
        html = """
        <div class="flex justify-between py-sm border-b">
          <p>Downloads</p><p>139</p>
        </div>
        <div class="flex justify-between py-sm border-b">
          <p>Views</p><p>many</p>
        </div>
        """
        with self.assertRaisesRegex(ValueError, "not a non-negative integer"):
            parse_metrics_html(html)

    @patch("article_metrics_scraper.scrapers.preprints_org.urlopen")
    def test_scrape_uses_canonical_manuscript_url(self, urlopen):
        response = urlopen.return_value.__enter__.return_value
        response.read.return_value = b"""
        <div class="flex justify-between py-sm">
          <p>Downloads</p><p>139</p>
        </div>
        <div class="flex justify-between py-sm">
          <p>Views</p><p>113</p>
        </div>
        """

        metrics = scrape({"doi": "10.20944/preprints202411.1965.v1"})

        self.assertEqual(
            metrics["article_url"],
            "https://www.preprints.org/manuscript/202411.1965",
        )
        self.assertEqual(metrics["version"], 1)
        self.assertEqual(metrics["downloads"], 139)
        self.assertEqual(metrics["views"], 113)
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, metrics["article_url"])


if __name__ == "__main__":
    unittest.main()
