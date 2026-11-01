# Publication rules

Rules for turning the raw survey exports (`data/raw/`, never committed) into the
public files (`data/public/`). Decided 2026-10-31.

## Sources

| Year | Authoritative source | Responses |
|---|---|---|
| 2023 | Coda table "2023 ISC Raw answers" (the Coda form itself was deleted) | 15 |
| 2024 | Google Sheet "2024 Sirens End of Year Survey (Responses)" | 97 |
| 2025 | Airtable base "Sirens surveys", table "2025 Results" | 65 |

- The Airtable "2024 results" table is a copy of the Google Sheet and isn't used: its
  checkboxes dropped the "No" answers.
- The 2023 ISC report isn't a source: it mixes member answers with officer ratings.

## Columns

- Drop columns for questions that were never asked: 10 in the 2024 sheet and 17 in
  the 2025 table. They're listed in `scripts/build_crosswalk.py` (`UNANSWERED_FIELDS`).
- Drop "Watch party summary" (2025). It's an officer-made field, not a question.
- Drop timestamps, Airtable record IDs and created times. Each file is already
  labeled by year.
- Give every response a fresh ID in the form `2024-001`, assigned after a fixed
  shuffle so row order doesn't reveal when people responded.
- Keep seat sections (2025) as answered. No rows or seat numbers were given.

## Free text

Every free-text answer was read by hand. Answers needing a decision are tracked in
`data/raw/review/privacy_flags.json` (gitignored, because it quotes the text), and
`scripts/privacy_flags.py` builds a review sheet from it.

- Replace names of Wave staff, Sirens officers and volunteers, and other private
  people with a role in brackets, e.g. `[ticket rep]`, `[Sirens officer]`, `[designer]`.
- Generalize details that would let other fans recognize the respondent.
- Any rewritten text goes in square brackets, so readers can tell it isn't the
  respondent's own words.
- Public figures (players, coaches, club executives) are kept as written.
- Respondents' own disclosures about identity, family or health are kept as written
  unless they identify the person.
