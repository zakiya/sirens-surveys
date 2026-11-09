# Sirens surveys

Raw-to-public pipeline for the San Diego Sirens member surveys (2023 onward).

- **Published data:** [`data/public/`](data/public/), with its own [README](data/public/README.md).
- **Results site:** [`site/`](site/), deployed to GitHub Pages by `.github/workflows/pages.yml`.
- **Question crosswalk across years:** [`docs/question_crosswalk.csv`](docs/question_crosswalk.csv)
- **How the public files are prepared:** [`docs/publication_rules.md`](docs/publication_rules.md)
- **Raw exports, by year:** `data/raw/`, local only and gitignored. Each year's
  folder has a README saying where the data came from.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env   # then add AIRTABLE_TOKEN
```

## Scripts

Run them in this order:

| Script | What it does |
|---|---|
| `scripts/export_airtable.py` | Exports every Airtable table to its year folder in `data/raw/` |
| `scripts/extract_free_text.py` | Collects all free-text answers into `data/raw/review/free_text.csv` |
| `scripts/privacy_flags.py` | Builds the privacy review sheet from `data/raw/review/privacy_flags.json` |
| `scripts/build_public.py` | Builds `data/public/` from the raw exports and the review decisions |
| `scripts/build_site.py` | Builds `site/data/` (chart data and CSV downloads) from `data/public/` |
| `scripts/build_crosswalk.py` | Rebuilds `docs/question_crosswalk.csv` |
| `scripts/airtable_count.py` | Counts records per Airtable table, to check the connection |

## Previewing the site

```bash
.venv/bin/python scripts/build_site.py
python3 -m http.server 8765 --directory site
```

Then open http://localhost:8765. The page loads `data/surveys.json`, so it needs a server; opening `index.html` as a file won't work.
