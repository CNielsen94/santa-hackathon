"""Split train.jsonl into a part to build your pipeline with and a part to test it on.

    python split_train.py train/train.jsonl --dev 100

writes train/build.jsonl (letters to learn from) and train/dev.jsonl (letters to score on).
The same --seed always gives the same split.
"""
import argparse
import json
import random
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("train", help="path to train.jsonl")
    ap.add_argument("--dev", type=int, default=100, help="how many letters to keep aside for scoring")
    ap.add_argument("--seed", default="santa")
    a = ap.parse_args()
    path = Path(a.train)
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    random.Random(a.seed).shuffle(rows)
    dev, build = rows[:a.dev], rows[a.dev:]
    for name, part in (("build.jsonl", build), ("dev.jsonl", dev)):
        with open(path.parent / name, "w", encoding="utf-8") as fh:
            for r in part:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{len(build)} letters in {path.parent / 'build.jsonl'}, {len(dev)} in {path.parent / 'dev.jsonl'}")


if __name__ == "__main__":
    main()
