# Sirens surveys

Raw-to-public pipeline for the San Diego Sirens member surveys (2023 onward).

- **Published data:** [`data/public/`](data/public/), with its own [README](data/public/README.md).
- **Question crosswalk across years:** [`docs/question_crosswalk.csv`](docs/question_crosswalk.csv)
- **How the public files are prepared:** [`docs/publication_rules.md`](docs/publication_rules.md)

## Sources

| Year | Platform | Raw export |
|---|---|---|
| 2023 | Coda | `data/raw/coda/2023_isc_raw_answers.json`, exported by hand through the Coda connector |
| 2024 | Google Sheets | `data/raw/drive/2024_sirens_end_of_year_survey_responses.xlsx`, downloaded from Drive |
| 2025 | Airtable | `data/raw/airtable/`, from `scripts/export_airtable.py` |

`data/raw/` is gitignored. It holds unreviewed responses and the privacy review
decisions, which quote the answers.

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
| `scripts/export_airtable.py` | Exports every Airtable table to `data/raw/airtable/` |
| `scripts/extract_free_text.py` | Collects all free-text answers into `data/raw/review/free_text.csv` |
| `scripts/privacy_flags.py` | Builds the privacy review sheet from `data/raw/review/privacy_flags.json` |
| `scripts/build_public.py` | Builds `data/public/` from the raw exports and the review decisions |
| `scripts/build_crosswalk.py` | Rebuilds `docs/question_crosswalk.csv` |
| `scripts/airtable_count.py` | Counts records per Airtable table, to check the connection |
