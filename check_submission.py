"""Check that a submission file is complete and well-formed. It knows nothing about
the answers: it only checks the format.

    python check_submission.py my_team.csv
        checks a test submission: one row for every test letter in test_ids.txt

    python check_submission.py my_dev_predictions.csv --key train/dev.jsonl known_fakes/known_fakes.jsonl
        checks a dev file: one row for every letter in the answer files you give
"""
import argparse
import csv
import json
from pathlib import Path

HERE = Path(__file__).parent
COLUMNS = ["id", "is_fake", "name", "workshops", "transcription", "wishes", "fake_score"]


def read_rows(path):
    """CSV rows as dicts. Accepts what spreadsheet programs write: a UTF-8 byte-order mark, Windows line
    endings, and ';' as the separator (Excel with Danish or other European settings)."""
    with open(path, encoding="utf-8-sig", newline="") as fh:
        text = fh.read()
    header = text.split("\n", 1)[0]
    delimiter = ";" if header.count(";") > header.count(",") else ","
    reader = csv.DictReader(text.splitlines(keepends=True), delimiter=delimiter)
    return reader.fieldnames or [], list(reader)


def expected_ids(key_paths):
    if not key_paths:
        return set(HERE.joinpath("test_ids.txt").read_text(encoding="utf-8").split()), "test"
    ids = set()
    for p in key_paths:
        for line in Path(p).read_text(encoding="utf-8").splitlines():
            if line.strip():
                ids.add(json.loads(line)["id"])
    return ids, "answer-file"


def check(path, key_paths=None):
    ids, kind = expected_ids(key_paths)
    workshops = set(json.loads(HERE.joinpath("workshops.json").read_text(encoding="utf-8")))
    try:
        fieldnames, rows = read_rows(path)
    except UnicodeDecodeError:
        return ["the file is not UTF-8. Save it as 'CSV UTF-8' (in pandas: to_csv(..., encoding='utf-8'))"]
    missing_cols = set(COLUMNS[:-1]) - set(fieldnames)
    if missing_cols:
        return [f"missing columns: {', '.join(sorted(missing_cols))}. The first line must be: {','.join(COLUMNS)}"]
    problems = []
    seen = set()
    for n, row in enumerate(rows, start=2):
        lid = (row["id"] or "").strip()
        if lid not in ids:
            hint = " (leave out the '_0.jpg' at the end)" if lid.endswith(".jpg") else ""
            problems.append(f"line {n}: unknown id {lid!r}{hint}")
        if lid in seen:
            problems.append(f"line {n}: {lid} appears twice")
        seen.add(lid)
        fake = (row["is_fake"] or "").strip()
        if fake not in ("0", "1"):
            problems.append(f"line {n}: is_fake must be 0 or 1")
        shops = [w.strip() for w in (row["workshops"] or "").split(";") if w.strip()]
        for w in shops:
            if w not in workshops:
                problems.append(f"line {n}: unknown workshop {w!r}")
        if fake == "1" and shops:
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
        if fake == "1" and wish_shops:
            problems.append(f"line {n}: a fake letter has no wishes to route")
        if wish_shops != set(shops):
            problems.append(f"line {n}: workshops column does not match the workshops in wishes")
        score = (row.get("fake_score") or "").strip()
        if score:
            try:
                if not 0 <= float(score) <= 1:
                    raise ValueError
            except ValueError:
                problems.append(f"line {n}: fake_score must be a number from 0 to 1")
    if ids - seen:
        problems.append(f"{len(ids - seen)} {kind} letters have no row")
    return problems


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("submission")
    ap.add_argument("--key", nargs="+", help="check against these answer files instead of the test letters")
    a = ap.parse_args()
    found = check(a.submission, a.key)
    for p in found[:50]:
        print(p)
    if len(found) > 50:
        print(f"... and {len(found) - 50} more (fix these first)")
    print("OK: ready to submit" if not found and not a.key else "OK: the format is right" if not found
          else f"{len(found)} problem(s)")
    raise SystemExit(1 if found else 0)
