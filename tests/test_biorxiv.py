import unittest

from article_metrics_scraper.scrapers.biorxiv import parse_metrics_html


class ParseMetricsHtmlTests(unittest.TestCase):
    def test_sums_lifetime_usage_columns_and_ignores_other_tables(self):
        html = """
        <table><tr><th>Abstract</th><th>Full</th><th>Pdf</th></tr>
        <tr><td>Jan 2024</td><td>900</td><td>900</td><td>900</td></tr></table>
        <table class="highwire-stats sticky-enabled">
          <thead><tr><th></th><th>Abstract</th><th>Full</th><th>Pdf</th></tr></thead>
          <tbody>
            <tr><td>Oct 2021</td><td>1,124</td><td>24</td><td>291</td></tr>
            <tr><td>Nov 2021</td><td>51</td><td>8</td><td>68</td></tr>
          </tbody>
        </table>
        """

        self.assertEqual(
            parse_metrics_html(html),
            {"abstract_views": 1175, "full_text_views": 32, "pdf_downloads": 359},
        )

    def test_rejects_page_without_metrics_table(self):
        with self.assertRaisesRegex(ValueError, "table was not found"):
            parse_metrics_html("<html><body>No usage data</body></html>")

    def test_rejects_metrics_table_without_expected_columns(self):
        html = """
        <table class="highwire-stats">
          <tr><th>Month</th><th>Abstract</th></tr>
          <tr><td>Oct 2021</td><td>12</td></tr>
        </table>
        """

        with self.assertRaisesRegex(ValueError, "missing the full_text_views column"):
            parse_metrics_html(html)


if __name__ == "__main__":
    unittest.main()
