![Santa's post office at night](assets/banner.jpg)
(STILL IN DEVELOPMENT - UPDATES INCOMING)
# Letters to Santa: the hackathon

Santa's mail room is drowning. Thousands of handwritten letters have been photographed, and the
elves need a pipeline that does four things for each photo:

1. **reads** the letter (it can be in any of 18 languages),
2. **finds the name** the letter is signed with,
3. **decides whether the letter is fake**,
4. **sends every wish** in a genuine letter to the right workshop. A fake letter gets no wishes.

The full guide is in the **[wiki](https://github.com/CNielsen94/santa-hackathon/wiki)**. Start with
[Getting Started](https://github.com/CNielsen94/santa-hackathon/wiki/Getting-Started).

## Data

Download the three files from the
[release page](https://github.com/CNielsen94/santa-hackathon/releases/tag/v1.0):

| file | size | contents |
|---|---|---|
| `train.zip` | 210 MB | 500 genuine letters: photos and their answers |
| `known_fakes.zip` | 6 MB | 15 fake letters the elves caught: photos, their text and the name they are signed with. They are not in the test set |
| `test.zip` | 1.2 GB | 2,924 photos without answers, to build and test with. You are not ranked on these |

Unzip each file into a folder with the same name (`train`, `known_fakes`, `test`) inside this
repository's folder. Details: [Data](https://github.com/CNielsen94/santa-hackathon/wiki/Data).

## What you hand in

On the final day you hand in the **code** of your pipeline. The organisers run it on 150 new
letters nobody has seen (they are not in the release) and score the result. The Christmas score on
those 150 letters decides the ranking, and the results are revealed at the end.

Hand in one of:

1. A folder (a zip, or a link to a GitHub repository the organisers can read) with `run.py` at the
   top level and a `requirements.txt`. The organisers run it like this:

   ```
   python run.py --images path/to/photos --out predictions.csv
   ```

2. A Colab notebook (`.ipynb`) whose first code cell sets `IMAGES_DIR` and `OUTPUT_CSV`. The
   organisers set them and choose Run all.

Your code reads every photo in the folder it is given and writes one row per photo, in this format:

```
id,is_fake,name,workshops,transcription,wishes,fake_score
letter-0a1b2c3d4e5f,0,Emma,outdoor;toy_shop,"Dear Santa, I want a doll and a bike...",a doll=>toy_shop;a bike=>outdoor,0.04
letter-6a7b8c9d0e1f,1,Grinchy,,"Hand over the sleigh schedule...",,0.97
```

Every column, and everything your code must do to run on its own (model weights, API keys, run
time), is on the
[Submission Format](https://github.com/CNielsen94/santa-hackathon/wiki/Submission-Format) page. The
deadline and how to send your code are given at the start of the hackathon.

Practise the hand-in: run your code on a folder of your dev photos, then check and score the CSV
(see [Scoring Yourself](https://github.com/CNielsen94/santa-hackathon/wiki/Scoring-Yourself)).
To check that your pipeline runs on all 2,924 test photos and writes a valid file, use
`python check_submission.py my_team.csv`. (On Mac and Linux, write `python3` instead of `python`.)

## How you are scored

Each part of your pipeline gets its own score, and the ranking uses one number, the **Christmas
score**: your points divided by the most points possible, times 100.

| what happens | points |
|---|---|
| a wish in a genuine letter reaches the right workshop | +1 |
| a wish in a genuine letter is missed or goes to the wrong workshop | 0 |
| a genuine letter is marked as fake | −1 for each of its wishes |
| a fake letter is marked as fake | +1 |
| a fake letter is not marked as fake | −2 |

You can measure your own pipeline during the hackathon with the same scoring script
(`score.py`): see [Scoring Yourself](https://github.com/CNielsen94/santa-hackathon/wiki/Scoring-Yourself)
or [SCORING.md](SCORING.md). On the final day the organisers score the output of your code on the 150
new letters with the same script.

## Rules

Anything goes: any language, library, model, service or AI assistant. The code just has to run as described on the hand-in page.
