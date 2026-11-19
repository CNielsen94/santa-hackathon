# Letters to Santa: the hackathon

Santa's mail room is drowning. Thousands of handwritten letters have been
photographed, and the elves need a pipeline that, for each photo:

1. **reads** the letter (it may be in any of 18 languages and scripts),
2. **finds the writer's name** as signed,
3. **decides whether the letter is fake**,
4. **sends every wish** in a genuine letter to the right workshop
   ([workshops.json](workshops.json)). Fake letters go to no workshop.

Not all of Santa's mail comes from children. Nobody knows how much of it is
fake, or what the fakes look like: no one has caught one yet. What the elves
do have is a sample of letters they checked by hand and know to be genuine.
Fake detection works like fraud detection: learn what genuine mail looks like,
then flag what doesn't fit.

## Data

Download both files from the [Releases](../../releases) page:

| file | contents |
|---|---|
| `train.zip` (about 210 MB) | 500 genuine letters: `images/` plus `train.jsonl` and `train.csv` with every answer: the text visible on the page, the name, and each wish as written with its workshop |
| `test.zip` (about 1.2 GB) | 2,923 photos with no answers. Your score comes from these |

`test_ids.txt` lists every test letter. A letter's id is its file name without
`_0.jpg`.

## What to hand in

One CSV file with a row for every test letter:

```
id,is_fake,name,workshops
letter-0a1b2c3d4e5f,0,Emma,toy_shop;electronics
letter-6a7b8c9d0e1f,1,,
```

- `is_fake`: 1 for a fake letter, 0 for a genuine one
- `name`: the name as signed (case doesn't matter, accents do)
- `workshops`: every workshop the letter's wishes go to, separated by `;`,
  and empty for fakes
- optional: a `transcription` column with what you read, scored as well

Check your file before submitting:

```
python check_submission.py my_team.csv
```

## Scoring

Each stage is scored on its own:

| stage | metric |
|---|---|
| reading | character error rate of `transcription` (optional) |
| name | share of names exactly right |
| fake detection | precision, recall and F1 |
| workshops | F1 over the workshops of genuine letters |
| end to end | share of genuine letters that are fully right: not flagged, every workshop right |

A scoring page will follow (link from the organisers). Each team will get a
limited number of scores per day. During the hackathon your score will come from
one half of the test letters; the final ranking uses the other half.
