# Checking and scoring your work

This guide shows how to measure your pipeline yourself during the hackathon, with exactly the same
scoring the organisers use at the end: they run your code on 150 new letters and score its output
with `score.py`. You need Python 3.9 or newer and no extra packages.

In every command below, write `python3` instead of `python` on Mac and Linux. On Windows, `python`
or `py` both work.

| script | what it does |
|---|---|
| `check_submission.py` | checks that a file has the right format. It knows nothing about the answers |
| `score.py` | scores your predictions against answer files |
| `split_train.py` | splits the training letters into letters to build with and letters to score on |

The test photos have no answers in this repository, so you can't score a test file yourself.
Instead you score your pipeline on training letters it has not seen, and on the known fakes.

## 1. Get the data

Download `train.zip`, `known_fakes.zip` and `test.zip` from the
[release page](https://github.com/CNielsen94/santa-hackathon/releases/tag/v1.0). Unzip each one into
a folder with the same name inside this repository's folder. On a Mac, double-clicking the zip does
this; on Windows, right-click the zip, choose **Extract All** and keep the suggested folder name.
You should end up with:

```
santa-hackathon/
  train/images/                    500 photos of genuine letters
  train/train.jsonl                their answers
  train/train.csv                  the same answers as a spreadsheet
  known_fakes/images/              15 photos of fake letters
  known_fakes/known_fakes.jsonl    their answers
  known_fakes/known_fakes.csv      the same answers as a spreadsheet
  test/images/                     2,924 photos without answers
  test_ids.txt                     the id of every test photo
```

If you see `train/train/images` instead, move the inner folder's contents up one level.

## 2. The answer files

`.jsonl` means "JSON lines": one JSON object per line, one line per letter. In Python:

```python
import pandas as pd
train = pd.read_json("train/train.jsonl", lines=True)
```

A line from `train/train.jsonl` (shortened):

```json
{"id": "letter-00448b22a084",
 "image": "letter-00448b22a084_0.jpg",
 "language": "en",
 "name": "Jodie",
 "transcription": "Dear Santa,\nI have been very good this yaer...",
 "wishes": [{"written": "scrapbook and glitter pens", "workshop": "arts_music"},
            {"written": "Nintendo Switch", "workshop": "electronics"}],
 "workshops": ["arts_music", "electronics"]}
```

| field | meaning |
|---|---|
| `id` | the photo's file name without `_0.jpg` |
| `name` | the name the letter is signed with |
| `transcription` | the text you can see on the page, with the writer's own spelling ("yaer" stays "yaer"). Crossed-out words are left out |
| `wishes` | each wish as it is written in the letter, and the workshop that makes it |
| `workshops` | the workshops of all the wishes together |

All 500 training letters are genuine. `known_fakes/known_fakes.jsonl` has the same fields for the
15 fake letters, plus `"is_fake": 1`, and no wishes. The test photos also include fake letters, but nobody
knows how many. The 15 known fakes show what fakes can look like, not how many there are.

## 3. Set some letters aside

If you build your pipeline with all 500 letters and then score it on the same letters, the score
looks better than it really is. So split them first:

```
python split_train.py train/train.jsonl --dev 100
```

This writes `train/build.jsonl` (400 **build letters**, to build your pipeline with) and
`train/dev.jsonl` (100 **dev letters**, to score on). Use the same split for the whole hackathon,
so your scores stay comparable.

Treat the known fakes the same way: look at some of them while you build, and keep the rest for
checking. If you tune your fake detection until it catches all 15, those 15 can no longer tell you
how well it works.

## 4. Make a predictions file

Run your pipeline on the photos of the 100 dev letters **and** the 15 known fakes, and write one row
per photo, in exactly the format your code will write
([Submission Format](https://github.com/CNielsen94/santa-hackathon/wiki/Submission-Format)).
You can choose any file name, for example `my_dev_predictions.csv`.

```python
import pandas as pd
predictions.to_csv("my_dev_predictions.csv", index=False, encoding="utf-8")
```

pandas and Python's `csv` module put quotes around fields with commas or line breaks for you. If you
save from Excel, choose **CSV UTF-8**; the scripts accept both commas and semicolons as separators.

## 5. Check the format

For your dev predictions, tell the checker which answer files to expect:

```
python check_submission.py my_dev_predictions.csv --key train/dev.jsonl known_fakes/known_fakes.jsonl
```

To check that your pipeline runs on the full set and writes a valid file, leave out `--key`; it
then expects a row for all 2,924 test photos:

```
python check_submission.py my_team.csv
```

It prints `OK`, or the first 50 problems with their line numbers.

## 6. Score your dev predictions

```
python score.py --key train/dev.jsonl known_fakes/known_fakes.jsonl --submission my_dev_predictions.csv --only-submitted
```

`--key` takes one or more answer files. `--only-submitted` scores only the letters in your file.
The output looks like this (example numbers):

```
**Christmas score: 71.3** (100 = every wish delivered, every fake caught)

| stage | metric | score |
|---|---|---|
| reading | character error rate (lower is better) | 0.061 |
| names | exact match | 74.0% |
| wish extraction | recall / precision | 88.2% / 91.0% |
| routing | right workshop, of the wishes found | 80.5% |
| fake detection | precision / recall / F1 | 84.6% / 73.3% / 78.6% |
| fake detection | ROC AUC | n/a (no fake_score) |
| fake detection | genuine letters wrongly flagged | 3.0% |
| end to end | genuine letters fully right | 41.0% |
```

How to read it:

- **reading**: the **character error rate** counts the characters you got wrong (missing, extra or
  different) per character of the real text. 0.05 means about 1 mistake in 20 characters.
- **names**: share of names exactly right. Case doesn't matter, accents do.
- **wish extraction**: recall is the share of the real wishes you found; precision is the share of
  your wishes that are real. A wish counts as found if your wording is close to the real one
  ("bike" matches "a bike").
- **routing**: of the wishes you found, the share you sent to the right workshop.
- **fake detection**: recall is the share of the known fakes you marked as fake. **Genuine letters
  wrongly flagged** is the share of dev letters you marked as fake by mistake. Precision depends on
  how many fakes are in the mix: here about 1 letter in 8 is fake, and other mixes have a different
  share, so precision will differ there.
- **Christmas score**: the number the ranking uses (see the README). Your dev mix is not the mix
  of the final letters, so use it to compare versions of your own pipeline, not to predict your final
  score.

## 7. Hand in

On the final day you hand in the code of your pipeline, not a CSV. The organisers run it on 150 new
letters and score the output with `score.py`. The full requirements are on the
[Submission Format](https://github.com/CNielsen94/santa-hackathon/wiki/Submission-Format) page.

Practise it. Run your entry point (`run.py`, or the notebook) on a folder of your dev photos, or on
the 15 known fakes. Then check the CSV with `check_submission.py --key ...` (step 5) and score it with
`score.py --only-submitted` (step 6). That is exactly what the organisers do with the secret letters.

Running a pipeline over all 2,924 test photos can take hours. Save results as you go (for example one line
per photo to a file), so a crash or a disconnected session doesn't cost you everything.
