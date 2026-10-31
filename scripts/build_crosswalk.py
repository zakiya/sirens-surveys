"""Write docs/question_crosswalk.csv: every question asked 2023-2025, side by side.

Each cell is "question text (answered/responses)". A blank cell means the
question wasn't asked that year. Fields that exist in a source but have zero
answers are listed separately in UNANSWERED_FIELDS, not treated as asked.
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
N = {"2023": 15, "2024": 97, "2025": 65}

# (id, section, 2023, 2024, 2025, answer format, notes)
# Each year entry is (question text, number answered) or None.
ROWS = [
    ("P1", "Respondent", None,
     ("1.1 Did you have Sirens 2024 membership?", 97),
     ("1.1 Did you have Sirens 2025 membership?", 65),
     "Yes/No", "96/97 and 65/65 said yes, so only members are responding."),
    ("P2", "Respondent", None,
     ("1.2 How many Wave FC home games did you go to in 2024?", 97),
     ("How many Wave home games did you go to in 2025?", 65),
     "Single choice", "Buckets changed: 2024 '0 - 5 / 5 - 10 / More than 10' overlap; 2025 '1 - 5 / 6 - 10 / More than 10' don't."),
    ("P3", "Respondent", None,
     ("1.3 Were you a 2024 season ticket holder?", 97),
     ("Were you a 2025 season ticket holder?", 65),
     "Yes/No", "Gates the ticketing section."),
    ("P4", "Respondent", None, None,
     ("Where do you typically sit during Wave FC home games?", 64),
     "Free text", "36 different spellings of sections; works better as a multiple choice."),
    ("M1", "Membership", None, None,
     ("How likely are you to renew your Sirens membership?", 63),
     "Likelihood scale", "58/63 very likely."),
    ("M2", "Membership", None, None,
     ("What factors go into your decision whether to renew?", 30),
     "Free text", ""),
    ("M3", "Membership", None,
     ("6.3 What else would you like us to know about Sirens membership?", 26),
     None, "Free text", ""),
    ("T1", "Ticketing (ISC)",
     ("01 Do you think your season tickets are fairly priced for the section you are in?", 15),
     ("2.1 Did you think your season tickets were fairly priced for the section you were in?", 80),
     None, "Yes/No/Other", "ISC core. Field exists in 2025 Airtable with no answers."),
    ("T2", "Ticketing (ISC)",
     ("02 Do you think you get good benefits being a season ticket holder?", 15),
     ("2.2 Do you think you got good benefits being a season ticket holder?", 80),
     None, "Yes/No/Other", "ISC core. Field exists in 2025 Airtable with no answers."),
    ("T3", "Ticketing (ISC)",
     ("03 Does your ticket rep provide good service?", 15),
     ("2.3 Did your ticket rep provide good service?", 80),
     ("Did your ticket rep(s) provide good service in 2025?", 60),
     "Yes/No/Other; 2025 satisfaction scale", "Only ticketing question asked all three years. 2025 option 'Somewhat satified' is misspelled."),
    ("T4", "Ticketing (ISC)",
     ("04 Does your front office provide fair and flexible ticketing policies?", 14),
     ("3.1 Does your front office provide fair and flexible ticketing policies?", 97),
     None, "Yes/No/Other", "ISC core. Field exists in 2025 Airtable with no answers."),
    ("T5", "Ticketing (ISC)",
     ("05 Would you recommend someone to become a season ticket holder on value alone?", 15),
     ("2.4 Would you recommend someone to become a season ticket holder on value alone?", 80),
     None, "Yes/No/Other", "ISC core. Field exists in 2025 Airtable with no answers."),
    ("T6", "Ticketing (ISC)",
     ("06 Share anything else you have to say about home game tickets and ticketing policies.", 6),
     ("3.2 What else would you like us to know about home game tickets and ticketing policies?", 31),
     ("What else would you like to share about your experience with the Wave Front Office this year?", 21),
     "Free text", "2025 widened this to the whole front office."),
    ("S1", "Stadium (ISC)",
     ("07 Do you feel safe when attending games in your own stadium? Does security keep away supporters out of the home supporters end?", 15),
     ("4.1 Do you feel safe when attending games in your home stadium?", 97),
     None, "Yes/No/Other", "ISC core. Field exists in 2025 Airtable with no answers."),
    ("S2", "Stadium (ISC)",
     ("08 Is the supporters section properly set up with standing in mind? Is the stadium and supporters section well maintained?", 15),
     None, None, "Yes/No/Other", "Columns exist in the 2024 sheet but the form never collected answers."),
    ("S3", "Stadium (ISC)",
     ("09 Are food and drinks affordable? Are there options for people with dietary needs? Is water widely available at a low cost or for free?", 15),
     ("4.2 Are food and drinks affordable?", 97),
     None, "Yes/No/Other", "2023 bundled price, dietary options and water into one question."),
    ("S4", "Stadium (ISC)", None,
     ("4.3 Does the stadium have options for people with dietary needs?", 97),
     None, "Yes/No/Other", "Split out of 2023 Q09."),
    ("S5", "Stadium (ISC)",
     ("10 How quickly does security respond to reported incidents? Does security handle these incidents in an appropriate manner?", 14),
     ("4.4 Does stadium security respond to incidents in an appropriate manner?", 97),
     None, "Yes/No/Other", "9/14 answered 'Other' in 2023, which suggests most people hadn't seen an incident."),
    ("S6", "Stadium (ISC)",
     ("11 Is there an area where people can learn more about the supporter groups in your stadium?", 15),
     None, None, "Yes/No/Other", "Column exists in the 2024 sheet but the form never collected answers."),
    ("S7", "Stadium (ISC)",
     ("12 Is there proper accommodations for people with physical disabilities? Does the team take into account the needs of people with sensory needs?", 15),
     ("5.1 Which stadium accessibility feature(s) have you or someone you know used at a Wave FC home game?", 97),
     ("Which stadium accessibility feature(s) have you or someone you know used at a Wave home game?", 37),
     "2023 Yes/No/Other; 2024-25 multi-select", "Changed from a rating to features used; years aren't directly comparable."),
    ("S8", "Stadium (ISC)", None,
     ("5.2 Please share any accessibility accommodations that would improve the home game day experience.", 16),
     None, "Free text", "Field exists in 2025 Airtable with no answers."),
    ("S9", "Stadium (ISC)",
     ("13 Share anything else you have to say about the experience in the stadium.", 7),
     ("4.5 What else would you like us to know about the experience in the stadium?", 39),
     ("What else would you like to share about your experience in the stadium this year?", 28),
     "Free text", "Asked all three years."),
    ("A1", "Sirens activities", None,
     ("6.1 How do you feel about the following: [Watch parties]", 97),
     None, "Satisfaction scale", "2024 grid. 2025 has watch-party venue rating fields (Kairoa, Brejeria, FairPlay) with no answers."),
    ("A2", "Sirens activities", None,
     ("6.1 How do you feel about the following: [Tailgates]", 97),
     None, "Satisfaction scale", "2025 'Tailgates' field exists with no answers."),
    ("A3", "Sirens activities", None,
     ("6.1 How do you feel about the following: [Drums and chants]", 97),
     None, "Satisfaction scale", "2025 'Drums and chants' field exists with no answers."),
    ("A4", "Sirens activities", None,
     ("6.1 How do you feel about the following: [Discord]", 97),
     None, "Satisfaction scale", "2025 asked how people hear about news instead (C1)."),
    ("A5", "Sirens activities", None,
     ("6.1 How do you feel about the following: [Newsletter]", 97),
     None, "Satisfaction scale", "Most-liked item in 2024 (86/97 satisfied)."),
    ("A6", "Sirens activities", None,
     ("6.1 How do you feel about the following: [Sirens discounts]", 97),
     None, "Satisfaction scale", "41/97 neutral."),
    ("A7", "Sirens activities", None,
     ("6.2 What types of Sirens events would you like to see more of in 2025?", 85),
     None, "Free text", "2025 field '6.2 ... in 2026? [XX]' has no answers."),
    ("A8", "Sirens activities", None, None,
     ("Where did you attend watch parties in 2025?", 51),
     "Multi-select", ""),
    ("A9", "Sirens activities", None, None,
     ("When there are multiple watch parties at the same time, how do decide which to attend?", 34),
     "Free text", "Marked 'Needs work' in the 2025 Questions table."),
    ("C1", "Communication", None, None,
     ("How do you find about about Sirens news and events?", 63),
     "Multi-select", "Typo in wording ('find about about')."),
    ("G1", "Community giving", None, None,
     ("Which of the following organizations would you like Sirens to continue supporting?", 57),
     "Multi-select", ""),
    ("G2", "Community giving", None, None,
     ("Please list any other organizations you feel like the Sirens should support.", 5),
     "Free text", ""),
    ("X1", "Merchandise", None,
     ("7.1 What kind of Sirens merchandise would you like to see?", 57),
     None, "Free text", ""),
    ("X2", "Merchandise", None,
     ("7.2 What would make you buy more Sirens merchandise?", 46),
     None, "Free text", ""),
    ("X3", "Merchandise", None,
     ("7.3 What design elements would you like to see in next year's merchandise?", 35),
     None, "Free text", ""),
    ("O1", "Open comments", None, None,
     ("What else would you like to share about your experience with the Sirens or the Wave this year?", 21),
     "Free text", ""),
]

UNANSWERED_FIELDS = {
    "2024 Google Sheet": [
        "Is the supporters section properly set up with standing in mind?",
        "IIs the stadium and supporters section well maintained?",
        "Is there an area where people can learn more about the supporter groups in your stadium?",
        "I have signed up for a Sirens membership",
        "Will you sign up for a 2025 Sirens membership?",
        "What do you value most about being a Siren?",
        "How do you feel about the following: [Merchandise]",
        "How do you feel about the following: [Value of membership]",
        "Column 31", "Column 32",
    ],
    "2025 Airtable": [
        "2.1 fairly priced", "2.2 good benefits", "2.4 recommend on value",
        "3.1 fair and flexible policies", "3.2 ticketing comments",
        "4.1 feel safe", "4.2 food and drinks affordable", "4.3 dietary needs",
        "4.4 security response", "5.2 accessibility suggestions",
        "Kairoa", "Brejeria", "FairPlay", "Tailgates", "Drums and chants",
        "Notes 2", "6.2 events in 2026 [XX]",
    ],
}
# "Watch party summary" in 2025 Airtable has 33 values but looks like an
# officer-made field, not a question, so it's in neither list.


def fmt(entry, year):
    if entry is None:
        return ""
    text, answered = entry
    return f"{text} ({answered}/{N[year]})"


def main():
    out = ROOT / "docs" / "question_crosswalk.csv"
    out.parent.mkdir(exist_ok=True)
    with open(out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "section", "2023 (n=15)", "2024 (n=97)", "2025 (n=65)",
                    "years asked", "answer format", "notes"])
        for qid, section, q23, q24, q25, fmt_, notes in ROWS:
            years = ",".join(y for y, q in (("2023", q23), ("2024", q24), ("2025", q25)) if q)
            w.writerow([qid, section, fmt(q23, "2023"), fmt(q24, "2024"), fmt(q25, "2025"),
                        years, fmt_, notes])
    print(f"{len(ROWS)} questions -> {out.relative_to(ROOT)}")
    for source, fields in UNANSWERED_FIELDS.items():
        print(f"{source}: {len(fields)} fields with no answers")


if __name__ == "__main__":
    main()
