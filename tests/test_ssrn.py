import unittest

from article_metrics_scraper.scrapers.ssrn import parse_metrics_html


class ParseSsrnMetricsTests(unittest.TestCase):
    def test_parses_downloads_and_abstract_views(self):
        html = """
        <div class="stats row">
          <div class="stat col-lg-4">
            <div class="lbl">Downloads</div>
            <div class="number" title="">64</div>
          </div>
          <div class="stat col-lg-4">
            <div class="lbl">Abstract Views</div>
            <div class="number" title="">1,533</div>
          </div>
        </div>
        """

        self.assertEqual(
            parse_metrics_html(html),
            {"downloads": 64, "abstract_views": 1533},
        )

    def test_rejects_missing_metric(self):
        with self.assertRaisesRegex(ValueError, "abstract views"):
            parse_metrics_html(
                '<div class="lbl">Downloads</div><div class="number">64</div>'
            )

    def test_rejects_non_numeric_metric(self):
        html = """
        <div class="lbl">Downloads</div><div class="number">64</div>
        <div class="lbl">Abstract Views</div><div class="number">many</div>
        """
        with self.assertRaisesRegex(ValueError, "not a non-negative integer"):
            parse_metrics_html(html)


if __name__ == "__main__":
    unittest.main()
