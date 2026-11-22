import unittest

from article_metrics_scraper.scrapers.mdpi import parse_metrics_html


class ParseMdpiMetricsTests(unittest.TestCase):
    def test_parses_article_views_count_from_adjacent_elements(self):
        html = """
        <div class="article-metrics">
          <span>Article Views</span>
          <span>2,330</span>
        </div>
        """

        self.assertEqual(parse_metrics_html(html), {"article_views": 2330})

    def test_parses_count_in_label_text(self):
        html = "<div>Article views: 2,330</div>"

        self.assertEqual(parse_metrics_html(html), {"article_views": 2330})

    def test_ignores_scripts_and_rejects_missing_count(self):
        html = """
        <script>Article views: 9999</script>
        <div>Downloads</div><div>45</div>
        """

        with self.assertRaisesRegex(ValueError, "Article views count was not found"):
            parse_metrics_html(html)


if __name__ == "__main__":
    unittest.main()
