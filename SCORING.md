# Checking and scoring your work

Two tools come with this repository. Both need only Python 3.9 or newer, no extra packages.

| tool | what it does |
|---|---|
| `check_submission.py` | checks that your submission file has the right format. It knows nothing about the answers. |
| `score.py` | scores predictions against an answer key, with the same metrics the organisers use for the final ranking |

The test letters have no answer key in this repository, so you can't score them yourself.
Instead you score your pipeline on training letters it hasn't seen.

## 1. Get the data

Download `train.zip` and `test.zip` from the Releases page and unzip them in this folder:

```
santa-hackathon/
  train/images/        500 photos
  train/train.jsonl    the answers for those photos
  train/train.csv      the same answers as a spreadsheet
  test/images/         2,924 photos, no answers
```

## 2. The answer format (`train.jsonl`)

One letter per line. Each line is a JSON object like this (shortened):

```json
{"id": "letter-00448b22a084",
 "image": "letter-00448b22a084_0.jpg",
 "language": "en",
 "name": "Maya",
 "transcription": "Dear Santa,\nI have been very good this yaer...",
 "wishes": [{"written": "scrapbook and glitter pens", "workshop": "arts_music"},
            {"written": "a scooter", "workshop": "outdoor"}],
 "workshops": ["arts_music", "outdoor"]}
```

- `id`: the photo's file name without `_0.jpg`
- `transcription`: the text you can see on the page, with the writer's own spelling
  ("yaer" stays "yaer"); crossed-out words are left out
- `name`: the name the letter is signed with
- `wishes`: each wish as it is written in the letter, and the workshop that makes it
- `workshops`: the workshops of all the wishes together

All training letters are genuine. Some test letters are not.

## 3. Keep some training letters aside

If you build your pipeline with all 500 letters and then score it on the same letters, the
score will look better than it really is. Keep some aside first:

```
python split_train.py train/train.jsonl --dev 100
```

This writes `train/build.jsonl` (400 letters to build with) and `train/dev.jsonl` (100 letters
to score on). Use the same split all week so your scores stay comparable.

## 4. Make a predictions file

Run your pipeline on the photos of the letters in `train/dev.jsonl` and write one CSV row per
letter, in exactly the format you will hand in (see the README):

```
id,is_fake,name,workshops,transcription,wishes,fake_score
letter-00448b22a084,0,Maya,arts_music;outdoor,"Dear Santa,
I have been very good this yaer...",scrapbook and glitter pens=>arts_music;a scooter=>outdoor,0.05
```

- Put quotes around a field with a comma or a line break in it. Python's `csv` module, pandas
  `to_csv` and spreadsheet programs all do this for you.
- `wishes` pairs each wish with its workshop as `wish=>workshop`, separated by `;`.
- `fake_score` is optional.

## 5. Check the format

```
python check_submission.py my_test_submission.csv
```

It prints `OK: ready to submit`, or a list of problems with their line numbers. It expects a
row for every **test** letter, so use it on your test submission. On a dev-predictions file it
will only complain that test letters are missing.

## 6. Score your dev predictions

```
python score.py --key train/dev.jsonl --submission my_dev_predictions.csv --only-submitted
```

`--only-submitted` scores only the letters in your file. The output looks like this (example numbers):

```
**Christmas score: 71.3** (100 = every wish delivered, every fake caught)

| stage | metric | score |
|---|---|---|
| reading | character error rate (lower is better) | 0.061 |
| names | exact match | 74.0% |
| wish extraction | recall / precision | 88.2% / 91.0% |
| routing | right workshop, of the wishes found | 80.5% |
| fake detection | precision / recall / F1 | 0.0% / 0.0% / 0.0% |
| fake detection | ROC AUC | n/a (no fake_score) |
| fake detection | genuine letters wrongly flagged | 3.0% |
| end to end | genuine letters fully right | 41.0% |
```

How to read it:

- **reading**: how many characters are wrong per character of the real text. 0.05 means
  about 1 mistake in 20 characters.
- **names**: case doesn't matter, accents do.
- **wish extraction**: recall is the share of the real wishes you found; precision is the share
  of your wishes that are real. Close spellings count ("bike" matches "a bike").
- **routing**: only for the wishes you found, so it measures routing on its own.
- **fake detection**: the training letters are all genuine, so precision, recall and AUC show 0
  or n/a here. The useful number is **genuine letters wrongly flagged**: every genuine letter
  you flag costs a child all their presents. How well you catch fakes only shows in the final
  ranking.
- **Christmas score**: the number the ranking uses (see the README). On dev letters it can
  only reward wishes, so it looks higher than it will on the test set.

## 7. Hand in

Run your pipeline on all of `test/images`, write the CSV, check it with
`check_submission.py`, and send it to the organisers.
