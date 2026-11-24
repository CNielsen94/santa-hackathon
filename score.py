"""Score your predictions against an answer key, with the same metrics the organisers use.

    python score.py --key train/dev.jsonl --submission my_dev_predictions.csv --only-submitted

Columns: id, is_fake, name, workshops, transcription, wishes (`text=>workshop; ...`),
and optionally fake_score (0-1). A test letter missing from the submission counts as
read wrong: not fake, no name, no text, no wishes.

Stage metrics (one per part of the pipeline):
    reading          character error rate of the transcription
    names            share of names exactly right (case-insensitive)
    wish extraction  recall and precision of the wish phrases, fuzzy-matched
    routing          of the correctly found wishes of genuine letters, the share sent to the right workshop
    fake detection   precision, recall and F1 at the team's threshold; ROC AUC from fake_score if given

Headline: the Christmas score, as a percentage of the best possible total.
    real wish reaches the right workshop           +1
    real wish lost or sent to the wrong workshop    0
    real letter flagged as fake                    -1 per wish in it
    fake caught                                    +1
    fake missed                                    -2
"""
import argparse
import csv
import difflib
import json
import re
import statistics
import unicodedata

POINTS = {"delivered": 1, "flagged_real_wish": -1, "fake_caught": 1, "fake_missed": -2}
MATCH = 0.6     # fuzzy similarity for a wish phrase to count as found


def strip_vowel_marks(text):
    """Remove optional vowel marks (Arabic harakat, Hebrew niqqud): children rarely write them."""
    return "".join(c for c in text if not (0x064B <= ord(c) <= 0x0652 or ord(c) == 0x0670
                                           or 0x05B0 <= ord(c) <= 0x05C7))


def norm(text):
    return re.sub(r"\s+", " ", strip_vowel_marks(text or "")).strip()


def error_rate(truth, pred):
    """Edit distance divided by the length of the truth."""
    prev = list(range(len(pred) + 1))
    for i, a in enumerate(truth, 1):
        cur = [i]
        for j, b in enumerate(pred, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a != b)))
        prev = cur
    return prev[-1] / max(1, len(truth))


def norm_name(name):
    return unicodedata.normalize("NFKC", strip_vowel_marks(name or "")).casefold().strip(" .,!")


def norm_wish(text):
    return " ".join(unicodedata.normalize("NFKC", text or "").casefold().split())


def parse_wishes(cell):
    """`bike=>outdoor; doll=>toy_shop` -> [("bike", "outdoor"), ("doll", "toy_shop")]."""
    pairs = []
    for part in (cell or "").split(";"):
        if not part.strip():
            continue
        text, _, shop = part.partition("=>")
        pairs.append((text.strip(), shop.strip()))
    return pairs


def load_submission(path):
    with open(path, encoding="utf-8", newline="") as fh:
        rows = {}
        for r in csv.DictReader(fh):
            score = (r.get("fake_score") or "").strip()
            rows[r["id"].strip()] = {
                "is_fake": str(r.get("is_fake", "")).strip().lower() in ("1", "true", "yes"),
                "name": r.get("name", ""),
                "workshops": {w.strip() for w in (r.get("workshops") or "").split(";") if w.strip()},
                "transcription": r.get("transcription") or "",
                "wishes": parse_wishes(r.get("wishes")),
                "fake_score": float(score) if score else None,
            }
    return rows


def similarity(a, b):
    a, b = norm_wish(a), norm_wish(b)
    if not a or not b:
        return 0.0
    if a in b or b in a:
        return 1.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def match_wishes(true_wishes, submitted):
    """Pair each true wish with at most one submitted wish: best similarity first, and on a tie
    the wish the team listed first (so listing one wish under every workshop earns nothing extra)."""
    candidates = sorted((-similarity(t["written"], s[0]), j, i) for i, t in enumerate(true_wishes)
                        for j, s in enumerate(submitted))
    used_t, used_s, pairs = set(), set(), {}
    for neg_sim, j, i in candidates:
        sim = -neg_sim
        if sim < MATCH:
            break
        if i in used_t or j in used_s:
            continue
        used_t.add(i); used_s.add(j); pairs[i] = j
    return pairs


def f1(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return p, r, (2 * p * r / (p + r) if p + r else 0.0)


def roc_auc(labels, scores):
    """Probability that a random fake gets a higher fake_score than a random genuine letter."""
    pos = [s for l, s in zip(labels, scores) if l]
    neg = [s for l, s in zip(labels, scores) if not l]
    if not pos or not neg:
        return None
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def score(key_rows, sub):
    empty = {"is_fake": False, "name": "", "workshops": set(), "transcription": "", "wishes": [], "fake_score": None}
    tp = fp = fn = 0
    names, cers = 0, []
    found = true_total = submitted_total = 0
    routed_right = 0
    points = best = 0
    fully_right = n_real = 0
    labels, fake_scores, all_scored = [], [], True
    for t in key_rows:
        s = sub.get(t["id"], empty)
        fake = bool(t.get("is_fake", 0))     # train.jsonl has no flag: every letter is genuine
        tp += fake and s["is_fake"]; fp += (not fake) and s["is_fake"]; fn += fake and not s["is_fake"]
        names += norm_name(s["name"]) == norm_name(t["name"])
        cers.append(min(1.0, error_rate(norm(t["transcription"]), norm(s["transcription"]))))
        labels.append(fake)
        fake_scores.append(s["fake_score"])
        all_scored &= s["fake_score"] is not None
        if fake:
            best += POINTS["fake_caught"]
            points += POINTS["fake_caught"] if s["is_fake"] else POINTS["fake_missed"]
            continue
        n_real += 1
        wishes = t["wishes"]
        best += POINTS["delivered"] * len(wishes)
        pairs = match_wishes(wishes, s["wishes"])
        true_total += len(wishes); submitted_total += len(s["wishes"]); found += len(pairs)
        right = sum(s["wishes"][j][1] == wishes[i]["workshop"] for i, j in pairs.items())
        routed_right += right
        if s["is_fake"]:
            points += POINTS["flagged_real_wish"] * len(wishes)
        else:
            points += POINTS["delivered"] * right
            fully_right += right == len(wishes) and len(pairs) == len(s["wishes"]) and \
                norm_name(s["name"]) == norm_name(t["name"])
    n = len(key_rows)
    fp_, fr_, ff_ = f1(tp, fp, fn)
    return {
        "letters": n, "submitted": sum(t["id"] in sub for t in key_rows),
        "reading_cer": statistics.mean(cers) if cers else None,
        "name_accuracy": names / n,
        "wish_recall": found / true_total if true_total else 0.0,
        "wish_precision": found / submitted_total if submitted_total else 0.0,
        "routing_accuracy": routed_right / found if found else 0.0,
        "fake_precision": fp_, "fake_recall": fr_, "fake_f1": ff_,
        "false_alarm_rate": fp / n_real if n_real else 0.0,
        "fake_auc": roc_auc(labels, fake_scores) if all_scored else None,
        "christmas_score": 100 * points / best if best else 0.0,
        "real_letters_fully_right": fully_right / n_real if n_real else 0.0,
    }


def as_markdown(s):
    auc = "n/a (no fake_score)" if s["fake_auc"] is None else f"{s['fake_auc']:.3f}"
    return "\n".join([
        f"letters scored: {s['letters']} (submitted: {s['submitted']})", "",
        f"**Christmas score: {s['christmas_score']:.1f}** (100 = every wish delivered, every fake caught)", "",
        "| stage | metric | score |", "|---|---|---|",
        f"| reading | character error rate (lower is better) | {s['reading_cer']:.3f} |",
        f"| names | exact match | {s['name_accuracy']:.1%} |",
        f"| wish extraction | recall / precision | {s['wish_recall']:.1%} / {s['wish_precision']:.1%} |",
        f"| routing | right workshop, of the wishes found | {s['routing_accuracy']:.1%} |",
        f"| fake detection | precision / recall / F1 | {s['fake_precision']:.1%} / {s['fake_recall']:.1%} / {s['fake_f1']:.1%} |",
        f"| fake detection | ROC AUC | {auc} |",
        f"| fake detection | genuine letters wrongly flagged | {s['false_alarm_rate']:.1%} |",
        f"| end to end | genuine letters fully right | {s['real_letters_fully_right']:.1%} |",
    ])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--key", required=True)
    ap.add_argument("--submission", required=True)
    ap.add_argument("--only-submitted", action="store_true", help="score only the letters in the submission")
    ap.add_argument("--json", action="store_true", help="print the scores as JSON")
    a = ap.parse_args(argv)
    with open(a.key, encoding="utf-8") as fh:
        key_rows = [json.loads(line) for line in fh if line.strip()]
    sub = load_submission(a.submission)
    if a.only_submitted:
        key_rows = [t for t in key_rows if t["id"] in sub]
    s = score(key_rows, sub)
    print(json.dumps(s, indent=1) if a.json else as_markdown(s))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
