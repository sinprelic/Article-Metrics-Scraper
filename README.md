# Article Metrics Scraper

A small, extensible Python project for collecting publication usage metrics and
publishing them as JSON. Each website has a separate scraper module.

## Current scraper

The bioRxiv scraper reads the article's lifetime usage table from its
`article-metrics` HTML page and totals its monthly **Abstract**, **Full**, and
**Pdf** counts. bioRxiv's documented API provides article metadata, not these
usage counts, so the scraper parses the metrics page.

The SSRN scraper reads **Downloads** and **Abstract Views** from each paper's
statistics section. The Preprints.org scraper reads **Downloads** and **Views**
from its manuscript page. Each scraper expects the source page to be publicly
accessible and fails explicitly if the site blocks the request or changes its
metrics markup.

The MDPI scraper resolves the article DOI and reads its **Article views** count
from the landing page.

The Figshare scraper reads **views** and **downloads** from Figshare's public
Statistics API and **citations** from OpenAlex's DOI record. The article
metadata API does not include Figshare usage totals.

The Springer Nature scraper reads **Accesses** and **Citations** from the
article metrics bar on SpringerLink. Springer returned a client challenge to
the scraper's direct Python request during setup; if this blocks GitHub
Actions too, the scraper reports the error rather than attempting to bypass
the challenge.

The EDMOND scraper reads the aggregate **Downloads** count from the dataset
page's **Dataset Metrics** section. Dataverse's public API provides monthly
Make Data Count metrics, not this aggregate count. The scraper does not work
around EDMOND's anti-bot challenge; if the dataset page is blocked, the scrape
fails explicitly and the existing metrics file is left unchanged.

The SSRN and Preprints.org pages rendered in the browser during setup, but
direct HTTP requests from this environment received HTTP 403. The MDPI page
also returned HTTP 403. GitHub Actions has now also received HTTP 403 from
Preprints.org. When a publisher blocks a request, the job reports the failure
and retains the previous `data/metrics.json` rather than bypassing the site's
access controls.

The tracked configuration is in `config/articles.json`. Each entry has a
unique ID, a scraper source, and the site's article identifier. The results
are written to `data/metrics.json`; a failed scrape leaves the previous file
unchanged and exits with an error.

## GitHub Actions

`.github/workflows/scrape-metrics.yml` runs daily at 00:23 UTC and checks the
timestamp in `data/metrics.json`. It scrapes only when at least 48 hours have
passed since the previous successful scrape, then commits updated JSON. Daily
checks avoid the month-boundary gaps of a `*/2` day-of-month cron schedule.

The workflow needs permission to write repository contents. Enable
**Settings → Actions → General → Workflow permissions → Read and write
permissions**. Branch protection that disallows bot pushes will also need to
be adjusted or the workflow's commit step replaced with an artifact/deployment
step.

You can run it manually from **Actions → Scrape article metrics → Run
workflow**. Select `force` to scrape immediately.

## Run locally

Requires Python 3.11 or later; there are no third-party dependencies.

```powershell
$env:PYTHONPATH = "src"
python -m article_metrics_scraper --force
python -m unittest discover -s tests
```

Without `--force`, the CLI also observes the 48-hour interval. The output
contains one entry per configured article:

```json
{
  "schema_version": 1,
  "generated_at": "2026-01-01T00:23:00Z",
  "articles": {
    "biorxiv_support_cells": {
      "source": "biorxiv",
      "doi": "10.1101/2021.10.04.463011",
      "version": 1,
      "article_url": "https://www.biorxiv.org/content/10.1101/2021.10.04.463011v1",
      "abstract_views": 0,
      "full_text_views": 0,
      "pdf_downloads": 0
    },
    "preprints_vatpase": {
      "source": "preprints_org",
      "doi": "10.20944/preprints202411.1965.v1",
      "version": 1,
      "article_url": "https://www.preprints.org/manuscript/202411.1965",
      "downloads": 0,
      "views": 0
    },
    "ssrn_stem_cells_epithelial_responders": {
      "source": "ssrn",
      "doi": "10.2139/ssrn.3485163",
      "article_url": "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3485163",
      "downloads": 0,
      "abstract_views": 0
    },
    "insects_vatpase": {
      "source": "mdpi",
      "doi": "10.3390/insects15121016",
      "article_url": "https://www.mdpi.com/2075-4450/15/12/1016",
      "article_views": 0
    },
    "insects_vatpase_figshare_data_repo": {
      "source": "figshare",
      "metrics_provider": "figshare_stats_and_openalex",
      "doi": "10.6084/m9.figshare.27994004",
      "article_url": "https://figshare.com/articles/journal_contribution/Supplementary_data_for_research_project_b_Expression_of_b_b_i_Drosophila_melanogaster_i_b_b_V-ATPases_in_olfactory_sensillum_support_cells_b_/27994004",
      "views": 139,
      "downloads": 68,
      "citations": 0
    }
  }
}
```

## Shields.io badge template

After pushing this project to GitHub, replace the placeholders below with its
owner, repository, and branch. Use the `raw.githubusercontent.com` URL as the
JSON source and query one metric at a time:

```markdown
![Abstract views](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2FOWNER%2FREPO%2FBRANCH%2Fdata%2Fmetrics.json&query=%24.articles.biorxiv_support_cells.abstract_views&label=Abstract%20views)
![Full-text HTML views](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2FOWNER%2FREPO%2FBRANCH%2Fdata%2Fmetrics.json&query=%24.articles.biorxiv_support_cells.full_text_views&label=HTML%20views)
![PDF downloads](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2FOWNER%2FREPO%2FBRANCH%2Fdata%2Fmetrics.json&query=%24.articles.biorxiv_support_cells.pdf_downloads&label=PDF%20downloads)
![Preprints.org downloads](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2FOWNER%2FREPO%2FBRANCH%2Fdata%2Fmetrics.json&query=%24.articles.preprints_vatpase.downloads&label=Preprints.org%20downloads)
![Preprints.org views](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2FOWNER%2FREPO%2FBRANCH%2Fdata%2Fmetrics.json&query=%24.articles.preprints_vatpase.views&label=Preprints.org%20views)
![SSRN downloads](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2FOWNER%2FREPO%2FBRANCH%2Fdata%2Fmetrics.json&query=%24.articles.ssrn_stem_cells_epithelial_responders.downloads&label=SSRN%20downloads)
![SSRN abstract views](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2FOWNER%2FREPO%2FBRANCH%2Fdata%2Fmetrics.json&query=%24.articles.ssrn_stem_cells_epithelial_responders.abstract_views&label=SSRN%20abstract%20views)
![MDPI article views](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2FOWNER%2FREPO%2FBRANCH%2Fdata%2Fmetrics.json&query=%24.articles.insects_vatpase.article_views&label=Article%20views)
![Figshare views](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2FOWNER%2FREPO%2FBRANCH%2Fdata%2Fmetrics.json&query=%24.articles.insects_vatpase_figshare_data_repo.views&label=Figshare%20views)
![Figshare downloads](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2FOWNER%2FREPO%2FBRANCH%2Fdata%2Fmetrics.json&query=%24.articles.insects_vatpase_figshare_data_repo.downloads&label=Figshare%20downloads)
![Figshare citations](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2FOWNER%2FREPO%2FBRANCH%2Fdata%2Fmetrics.json&query=%24.articles.insects_vatpase_figshare_data_repo.citations&label=Figshare%20citations)
![EDMOND downloads](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2FOWNER%2FREPO%2FBRANCH%2Fdata%2Fmetrics.json&query=%24.articles.edmond_3_7m.downloads&label=EDMOND%20downloads%20(3.7M))
![EDMOND downloads](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2FOWNER%2FREPO%2FBRANCH%2Fdata%2Fmetrics.json&query=%24.articles.edmond_3_9v6mom.downloads&label=EDMOND%20downloads%20(3.9V6MOM))
![EDMOND downloads](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2FOWNER%2FREPO%2FBRANCH%2Fdata%2Fmetrics.json&query=%24.articles.edmond_3_ogrunx.downloads&label=EDMOND%20downloads%20(3.OGRUNX))
![Springer Nature accesses](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2FOWNER%2FREPO%2FBRANCH%2Fdata%2Fmetrics.json&query=%24.articles.cell_tiss_res_innexin.accesses&label=Accesses)
![Springer Nature citations](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2FOWNER%2FREPO%2FBRANCH%2Fdata%2Fmetrics.json&query=%24.articles.cell_tiss_res_innexin.citations&label=Citations)
```

Shields.io caches badge responses, so displayed values may lag behind a scrape.

## Add another website

Create a scraper module under `src/article_metrics_scraper/scrapers/`, with a
function accepting one article's configuration and returning a dictionary of
integer metrics. Register its source in `src/article_metrics_scraper/cli.py`,
then add entries using that source to `config/articles.json`. Keep site-specific
HTTP and parsing behavior in its own module.
