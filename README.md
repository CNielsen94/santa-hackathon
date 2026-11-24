# Letters to Santa: the hackathon

Santa's mail room is drowning. Thousands of handwritten letters have been
photographed, and the elves need a pipeline that, for each photo:

1. **reads** the letter (it may be in any of 18 languages and scripts),
2. **finds the writer's name** as signed,
3. **decides whether the letter is fake**,
4. **sends every wish** in a genuine letter to the right workshop
   ([workshops.json](workshops.json)). Fake letters go to no workshop.

Not all of Santa's mail comes from children, and nobody knows how much of it is
fake. The elves have checked a sample of letters by hand and know them to be
genuine, and they have caught a few fakes: 15 of them. That's too few to learn
from on their own, but enough to test your ideas on. Fake detection works like
fraud detection: learn what genuine mail looks like, flag what doesn't fit, and
use the known fakes to check that you catch them.

## Data

Download both files from the [Releases](../../releases) page:

| file | contents |
|---|---|
| `train.zip` (about 210 MB) | 500 genuine letters: `images/` plus `train.jsonl` and `train.csv` with every answer: the text visible on the page, the name, and each wish as written with its workshop |
| `known_fakes.zip` (about 6 MB) | 15 confirmed fakes: `images/` plus `known_fakes.jsonl` and `known_fakes.csv` with the text visible on the page and the name they signed with. They are not part of the test set |
| `test.zip` (about 1.2 GB) | 2,924 photos with no answers. Your score comes from these |

`test_ids.txt` lists every test letter. A letter's id is its file name without
`_0.jpg`.

## What to hand in

One CSV file with a row for every test letter:

```
id,is_fake,name,workshops,transcription,wishes,fake_score
letter-0a1b2c3d4e5f,0,Emma,toy_shop;outdoor,"Dear Santa, I want a doll and a bike...",a doll=>toy_shop;a bike=>outdoor,0.04
letter-6a7b8c9d0e1f,1,,,"Hand over the sleigh schedule...",,0.97
```

- `is_fake`: 1 for a fake letter, 0 for a genuine one
- `name`: the name as signed (case doesn't matter, accents do)
- `workshops`: every workshop the letter's wishes go to, separated by `;`, empty for fakes
- `transcription`: the text you read on the page, as written (keep the writer's spelling)
- `wishes`: each wish as written, with its workshop: `wish=>workshop`, separated by `;`, empty for fakes
- `fake_score` (optional): how likely you think the letter is fake, from 0 to 1

Use quotes around any field that contains a comma or a line break (any CSV
library does this for you).

Check your file before submitting (and see [SCORING.md](SCORING.md) for how to score your
pipeline on training letters yourself, with the same metrics as the final ranking):

```
python check_submission.py my_team.csv
```

## Scoring

Every part of your pipeline gets its own score, so you can see where it loses points:

| stage | metric |
|---|---|
| reading | character error rate of `transcription` (lower is better) |
| names | share of names exactly right |
| wish extraction | recall and precision of your wish phrases (close spellings count) |
| routing | of the wishes you found, the share sent to the right workshop |
| fake detection | precision, recall and F1; ROC AUC if you give `fake_score` |
| end to end | share of genuine letters fully right: not flagged, every wish found and routed, name right |

Your rank comes from one number, the **Christmas score**: points as a percentage
of the best possible total.

| what happens | points |
|---|---|
| a real wish reaches the right workshop | +1 |
| a real wish is lost or goes to the wrong workshop | 0 |
| a real letter is flagged as fake (a child gets nothing) | −1 for each of its wishes |
| a fake letter is caught | +1 |
| a fake letter slips through | −2 |

Flag too much and children lose their presents; flag too little and the Grinch
gets in. Listing a wish more than once, or under several workshops, earns nothing
extra.

A scoring page will follow (link from the organisers). Each team will get a
limited number of scores per day. During the hackathon your score will come from
one half of the test letters; the final ranking uses the other half.
