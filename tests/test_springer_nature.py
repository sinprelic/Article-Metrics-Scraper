import unittest

from article_metrics_scraper.scrapers.springer_nature import parse_metrics_html


class ParseSpringerNatureMetricsTests(unittest.TestCase):
    def test_reads_accesses_and_citations_from_metrics_bar(self):
        html = """
        <div data-test="article-metrics">
          <ul class="app-article-metrics-bar">
            <li data-test="access-count">
              <p>4,201 <span>Accesses</span></p>
            </li>
            <li data-test=citation-count>
              <p>2 <span>Citations</span></p>
            </li>
            <li data-test="altmetric-score"><p>2 Altmetric</p></li>
          </ul>
        </div>
        """

        self.assertEqual(
            parse_metrics_html(html),
            {"accesses": 4201, "citations": 2},
        )

    def test_rejects_missing_metrics(self):
        with self.assertRaisesRegex(ValueError, "missing the Accesses count"):
            parse_metrics_html("<html><body>No metrics</body></html>")

    def test_reports_client_challenge(self):
        html = '<html><head><title>Client Challenge</title></head></html>'
        with self.assertRaisesRegex(RuntimeError, "client challenge"):
            parse_metrics_html(html)


if __name__ == "__main__":
    unittest.main()
