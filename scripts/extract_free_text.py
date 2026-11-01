"""Collect every free-text answer from 2023-2025 into data/raw/review/free_text.csv.

A value counts as free text when its column is mostly unique answers, or when
it's a one-off write-in in an otherwise multiple-choice column. Output columns:
year, response, question, text. Output stays under data/raw/ (gitignored).
"""
import csv
import json
from collections import Counter
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = RAW / "review" / "free_text.csv"

# Fields that look free-text but hold fixed options or officer notes.
SKIP_COLUMNS = {"Timestamp", "Watch party summary"}


def year_2023():
    d = json.loads((RAW / "2023" / "coda_2023_isc_raw_answers.json").read_text())
    cols = d["columns"]
    for row in d["rows"]:
        for i, col in enumerate(cols):
            if col.endswith("(Share)") and row[i].strip():
                yield str(row[0]), col, row[i]


def year_2024():
    ws = openpyxl.load_workbook(
        RAW / "2024" / "google_sheet_2024_responses.xlsx"
    )["Form Responses 1"]
    rows = [r for r in ws.iter_rows(values_only=True) if any(v not in (None, "") for v in r)]
    header, body = rows[0], rows[1:]
    records = [
        (str(n), {h: ("" if v is None else str(v)) for h, v in zip(header, r) if h})
        for n, r in enumerate(body, start=1)
    ]
    yield from free_text(records, separator=", ")


def year_2025():
    with open(RAW / "2025" / "airtable_2025_results.csv", newline="") as fh:
        reader = csv.DictReader(fh)
        records = [
            (r["Number"], {k: v for k, v in r.items() if k not in ("airtable_id", "created_time", "Number")})
            for r in reader
        ]
    yield from free_text(records, separator="; ")


def free_text(records, separator):
    columns = {k for _, r in records for k in r} - SKIP_COLUMNS
    for col in sorted(columns):
        values = [r.get(col, "").strip() for _, r in records]
        answered = [v for v in values if v]
        if not answered:
            continue
        mostly_unique = len(set(answered)) / len(answered) > 0.5
        parts = Counter(p.strip() for v in answered for p in v.split(separator))
        for rid, r in records:
            v = r.get(col, "").strip()
            if not v:
                continue
            if mostly_unique:
                yield rid, col, v
            else:
                # Keep only one-off write-ins from a choice column.
                rare = [p.strip() for p in v.split(separator) if parts[p.strip()] == 1]
                if rare:
                    yield rid, col, separator.join(rare)


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    counts = Counter()
    with open(OUT, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["year", "response", "question", "text"])
        for year, source in (("2023", year_2023), ("2024", year_2024), ("2025", year_2025)):
            for rid, col, text in source():
                w.writerow([year, rid, col, text])
                counts[year] += 1
    for year, n in sorted(counts.items()):
        print(f"{year}: {n} free-text values")
    print(f"-> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
