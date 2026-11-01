"""Build the public survey files in data/public/ from the raw exports.

Applies docs/publication_rules.md:
  - only questions that were asked, headed with the wording respondents saw
  - no timestamps or platform IDs; each response gets a fresh ID (e.g. 2024-001),
    assigned after shuffling so the order doesn't reveal when people responded
  - free-text edits from data/raw/review/privacy_flags.json
"""
import csv
import json
import random
import re
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "public"

# 2023: Coda column -> question wording from the Coda page headings.
COLUMNS_2023 = {
    "01H Price": "01 Do you think your season tickets are fairly priced for the section you are in?",
    "02H Benefits": "02 Do you think you get good benefits being a season ticket holder?",
    "03H Service": "03 Does your ticket rep provide good service?",
    "04H Flex": "04 Does your front office provide fair and flexible ticketing policies?",
    "05H Recommend": "05 Would you recommend someone to become a season ticket holder on value alone?",
    "06H (Share)": "06 Share anything else you have to say about home game tickets and ticketing policies.",
    "07S Safety": "07 Do you feel safe when attending games in your own stadium? Does security keep away supporters out of the home supporters end?",
    "08S Standing": "08 Is the supporters section properly set up with standing in mind? Is the stadium and supporters section well maintained?",
    "09S Concessions": "09 Are food and drinks affordable? Are there options for people with dietary needs (i.e. vegan, nut-free, sugar free options, etc.)? Is water widely available at a low cost or for free (i.e. water fountains)?",
    "10S Security": "10 How quickly does security respond to reported incidents? Does security handle these incidents in an appropriate manner?",
    "11S Supporter": "11 Is there an area where people can learn more about the supporter groups in your stadium?",
    "12S Accessibility": "12 Is there proper accommodations for people with physical disabilities (i.e. companion seating, accessible bathrooms/stalls) Does the team take into account the needs of people with sensory needs? (ie. sensory room/bags)",
    "13S (Share)": "13 Share anything else you have to say about the experience in the stadium.",
}

# 2024: sheet columns for questions that were never asked.
NOT_ASKED_2024 = {
    "Is the supporters section properly set up with standing in mind?",
    "IIs the stadium and supporters section well maintained?",
    "Is there an area where people can learn more about the supporter groups in your stadium?",
    "I have signed up for a Sirens membership",
    "Will you sign up for a 2025 Sirens membership?",
    "What do you value most about being a Siren?",
    "How do you feel about the following: [Merchandise]",
    "How do you feel about the following: [Value of membership]",
    "Column 31",
    "Column 32",
}

# 2025: Airtable field -> wording on the form, in form order (section, field, question).
COLUMNS_2025 = [
    ("Stadium experience", "How many Wave home games did you go to in 2025?",
     "How many Wave home games did you go to in 2025?"),
    ("Stadium experience", "Which stadium accessibility feature(s) have you or someone you know used at a Wave home game?",
     "Which stadium accessibility feature(s) have you or someone you know used at a Wave home game?"),
    ("Stadium experience", "Where do you typically sit during Wave FC home games?",
     "Where do you typically sit during Wave home games?"),
    ("Stadium experience", "What else would you like to share about your experience in the stadium this year?",
     "What else would you like to share about your experience in the stadium this year?"),
    ("Wave front office", "Were you a 2025 season ticket holder?",
     "Were you a 2025 season ticket holder?"),
    ("Wave front office", "Did your ticket rep(s) provide good service in 2025?",
     "Did your ticket rep(s) provide good service in 2025?"),
    ("Wave front office", "What else would you like to share about your experience with the Wave Front Office this year?",
     "What else would you like to share about your experience with the Wave Front Office this year?"),
    ("Watch parties", "Where did you attend watch parties in 2025?",
     "Where did you attend watch parties in 2025?"),
    ("Watch parties", "When there are multiple watch parties at the same time, how do decide which to attend?",
     "When there are multiple watch parties at the same time, how do you decide which to attend?"),
    ("Sirens", "How do you find about about Sirens news and events?",
     "How do you find about about Sirens news and events?"),
    ("Sirens", "Which of the following organizations would you like Sirens to continue supporting?",
     "Which of the following organizations would you like Sirens to continue supporting?"),
    ("Sirens", "Please list any other organizations you feel like the Sirens should support.",
     "Please list any other organizations you feel like the Sirens should support."),
    ("Sirens", "1.1 Did you have Sirens 2025 membership?",
     "Did you have Sirens 2025 membership?"),
    ("Sirens", "How likely are you to renew your Sirens membership?",
     "How likely are you to renew your Sirens membership for 2026?"),
    ("Sirens", "What factors go into your decision whether to renew?",
     "What factors go into your decision whether to renew?"),
    ("Final thoughts", "What else would you like to share about your experience with the Sirens or the Wave this year?",
     "What else would you like to share about your experience with the Sirens or the Wave this year?"),
]


def clean(value):
    return "" if value is None else str(value).strip()


def load_2023():
    d = json.loads((RAW / "coda" / "2023_isc_raw_answers.json").read_text())
    cols = d["columns"]
    header = [COLUMNS_2023[c] for c in cols[1:]]
    rows = [(str(r[0]), {COLUMNS_2023[c]: clean(v) for c, v in zip(cols[1:], r[1:])}) for r in d["rows"]]
    # Flags refer to Coda column names; map them to the published headers.
    return header, rows, dict(COLUMNS_2023)


def question_number(header):
    m = re.match(r"(\d+)\.(\d+)", header)
    return (int(m.group(1)), int(m.group(2))) if m else (99, 99)


def load_2024():
    ws = openpyxl.load_workbook(
        RAW / "drive" / "2024_sirens_end_of_year_survey_responses.xlsx"
    )["Form Responses 1"]
    data = [r for r in ws.iter_rows(values_only=True) if any(v not in (None, "") for v in r)]
    sheet_header = [clean(h) for h in data[0]]
    keep = [h for h in sheet_header if h and h != "Timestamp" and h not in {clean(c) for c in NOT_ASKED_2024}]
    header = sorted(keep, key=question_number)  # sorted() is stable, so 6.1 items keep sheet order
    rows = []
    for n, r in enumerate(data[1:], start=1):
        values = dict(zip(sheet_header, r))
        rows.append((str(n), {h: clean(values[h]) for h in header}))
    return header, rows, {}


def load_2025():
    with open(RAW / "airtable" / "2025_results.csv", newline="") as fh:
        records = list(csv.DictReader(fh))
    header = [f"{section}: {question}" for section, _, question in COLUMNS_2025]
    rename = {field: f"{section}: {question}" for section, field, question in COLUMNS_2025}
    rows = [(r["Number"], {rename[f]: clean(r[f]) for _, f, _ in COLUMNS_2025}) for r in records]
    return header, rows, rename


def apply_flags(year, header, rows, rename, flags):
    by_id = dict(rows)
    applied = 0
    for f in flags:
        if f["year"] != year or f["find"] is None:
            continue
        cols = [h for h in header if h.startswith(f["question_prefix"])]
        cols += [new for old, new in rename.items() if old.startswith(f["question_prefix"])]
        cols = list(dict.fromkeys(cols))
        assert len(cols) == 1, (f, cols)
        row = by_id[f["response"]]
        assert row[cols[0]].count(f["find"]) == 1, (f, row[cols[0]])
        row[cols[0]] = row[cols[0]].replace(f["find"], f["replace"])
        applied += 1
    return applied


def write(year, header, rows):
    order = list(rows)
    random.Random(f"sirens-{year}").shuffle(order)
    path = OUT / f"sirens_survey_{year}.csv"
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["response_id"] + header)
        for i, (_, values) in enumerate(order, start=1):
            w.writerow([f"{year}-{i:03d}"] + [values[h] for h in header])
    return path


def main():
    flags = json.loads((RAW / "review" / "privacy_flags.json").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    expected = sum(1 for f in flags if f["find"] is not None)
    total = 0
    for year, load in (("2023", load_2023), ("2024", load_2024), ("2025", load_2025)):
        header, rows, rename = load()
        n = apply_flags(year, header, rows, rename, flags)
        total += n
        path = write(year, header, rows)
        print(f"{year}: {len(rows)} responses, {len(header)} questions, {n} edits -> {path.relative_to(ROOT)}")
    assert total == expected, (total, expected)
    print(f"all {total} edits applied")


if __name__ == "__main__":
    main()
