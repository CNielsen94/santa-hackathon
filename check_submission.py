"""Check that a submission file is complete and well-formed. It knows nothing about
the answers: it only checks the format.

    python check_submission.py my_team.csv
"""
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent


def check(path):
    ids = set(HERE.joinpath("test_ids.txt").read_text(encoding="utf-8").split())
    workshops = set(json.loads(HERE.joinpath("workshops.json").read_text(encoding="utf-8")))
    problems = []
    with open(path, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        missing_cols = {"id", "is_fake", "name", "workshops", "transcription", "wishes"} - set(reader.fieldnames or [])
        if missing_cols:
            return [f"missing columns: {', '.join(sorted(missing_cols))}"]
        seen = set()
        for n, row in enumerate(reader, start=2):
            lid = row["id"].strip()
            if lid not in ids:
                problems.append(f"line {n}: unknown id {lid!r}")
            if lid in seen:
                problems.append(f"line {n}: {lid} appears twice")
            seen.add(lid)
            if row["is_fake"].strip() not in ("0", "1"):
                problems.append(f"line {n}: is_fake must be 0 or 1")
            shops = [w.strip() for w in (row["workshops"] or "").split(";") if w.strip()]
            for w in shops:
                if w not in workshops:
                    problems.append(f"line {n}: unknown workshop {w!r}")
            if row["is_fake"].strip() == "1" and shops:
                problems.append(f"line {n}: a fake letter goes to no workshop")
            wish_shops = set()
            for part in (row["wishes"] or "").split(";"):
                if not part.strip():
                    continue
                text, arrow, shop = part.partition("=>")
                if not arrow or not text.strip():
                    problems.append(f"line {n}: wishes must look like 'wish=>workshop', got {part.strip()!r}")
                elif shop.strip() not in workshops:
                    problems.append(f"line {n}: unknown workshop {shop.strip()!r} in wishes")
                else:
                    wish_shops.add(shop.strip())
            if row["is_fake"].strip() == "1" and wish_shops:
                problems.append(f"line {n}: a fake letter has no wishes to route")
            if wish_shops and wish_shops != set(shops):
                problems.append(f"line {n}: workshops column does not match the workshops in wishes")
            score = (row.get("fake_score") or "").strip()
            if score:
                try:
                    if not 0 <= float(score) <= 1:
                        raise ValueError
                except ValueError:
                    problems.append(f"line {n}: fake_score must be a number from 0 to 1")
    if ids - seen:
        problems.append(f"{len(ids - seen)} test letters have no row")
    return problems


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    found = check(sys.argv[1])
    for p in found[:50]:
        print(p)
    if len(found) > 50:
        print(f"... and {len(found) - 50} more")
    print("OK: ready to submit" if not found else f"{len(found)} problem(s)")
    sys.exit(1 if found else 0)
