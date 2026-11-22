from contextlib import redirect_stderr
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from io import StringIO

from article_metrics_scraper import cli


class WriteMetricsTests(unittest.TestCase):
    def test_continues_after_failure_and_preserves_matching_previous_result(self):
        articles = [
            {
                "id": "preprints_vatpase",
                "source": "preprints_org",
                "doi": "10.20944/preprints202411.1965.v1",
            },
            {
                "id": "biorxiv_support_cells",
                "source": "biorxiv",
                "doi": "10.1101/2021.10.04.463011",
            },
        ]
        previous_preprints = {
            "source": "preprints_org",
            "doi": "10.20944/preprints202411.1965.v1",
            "downloads": 139,
            "views": 113,
        }
        refreshed_biorxiv = {
            "source": "biorxiv",
            "doi": "10.1101/2021.10.04.463011",
            "abstract_views": 2000,
        }
        now = datetime(2026, 11, 22, tzinfo=timezone.utc)

        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "metrics.json"
            output_path.write_text(
                json.dumps({"generated_at": "2026-11-20T00:00:00Z", "articles": {
                    "preprints_vatpase": previous_preprints,
                }}),
                encoding="utf-8",
            )
            warning_output = StringIO()
            with (
                patch.dict(
                    cli._SCRAPERS,
                    {
                        "preprints_org": unittest.mock.Mock(
                            side_effect=RuntimeError("HTTP Error 403: Forbidden")
                        ),
                        "biorxiv": unittest.mock.Mock(return_value=refreshed_biorxiv),
                    },
                ),
                redirect_stderr(warning_output),
            ):
                cli._write_metrics(output_path, articles, now)

            output = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(output["articles"]["preprints_vatpase"], previous_preprints)
        self.assertEqual(output["articles"]["biorxiv_support_cells"], refreshed_biorxiv)
        self.assertIn("retaining previous metrics", warning_output.getvalue())

    def test_leaves_output_unchanged_when_every_scraper_fails(self):
        articles = [
            {"id": "preprints_vatpase", "source": "preprints_org", "doi": "doi-1"},
            {"id": "biorxiv_support_cells", "source": "biorxiv", "doi": "doi-2"},
        ]
        original = json.dumps({
            "generated_at": "2026-11-20T00:00:00Z",
            "articles": {},
        })

        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "metrics.json"
            output_path.write_text(original, encoding="utf-8")
            with patch.dict(
                cli._SCRAPERS,
                {
                    "preprints_org": unittest.mock.Mock(side_effect=RuntimeError("blocked")),
                    "biorxiv": unittest.mock.Mock(side_effect=RuntimeError("blocked")),
                },
            ), redirect_stderr(StringIO()):
                with self.assertRaisesRegex(RuntimeError, "No article metrics were refreshed"):
                    cli._write_metrics(
                        output_path,
                        articles,
                        datetime(2026, 11, 22, tzinfo=timezone.utc),
                    )

            self.assertEqual(output_path.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()
