"""Write data/raw/review/privacy_review.csv: free-text answers that need a decision
before the survey data goes public.

Every free-text answer for 2023-2025 was read by hand on 2026-10-31. The ones with
a concern are listed in data/raw/review/privacy_flags.json, kept under data/raw/
(gitignored) because the flags quote the sensitive text. Each flag has:
  year, response, question_prefix, risk (high/medium/low), concern,
  find, replace   - the edit; find=null means keep, flagged for awareness
  decision        - "edit" or "keep", as decided with the user on 2026-10-31
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REVIEW = ROOT / "data" / "raw" / "review"
FREE_TEXT = REVIEW / "free_text.csv"
FLAGS = REVIEW / "privacy_flags.json"
OUT = REVIEW / "privacy_review.csv"


def main():
    flags = json.loads(FLAGS.read_text())
    with open(FREE_TEXT, newline="") as fh:
        answers = list(csv.DictReader(fh))
    with open(OUT, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["year", "response", "question", "risk", "concern", "suggested_edit", "text", "decision"])
        for f in flags:
            match = [a for a in answers
                     if a["year"] == f["year"] and a["response"] == f["response"]
                     and a["question"].startswith(f["question_prefix"])]
            assert len(match) == 1, f
            text = match[0]["text"]
            if f["find"] is None:
                edit = "keep as is (flagged for awareness)"
            else:
                assert f["find"] in text, f
                edit = f'replace "{f["find"]}" with "{f["replace"]}"'
            w.writerow([f["year"], f["response"], match[0]["question"], f["risk"],
                        f["concern"], edit, text, f.get("decision", "")])
    counts = {r: sum(1 for f in flags if f["risk"] == r) for r in ("high", "medium", "low")}
    print(f"{len(flags)} flags {counts} -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
