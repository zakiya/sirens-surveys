"""Export every table in the Sirens surveys Airtable base to data/raw/airtable/.

For each table this writes:
  <table>.records.json  - records exactly as the API returns them
  <table>.csv           - one row per record, columns in the base's field order
  schema.json           - table and field metadata for the whole base
"""
import csv
import json
import os
import re
import urllib.request
from pathlib import Path

BASE_ID = "appPpqIZUPQDyBYeZ"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw" / "airtable"


def load_token():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("AIRTABLE_TOKEN="):
                return line.split("=", 1)[1].strip()
    return os.environ["AIRTABLE_TOKEN"]


def get(url, token):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def fetch_records(table_id, token):
    records, offset = [], None
    while True:
        url = f"https://api.airtable.com/v0/{BASE_ID}/{table_id}?pageSize=100"
        if offset:
            url += f"&offset={offset}"
        page = get(url, token)
        records += page.get("records", [])
        offset = page.get("offset")
        if not offset:
            return records


def cell(value):
    """Flatten Airtable cell values (lists, attachments, AI text) for CSV."""
    if isinstance(value, list):
        return "; ".join(cell(v) for v in value)
    if isinstance(value, dict):
        return value.get("value") or value.get("url") or value.get("name") or json.dumps(value)
    return "" if value is None else str(value)


def slug(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def main():
    token = load_token()
    OUT.mkdir(parents=True, exist_ok=True)
    tables = get(f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables", token)["tables"]
    (OUT / "schema.json").write_text(json.dumps(tables, indent=2))

    for table in tables:
        records = fetch_records(table["id"], token)
        name = slug(table["name"])
        (OUT / f"{name}.records.json").write_text(json.dumps(records, indent=2))

        fields = [f["name"] for f in table["fields"]]
        with open(OUT / f"{name}.csv", "w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["airtable_id", "created_time"] + fields)
            for r in records:
                writer.writerow(
                    [r["id"], r["createdTime"]] + [cell(r["fields"].get(f)) for f in fields]
                )
        print(f"{table['name']}: {len(records)} records -> {name}.csv")


if __name__ == "__main__":
    main()
