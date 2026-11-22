import unittest

from article_metrics_scraper.scrapers.edmond import parse_metrics_html


class ParseEdmondMetricsTests(unittest.TestCase):
    def test_reads_aggregate_downloads_and_ignores_file_counts(self):
        html = """
        <div id="metrics-block">
          <div id="metrics-body">
            <div class="metrics-count-block">1,272 Downloads
              <span class="tooltip-icon">Total aggregated downloads</span>
            </div>
          </div>
        </div>
        <div class="file-row">13 Downloads</div>
        """

        self.assertEqual(parse_metrics_html(html), {"downloads": 1272})

    def test_rejects_missing_dataset_metrics_section(self):
        with self.assertRaisesRegex(ValueError, "Dataset Metrics section was not found"):
            parse_metrics_html("<html><body>272 Downloads</body></html>")

    def test_rejects_page_without_aggregate_downloads(self):
        html = '<div id="metrics-body">No downloads yet</div>'
        with self.assertRaisesRegex(ValueError, "found 0"):
            parse_metrics_html(html)

    def test_reports_antibot_challenge_without_attempting_to_bypass_it(self):
        html = "<html><body>Making sure you're not a bot!</body></html>"
        with self.assertRaisesRegex(RuntimeError, "anti-bot challenge"):
            parse_metrics_html(html)


if __name__ == "__main__":
    unittest.main()
