"""Build site/data/surveys.json (chart-ready summaries) and copy the public CSVs
into site/data/ for download.

Reads only data/public/, so everything on the site is already privacy-reviewed.
Write-in answers to choice questions are counted under "Not sure or other" and
listed in full under the chart.
"""
import csv
import json
import re
import shutil
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "data" / "public"
OUT = ROOT / "site" / "data"

YES_NO = [
    {"key": "No", "label": "No", "role": "neg2"},
    {"key": "Other", "label": "Not sure or other", "role": "neutral"},
    {"key": "Yes", "label": "Yes", "role": "pos2"},
]
SATISFACTION = [
    {"key": "Very unsatisfied", "label": "Very unsatisfied", "role": "neg2"},
    {"key": "Somewhat unsatisfied", "label": "Somewhat unsatisfied", "role": "neg1"},
    {"key": "Neutral", "label": "Neutral", "role": "neutral"},
    {"key": "Somewhat satisfied", "label": "Somewhat satisfied", "role": "pos1"},
    {"key": "Very satisfied", "label": "Very satisfied", "role": "pos2"},
]


def read(year):
    with open(PUBLIC / f"sirens_survey_{year}.csv", newline="") as fh:
        return list(csv.DictReader(fh))


def col(rows, prefix):
    matches = [h for h in rows[0] if h.startswith(prefix)]
    assert len(matches) == 1, (prefix, matches)
    return matches[0]


def answered(rows, header):
    return [r[header] for r in rows if r[header].strip()]


def strip_number(header):
    """'2.1 Did you…' / '01 Do you…' / 'Sirens: How…' -> the question alone."""
    header = re.sub(r"^\d+(\.\d+)?\s+", "", header)
    return header.split(": ", 1)[1] if re.match(r"^[A-Z][a-z]+( [a-z]+)*: ", header) else header


# ---------- block builders ----------

def yes_no_row(rows, prefix, label, yes=("Yes",), no=("No",)):
    """One diverging row. Anything other than the yes/no options counts as Other;
    long write-ins are kept so the page can list them."""
    header = col(rows, prefix)
    counts, write_ins = Counter(), []
    for v in answered(rows, header):
        v = v.strip()
        if v in yes:
            counts["Yes"] += 1
        elif v in no:
            counts["No"] += 1
        else:
            counts["Other"] += 1
            if v.lower() not in {"unsure", "other", "not sure", "unsure?", "idk", "?"}:
                write_ins.append(v)
    return {"label": label, "question": strip_number(header), "counts": dict(counts),
            "n": sum(counts.values()), "writeIns": write_ins}


def diverging(title, subtitle, categories, rows_, note=None):
    return {"type": "diverging", "title": title, "subtitle": subtitle,
            "categories": categories, "rows": rows_, "note": note}


def scale_row(rows, prefix, label, mapping, excluded=None):
    header = col(rows, prefix)
    counts, skipped = Counter(), 0
    for v in answered(rows, header):
        if excluded and v == excluded:
            skipped += 1
            continue
        counts[mapping.get(v, v)] += 1
    row = {"label": label, "question": strip_number(header), "counts": dict(counts),
           "n": sum(counts.values()), "writeIns": []}
    if excluded:
        row["excluded"] = {"label": excluded, "count": skipped}
    return row


def bars(title, subtitle, items, denominator, note=None, ordered=False, write_ins=None):
    if not ordered:
        items = sorted(items, key=lambda kv: (-kv[1], kv[0] == "Other"))
    return {"type": "bars", "title": title, "subtitle": subtitle,
            "items": [{"label": k, "count": v} for k, v in items],
            "denominator": denominator, "note": note, "writeIns": write_ins or []}


def multi_select(rows, prefix, options, separator):
    """Count each option; anything that isn't a known option is a write-in."""
    header = col(rows, prefix)
    values = answered(rows, header)
    counts, write_ins = Counter(), []
    for v in values:
        rest = v
        for opt in sorted(options, key=len, reverse=True):
            if opt in rest:
                counts[opt] += 1
                rest = rest.replace(opt, "")
        sep = re.escape(separator.strip())
        rest = re.sub(rf"(\s*{sep}\s*){{2,}}", f"{separator.strip()} ", rest)
        rest = re.sub(rf"^(\s*{sep})+|({sep}\s*)+$", "", rest).strip()
        if rest:
            counts["Other"] += 1
            write_ins.append(rest)
    return header, values, counts, write_ins


def comments(title, rows, prefix):
    header = col(rows, prefix)
    items = sorted(answered(rows, header), key=lambda t: (len(t) < 25, t.lower()))
    return {"type": "comments", "title": title, "question": strip_number(header), "items": items}


def stat(label, value, detail):
    return {"label": label, "value": value, "detail": detail}


def pct(part, whole):
    return round(100 * part / whole) if whole else 0


# ---------- years ----------

def year_2023():
    rows = read("2023")
    n = len(rows)
    t = lambda p, label: yes_no_row(rows, p, label)
    ticketing = [t("01", "Fairly priced"), t("02", "Good benefits"), t("03", "Ticket rep service"),
                 t("04", "Fair, flexible policies"), t("05", "Would recommend on value")]
    stadium = [t("07", "Feel safe"), t("08", "Set up for standing"), t("09", "Food and drink affordable"),
               t("10", "Security responds well"), t("11", "Place to learn about supporter groups"),
               t("12", "Accessibility accommodations")]
    return {
        "year": "2023", "title": "2023 front office ratings", "responses": n,
        "platform": "Coda form", "when": "October 2023",
        "who": "Anyone in the Sirens Discord, invited in the announcements channel",
        "stats": [
            stat("Responses", str(n), "All answers collected by the form"),
            stat("Questions", "13", "11 rating questions and 2 comment boxes"),
            stat("Comments", str(sum(1 for r in rows for h in r if "Share anything" in h and r[h])), "Written answers across both comment boxes"),
        ],
        "sections": [
            {"title": "Tickets and the front office", "blocks": [
                diverging("How the Wave did on ticketing",
                          f"Share of {n} respondents. \"Other\" was a single choice, with no write-in box.",
                          YES_NO, ticketing),
                comments("Comments on tickets", rows, "06"),
            ]},
            {"title": "Stadium experience", "blocks": [
                diverging("How the stadium did", f"Share of {n} respondents.", YES_NO, stadium),
                comments("Comments on the stadium", rows, "13"),
            ]},
        ],
    }


def year_2024():
    rows = read("2024")
    n = len(rows)
    sth = sum(1 for v in answered(rows, col(rows, "1.3")) if v == "Yes")
    members = sum(1 for v in answered(rows, col(rows, "1.1")) if v == "Yes")
    games = Counter(answered(rows, col(rows, "1.2")))
    t = lambda p, label, **kw: yes_no_row(rows, p, label, **kw)
    unsure = ("Unsure",)
    ticketing = [t("2.1", "Fairly priced"), t("2.2", "Good benefits"), t("2.3", "Ticket rep service"),
                 t("2.4", "Would recommend on value"), t("3.1", "Fair, flexible policies")]
    stadium = [t("4.1", "Feel safe"), t("4.2", "Food and drink affordable"),
               t("4.3", "Options for dietary needs"), t("4.4", "Security responds well")]
    grid = [scale_row(rows, f"6.1 How do you feel about the following: [{item}]", item, {},
                      excluded="Doesn't apply to me")
            for item in ("Newsletter", "Drums and chants", "Discord", "Tailgates", "Watch parties", "Sirens discounts")]
    access_opts = ["None", "Accessible/ADA seating", "Accessible/ADA parking", "Shuttle service",
                   "Closed captioning", "Quiet room"]
    _, access_vals, access, access_wi = multi_select(rows, "5.1", access_opts, ", ")
    event_opts = ["Social events", "Volunteer events", "Donation drives", "Social justice and activism",
                  "Watch parties for other soccer leagues", "Other San Diego sports events (Padres, Legion, Mojo, etc)"]
    _, event_vals, events, event_wi = multi_select(rows, "6.2", event_opts, ", ")
    events = Counter({("Other San Diego sports events" if k.startswith("Other San Diego") else k): v
                      for k, v in events.items()})
    return {
        "year": "2024", "title": "2024 End of Year Survey", "responses": n,
        "platform": "Google Form", "when": "November 4–15, 2024",
        "who": "2024 Sirens members, through social media, Discord and the newsletter",
        "stats": [
            stat("Responses", str(n), "Everyone who submitted the form"),
            stat("Sirens members", f"{pct(members, n)}%", f"{members} of {n}"),
            stat("Season ticket holders", f"{pct(sth, n)}%", f"{sth} of {n}"),
            stat("At more than 10 home games", f"{pct(games['More than 10'], n)}%", f"{games['More than 10']} of {n}"),
        ],
        "sections": [
            {"title": "Who answered", "blocks": [
                bars("Home games attended in 2024", f"Share of {n} respondents.",
                     [(k, games[k]) for k in ("0 - 5", "5 - 10", "More than 10", "I'm not sure")], n, ordered=True,
                     note="The answer ranges overlap at 5, as they did on the form."),
            ]},
            {"title": "Tickets and the front office", "blocks": [
                diverging("How the Wave did on ticketing",
                          "Share of people who answered each question. The first four were asked of season ticket holders.",
                          YES_NO, ticketing,
                          note="Write-in answers count as \"Not sure or other\" and are listed below."),
                comments("Comments on tickets", rows, "3.2"),
            ]},
            {"title": "Stadium experience", "blocks": [
                diverging("How the stadium did", f"Share of {n} respondents.",
                          YES_NO, stadium,
                          note="\"Unsure\" was an answer choice for dietary options and security, and most people picked it."),
                bars("Accessibility features used",
                     f"Share of {n} respondents. People could pick more than one.",
                     list(access.items()), n, write_ins=access_wi),
                comments("Accessibility suggestions", rows, "5.2"),
                comments("Comments on the stadium", rows, "4.5"),
            ]},
            {"title": "Sirens activities", "blocks": [
                diverging("How people feel about Sirens activities",
                          "Share of people each item applies to, sorted by how many were very satisfied.",
                          SATISFACTION, sorted(grid, key=lambda r: -r["counts"].get("Very satisfied", 0) / max(r["n"], 1)),
                          note="People who said an item doesn't apply to them are left out; the count is in the table."),
                bars("Events people want more of in 2025",
                     f"Share of {len(event_vals)} people who answered. They could pick more than one.",
                     list(events.items()), len(event_vals), write_ins=event_wi),
                comments("Comments on Sirens membership", rows, "6.3"),
            ]},
            {"title": "Merchandise", "blocks": [
                comments("Merchandise people want", rows, "7.1"),
                comments("What would make people buy more", rows, "7.2"),
                comments("Design ideas", rows, "7.3"),
            ]},
        ],
    }


def seat_bucket(v):
    s = v.lower()
    if re.search(r"\b138\b|cove|supporter", s):
        return "The Cove (section 138)"
    m = re.search(r"c?\s*([123])\d\d", s)
    if m:
        return f"{m.group(1)}00 level"
    if "ga" == s.strip() or "general admission" in s:
        return "General admission"
    return "Varies or doesn't sit"


def year_2025():
    rows = read("2025")
    n = len(rows)
    games = Counter(answered(rows, col(rows, "Stadium experience: How many")))
    sth = sum(1 for v in answered(rows, col(rows, "Wave front office: Were you")) if v == "Yes")
    seats = Counter(seat_bucket(v) for v in answered(rows, col(rows, "Stadium experience: Where do you")))
    seat_n = sum(seats.values())
    access_opts = ["None", "Accessible/ADA seating", "Accessible/ADA parking", "Shuttle service",
                   "Closed captioning", "Quiet room", "Other"]
    _, access_vals, access, _ = multi_select(rows, "Stadium experience: Which stadium", access_opts, "; ")
    news_opts = ["Sirens newsletter", "Discord", "Social media", "Word of mouth", "Other", "Unsure"]
    _, news_vals, news, _ = multi_select(rows, "Sirens: How do you find", news_opts, "; ")
    venue_header = col(rows, "Watch parties: Where did")
    venue_vals = answered(rows, venue_header)
    venues = Counter(p.strip() for v in venue_vals for p in v.split(";"))
    org_header = col(rows, "Sirens: Which of the following")
    org_vals = answered(rows, org_header)
    orgs = Counter(p.strip() for v in org_vals for p in v.split(";"))
    rep = scale_row(rows, "Wave front office: Did your ticket rep", "Ticket rep service",
                    {"Somewhat satified": "Somewhat satisfied"}, excluded="Other / Not sure")
    renew = scale_row(rows, "Sirens: How likely", "Renewing for 2026",
                      {}, excluded=None)
    renew_cats = [
        {"key": "Very unlikely", "label": "Very unlikely", "role": "neg2"},
        {"key": "Somewhat unlikely", "label": "Somewhat unlikely", "role": "neg1"},
        {"key": "Somewhat likely", "label": "Somewhat likely", "role": "pos1"},
        {"key": "Very likely", "label": "Very likely", "role": "pos2"},
    ]
    # The 2025 form offered only these three ratings (plus "Other / Not sure").
    rep_cats = [c for c in SATISFACTION if c["key"] in ("Very unsatisfied", "Somewhat satisfied", "Very satisfied")]
    return {
        "year": "2025", "title": "2025 Sirens survey", "responses": n,
        "platform": "Airtable form", "when": "November 5 – December 8, 2025",
        "who": "2025 Sirens members",
        "stats": [
            stat("Responses", str(n), "Everyone who submitted the form"),
            stat("Season ticket holders", f"{pct(sth, n)}%", f"{sth} of {n}"),
            stat("Very likely to renew", f"{pct(renew['counts'].get('Very likely', 0), renew['n'])}%",
                 f"{renew['counts'].get('Very likely', 0)} of {renew['n']} who answered"),
            stat("At more than 10 home games", f"{pct(games['More than 10'], n)}%", f"{games['More than 10']} of {n}"),
        ],
        "sections": [
            {"title": "Stadium experience", "blocks": [
                bars("Home games attended in 2025", f"Share of {n} respondents.",
                     [(k, games.get(k, 0)) for k in ("1 - 5", "6 - 10", "More than 10")], n, ordered=True,
                     note="Nobody picked \"None\" or \"Other / Not sure\"."),
                bars("Where people usually sit", f"Share of {seat_n} people who answered, grouped by section.",
                     list(seats.items()), seat_n,
                     note="Answers were typed in, so they're grouped here. Club sections (C107, C229 and so on) are counted by level."),
                bars("Accessibility features used",
                     f"Share of {len(access_vals)} people who answered. People could pick more than one.",
                     list(access.items()), len(access_vals)),
                comments("Comments on the stadium", rows, "Stadium experience: What else"),
            ]},
            {"title": "Wave front office", "blocks": [
                diverging("Ticket rep service",
                          f"Share of {rep['n']} people who rated their rep.",
                          rep_cats, [rep],
                          note="The form had no \"Somewhat unsatisfied\" option. People who picked \"Other / Not sure\" are left out; the count is in the table."),
                comments("Comments on the front office", rows, "Wave front office: What else"),
            ]},
            {"title": "Watch parties", "blocks": [
                bars("Where people watched away games",
                     f"Share of {len(venue_vals)} people who answered. People could pick more than one.",
                     list(venues.items()), len(venue_vals)),
                comments("How people choose a watch party", rows, "Watch parties: When there are"),
            ]},
            {"title": "Sirens", "blocks": [
                diverging("Renewing for 2026", f"Share of {renew['n']} people who answered.",
                          renew_cats, [renew], note="The form offered Very likely, Somewhat likely and Very unlikely."),
                comments("What goes into renewing", rows, "Sirens: What factors"),
                bars("How people hear about Sirens news",
                     f"Share of {len(news_vals)} people who answered. People could pick more than one.",
                     list(news.items()), len(news_vals)),
                bars("Organizations to keep supporting",
                     f"Share of {len(org_vals)} people who answered. People could pick more than one.",
                     list(orgs.items()), len(org_vals)),
                comments("Other organizations suggested", rows, "Sirens: Please list"),
            ]},
            {"title": "Final thoughts", "blocks": [
                comments("Anything else", rows, "Final thoughts:"),
            ]},
        ],
    }


TAKEAWAYS = {
    "2023": [
        "Ticketing mostly got good marks: 12 of 15 said prices were fair, 11 rated their ticket rep well, and 10 would recommend season tickets on value alone.",
        "Benefits were the weak spot. 8 of 15 said season tickets didn't come with good benefits.",
        "9 of 15 said stadium food and drink weren't affordable.",
        "Nobody said security responds well to incidents: 9 of 14 weren't sure and 5 said no.",
        "With 15 responses, each answer is about 7% of the total, so read these as signals, not settled numbers.",
    ],
    "2024": [
        "89 of 97 people feel safe at home games.",
        "Season ticket holders were mostly happy with prices (70 of 80) and their reps (58 of 80), but less sure about benefits: 45 said yes and 27 said no.",
        "52 of 97 said stadium food and drink aren't affordable.",
        "Most people couldn't rate security (71 of 97 weren't sure or wrote something else) or dietary options (60 of 97).",
        "The newsletter was the best-liked Sirens activity: 86 of the 96 people it applies to were satisfied. Discounts drew the most shrugs, with 41 of 83 neutral.",
        "Volunteer events (46), social events (44) and social justice and activism (43) topped the list of events people want more of.",
    ],
    "2025": [
        "58 of 63 people are very likely to renew their Sirens membership.",
        "52 of the 53 people who rated their ticket rep were satisfied, 37 of them very satisfied.",
        "The newsletter (42 of 63) and Discord (41) are how most people hear Sirens news.",
        "FairPlay in North Park (24 of 51) and Novo Brewing in Mission Valley (21) drew the most people to away-game watch parties.",
        "The NWSL Players Association was the most-chosen organization to keep supporting, picked by 49 of 57.",
        "25 of 64 people sit in the Cove (section 138); the rest are spread across the stadium.",
    ],
}


def across(y23, y24, y25):
    def find(year, title=None, label=None):
        for s in year["sections"]:
            for b in s["blocks"]:
                if label:
                    for r in b.get("rows", []):
                        if r["label"] == label:
                            return r
                elif b.get("title") == title:
                    return b
        raise KeyError(title or label)

    def bar_count(block, label):
        return next(i["count"] for i in block["items"] if i["label"] == label)

    def positive(row, keys):
        good = sum(row["counts"].get(k, 0) for k in keys)
        rated = row["n"] - row["counts"].get("Other", 0)
        return {"value": pct(good, rated), "detail": f"{good} of {rated}"}

    rep23 = positive(find(y23, label="Ticket rep service"), ["Yes"])
    rep24 = positive(find(y24, label="Ticket rep service"), ["Yes"])
    rep25 = positive(find(y25, label="Ticket rep service"), ["Very satisfied", "Somewhat satisfied"])

    def cell(value, detail):
        return {"value": value, "detail": detail}

    sth24 = next(s for s in y24["stats"] if s["label"] == "Season ticket holders")
    sth25 = next(s for s in y25["stats"] if s["label"] == "Season ticket holders")
    g24 = next(s for s in y24["stats"] if s["label"] == "At more than 10 home games")
    g25 = next(s for s in y25["stats"] if s["label"] == "At more than 10 home games")
    a24, a25 = find(y24, "Accessibility features used"), find(y25, "Accessibility features used")
    none24, none25 = bar_count(a24, "None"), bar_count(a25, "None")
    na = cell("", "Not asked")
    return {
        "rep": {
            "title": "Ticket rep service, all three years",
            "subtitle": "Share of people who rated their rep positively, leaving out \"not sure\" answers. 2023 and 2024 asked yes or no; 2025 used a satisfaction scale, so \"very\" and \"somewhat satisfied\" both count here.",
            "items": [{"label": "2023", **rep23}, {"label": "2024", **rep24}, {"label": "2025", **rep25}],
        },
        "table": {
            "title": "Measures asked in more than one year",
            "columns": ["2023", "2024", "2025"],
            "rows": [
                {"label": "Responses", "cells": [cell("15", ""), cell("97", ""), cell("65", "")]},
                {"label": "Season ticket holders", "cells": [na, cell(sth24["value"], sth24["detail"]), cell(sth25["value"], sth25["detail"])]},
                {"label": "At more than 10 home games", "cells": [na, cell(g24["value"], g24["detail"]), cell(g25["value"], g25["detail"])]},
                {"label": "Rated their ticket rep positively", "cells": [
                    cell(f"{rep23['value']}%", rep23["detail"]), cell(f"{rep24['value']}%", rep24["detail"]), cell(f"{rep25['value']}%", rep25["detail"])]},
                {"label": "Used no stadium accessibility features", "cells": [
                    na, cell(f"{pct(none24, a24['denominator'])}%", f"{none24} of {a24['denominator']}"),
                    cell(f"{pct(none25, a25['denominator'])}%", f"{none25} of {a25['denominator']}")]},
            ],
            "note": "2023 asked about accessibility as a yes-or-no rating, so it isn't comparable. 2025 didn't ask the ticketing, safety, food or security questions.",
        },
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    years = [year_2023(), year_2024(), year_2025()]
    for y in years:
        y["takeaways"] = TAKEAWAYS[y["year"]]
    data = {"years": years, "across": across(*years)}
    (OUT / "surveys.json").write_text(json.dumps(data, indent=1, ensure_ascii=False))
    for f in PUBLIC.glob("sirens_survey_*.csv"):
        shutil.copy(f, OUT / f.name)
    for y in years:
        blocks = [b for s in y["sections"] for b in s["blocks"]]
        print(f"{y['year']}: {y['responses']} responses, {len(blocks)} blocks")
    print(f"-> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
