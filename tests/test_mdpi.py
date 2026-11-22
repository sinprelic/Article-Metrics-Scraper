import unittest

from article_metrics_scraper.scrapers.mdpi import parse_metrics_html


class ParseMdpiMetricsTests(unittest.TestCase):
    def test_parses_article_views_and_citations_from_adjacent_elements(self):
        html = """
        <div class="article-metrics">
          <span>Article Views</span>
          <span>2,330</span>
          <span>Citations</span>
          <span>5</span>
        </div>
        """

        self.assertEqual(parse_metrics_html(html), {"article_views": 2330, "citations": 5})

    def test_parses_inline_counts_and_zero_citations(self):
        html = "<div>Article views: 2,330</div><div>Citations: 0</div>"

        self.assertEqual(parse_metrics_html(html), {"article_views": 2330, "citations": 0})

    def test_parses_metrics_when_citations_appear_first(self):
        html = """
        <div class="article-metrics">
          <span>Citations</span>
          <span>5</span>
          <span>Article Views</span>
          <span>2,330</span>
        </div>
        """

        self.assertEqual(parse_metrics_html(html), {"article_views": 2330, "citations": 5})

    def test_ignores_scripts_and_rejects_missing_article_views(self):
        html = """
        <script>Article views: 9999; Citations: 4</script>
        <div>Downloads</div><div>45</div>
        """

        with self.assertRaisesRegex(ValueError, "Article views count was not found"):
            parse_metrics_html(html)

    def test_requires_citations_count(self):
        html = "<div>Article views: 2,330</div>"

        with self.assertRaisesRegex(ValueError, "Citations count was not found"):
            parse_metrics_html(html)


if __name__ == "__main__":
    unittest.main()
