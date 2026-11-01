# San Diego Sirens member surveys, 2023–2025

The San Diego Sirens are an independent supporters group for the San Diego Wave
Fútbol Club (Wave FC). Each year the Sirens survey their members about the game day
experience, the Wave front office and the Sirens themselves. The results feed the
Independent Supporters Council (ISC) front office rating, Sirens reports to Wave FC,
and the Sirens' plans for the next season.

This folder has every response from each year, cleaned for publication.

## Files

| File | Survey | Responses | Questions |
|---|---|---|---|
| `sirens_survey_2023.csv` | 2023 ISC front office ratings | 15 | 13 |
| `sirens_survey_2024.csv` | 2024 Sirens End of Year Survey | 97 | 27 |
| `sirens_survey_2025.csv` | 2025 Sirens survey | 65 | 16 |

Each file has one row per response. The first column, `response_id`, is an ID made up
for this release (for example `2024-001`). After that there's one column per question,
headed with the question as respondents saw it. A blank cell means the question was
skipped or didn't apply.

[`../../docs/question_crosswalk.csv`](../../docs/question_crosswalk.csv) lines up the
questions across years, with response counts and notes on wording changes.

## About each year

### 2023

- **Collected with:** a Coda form, which has since been deleted. These 15 responses
  are the complete set.
- **When and who:** October 2023. Posted to everyone in the Sirens Discord
  announcements channel to inform the ISC front office rating.
- **Questions:** the ISC guiding questions on home game ticketing and the in-stadium
  experience. Each rating question was answered Yes, No or Other, and "Other" had no
  write-in box. There were two optional comment questions.
- **Not included:** feedback sent to officers by direct message instead of through the
  form. The published 2023 ISC report also used officer ratings, so this file won't
  match that report.

### 2024

- **Collected with:** a Google Form.
- **When and who:** November 4–15, 2024. Sent to 2024 Sirens members through social
  media, Discord and the newsletter.
- **Questions:** sections on respondent profile (1.x), ticketing (2.x–3.x), the
  stadium (4.x), accessibility (5.x), Sirens activities and membership (6.x) and
  merchandise (7.x). Columns are in question-number order.
- **Choice answers:** many choice questions also accepted a write-in, so some cells
  hold free text.
- **Multi-select answers:** separated by commas. Some options contain commas
  themselves, e.g. "Other San Diego sports events (Padres, Legion, Mojo, etc)".

### 2025

- **Collected with:** an Airtable form.
- **When and who:** November 5 to December 8, 2025. Sent to 2025 Sirens members.
- **Questions:** column headers start with the form section ("Stadium experience",
  "Wave front office", "Watch parties", "Sirens", "Final thoughts"), in form order.
- **Changes from earlier years:** 2025 did **not** repeat most ISC ticketing and
  stadium questions (ticket price, benefits, policies, safety, food, security), so
  those trends cover 2023–2024 only. The ticket rep question changed to a
  satisfaction scale.
- **Multi-select answers:** separated by semicolons (`; `).
- **Spelling:** typos in the wording and options are kept as respondents saw them,
  e.g. "find about about" and "Somewhat satified".

## How the data was prepared

- Only questions that were actually asked are included. Each source had extra empty
  fields left over from templates, and those were dropped.
- Timestamps and platform record IDs were removed. Rows were shuffled before IDs were
  assigned, so row order doesn't reveal when someone responded.
- Every free-text answer was read before release. Names of Wave staff, Sirens
  officers, volunteers and other private people were replaced with a role in square
  brackets, e.g. `[ticket rep]`. A few details that would let other fans recognize the
  respondent were generalized the same way. **Any text in square brackets was written
  by the Sirens, not the respondent.**
- Players, coaches and club executives are public figures, and their names are kept.
- Otherwise answers are published as written, including spelling and opinions.

## Questions or concerns

If you see something in these files that identifies you or someone else, email
contact@sandiegosirens.com and it will be removed.
