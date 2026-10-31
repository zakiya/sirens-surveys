"""Count records in each table of the Sirens surveys Airtable base."""
import json
import os
import urllib.request
from pathlib import Path

BASE_ID = "appPpqIZUPQDyBYeZ"


def load_token():
    for line in (Path(__file__).resolve().parent.parent / ".env").read_text().splitlines():
        if line.startswith("AIRTABLE_TOKEN="):
            return line.split("=", 1)[1].strip()
    return os.environ["AIRTABLE_TOKEN"]


def get(url, token):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def main():
    token = load_token()
    tables = get(f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables", token)["tables"]
    for table in tables:
        count, offset = 0, None
        while True:
            url = f"https://api.airtable.com/v0/{BASE_ID}/{table['id']}?pageSize=100"
            if offset:
                url += f"&offset={offset}"
            page = get(url, token)
            count += len(page.get("records", []))
            offset = page.get("offset")
            if not offset:
                break
        print(f"{table['name']}: {count} records")


if __name__ == "__main__":
    main()
