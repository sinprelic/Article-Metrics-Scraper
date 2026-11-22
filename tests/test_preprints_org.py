import unittest

from article_metrics_scraper.scrapers.preprints_org import parse_metrics_html


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


if __name__ == "__main__":
    unittest.main()
