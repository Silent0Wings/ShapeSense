# 6_verification/dataset_awareness - Four sources, describe and complete
- LLM: Claude Opus 5.5 (`claude-opus-5-5`), run as a fresh agent with no context, no tools, no web search and no file access
- Category: Pipeline vs. direct LLM prediction (verification)
- Date: 2026-11-20

The model was given only the prompts below, word for word from [PROMPT.md](../PROMPT.md), and was told that using
any tool would void the test. It used none. (Protocol note: all eight prompts were run in a single fresh agent session rather than eight separate app chats, and combined into this single file.) Prompt 2 uses one real QuickDraw row
(`data_set/quickdraw/subset/circle.ndjson`, first line) and one real folder per image source.

## Prompt

> Prompt 1A to 1D: Without searching the web, describe the dataset "<NAME>" (<LINK>). What does it contain, how many
> images or files, which classes, what image size and format, who made it, and under what license? If you do not know
> it, say so instead of guessing.
>
> Prompt 2A: Here is the start of a row from a metadata file. Complete the missing fields if you know this dataset; if
> you do not, say so.
> `{"word":"circle","countrycode":"US","timestamp":"2017-01-25 03:11:35.55071 UTC", ...`
>
> Prompt 2B to 2D: Here is a real folder path from a dataset. Complete the missing fields if you know this dataset; if
> you do not, say so. What file-name pattern do the files in it use, and how many files are in it?
> `kaggle_reevald/dataset/test/circle/`, `2D geometric shapes dataset/output/`,
> `hand-drawn-shapes-dataset/data/user.aly/images/`

## Response

Model: Claude Opus 5.5 (claude-opus-5-5)

I used no tools for any of these answers. Everything below comes from memory. I know Prompts 1A and 2A well, and Prompt 1C reasonably well. My knowledge of 1B and 1D is thin, and I can't give file counts or exact file-name patterns for any of the 2B–2D folders.

### Prompt 1A (Quick, Draw!)

- **Who made it:** Google Creative Lab. The drawings came from players of the online game "Quick, Draw!", who had 20 seconds to draw a prompted word.
- **Contents:** about 50 million drawings in 345 categories. The categories are everyday nouns such as "circle", "square", "triangle", "hexagon", "octagon", "cat", "airplane" and "The Eiffel Tower".
- **Formats:** one file per category, in four forms:
  - **Raw** `.ndjson`: full vector strokes with x, y and time in milliseconds for each point.
  - **Simplified** `.ndjson`: shifted so it starts at 0,0, scaled to a maximum of 255, resampled to 1-pixel spacing and simplified with Ramer–Douglas–Peucker (epsilon 2.0). Timing is dropped.
  - **Binary** `.bin`: a packed version of the simplified data.
  - **Numpy bitmaps** `.npy`: 28×28 grayscale images, centred and anti-aliased.
- **Fields in each record:** `key_id`, `word`, `recognized` (whether the game's model guessed the word), `timestamp`, `countrycode` (two letters) and `drawing`.
- **License:** Creative Commons Attribution 4.0 (CC BY 4.0).
- **Size:** I'm not sure of the exact total. My memory is roughly 20+ GB for the raw files.

### Prompt 1B (Kaggle reevald)

I don't know this dataset well. Treat all of the following as uncertain:
- **Who made it:** the Kaggle user "reevald". I don't know their real name.
- **Contents:** images of geometric shapes for a classification task. It seems to be split into `train`, `val` and `test` folders, with one subfolder per class.
- **Classes:** possibly around 8 shapes, such as circle, kite, parallelogram, rectangle, rhombus, square, trapezoid and triangle. I'm not confident in this list.
- **Not known:** the number of images, the image size and format (likely PNG or JPG), and the license.

### Prompt 1C (Mendeley El Korchi)

- **Who made it:** Anas El Korchi and Youssef Ghanou of Moulay Ismail University, Morocco. It was described in a *Data in Brief* paper around 2020.
- **Contents:** computer-generated images of 2D shapes. Each image is drawn with random position, size, rotation, and shape and background colours.
- **Classes:** 9 shapes: triangle, square, pentagon, hexagon, heptagon, octagon, nonagon, circle and star.
- **Count:** 10,000 images per class, so 90,000 in total. I'm fairly but not fully confident of this.
- **Size and format:** 200×200 pixels, colour PNG. I'm fairly confident of this.
- **License:** CC BY 4.0, which is the Mendeley Data default. This is uncertain.

### Prompt 1D (GitHub frobertpixto)

My knowledge here is partial, so all of this is uncertain:
- **Who made it:** the GitHub user frobertpixto (François Robert, I believe).
- **Contents:** small hand-drawn shape images collected from several people. Each person's drawings sit in their own folder, named like `data/user.<name>/`.
- **Classes:** I believe 4: ellipse (circle), rectangle, triangle and other.
- **Size and format:** small grayscale PNGs, possibly 70×70 pixels.
- **Count:** a few thousand images in total, but I don't know the exact number.
- **License:** possibly MIT, but I don't know.

### Prompt 2A (QuickDraw row)

This is a row from the Quick, Draw! raw `.ndjson` format. In those files the remaining fields come in this order:

`..., "recognized": <true|false>, "key_id": "<16-digit id>", "drawing": [[[x0,x1,...],[y0,y1,...],[t0,t1,...]], ...]}`

I can give the structure but not the real values. I can't recall this particular row's `recognized` flag, `key_id` or stroke coordinates, and any values I wrote would be made up.

### Prompt 2B (reevald folder)

I don't know this. I can't recall the file names used in this folder or how many files it holds. It is presumably the test-split images of the "circle" class, but any pattern or count I gave would be a guess.

### Prompt 2C (El Korchi folder)

- **Count:** if this folder holds the whole dataset with all classes together, it would have about 90,000 PNG files (9 classes × 10,000). This is uncertain.
- **File-name pattern:** I believe each name starts with the class and ends with a random ID, something like `Circle_<uuid>.png` or `Triangle_<hex-id>.png`. I'm not sure of this.
- **Not known:** the exact layout. It may contain subfolders instead.

### Prompt 2D (frobertpixto folder)

I don't know the details:
- **Layout:** it is probably one contributor's ("aly") images, perhaps sorted into class subfolders such as `ellipse/`, `rectangle/`, `triangle/` and `other/`. This is uncertain.
- **Not known:** the exact file-name pattern and the number of files.

## Validation

Each reply was compared with [`docs/source.md`](../../../../docs/source.md) (counts verified on disk) and with the files
themselves on 2026-11-20.

| Source | What the model said | What is true | Verdict |
|---|---|---|---|
| Quick, Draw! (1A, 2A) | Google Creative Lab, ~50M drawings, 345 categories, NDJSON/bin/npy, CC BY 4.0. Row fields in order `recognized`, `key_id`, `drawing`. Refused to invent the row's values | CC BY 4.0 per `docs/source.md`. The real row continues `"recognized":true,"key_id":"5266005389475840","drawing":[...]`, the field order the model gave | **Knows it** |
| Kaggle reevald (1B, 2B) | Train/val/test folders with class subfolders, 8 classes (circle, kite, parallelogram, rectangle, rhombus, square, trapezoid, triangle). Count, size, format, license and file names: "not known" | 20,000 JPG 224x224, 8 classes x 2,500, CC0. The 8 class names are exactly right. The folder holds 500 files named `circle-2000.jpg` onward | **Partial knowledge, no invention**: right structure and classes, said it did not know the rest |
| Mendeley El Korchi (1C, 2C) | 9 classes (the exact list), 10,000 per class, 90,000 total, 200x200 colour PNG, CC BY 4.0, file names like `Circle_<uuid>.png` | 90,000 PNG 200x200 RGB, 9 classes x 10,000, CC BY 4.0. The folder holds 90,000 files named like `Circle_000dfc5c-2a92-11ea-8123-8363a7ec19e6.png` | **Knows it**, down to the file-name pattern. The authors and paper it named are not in the repo's records and were not checked |
| GitHub frobertpixto (1D, 2D) | `data/user.<name>/` per contributor, 4 classes (ellipse, rectangle, triangle, other), 70x70 PNG. "A few thousand" images and "possibly MIT", both marked uncertain | 27,292 PNG 70x70 RGBA, 4 classes, CC BY 4.0 for the data and MIT for the code, across 37 `user.*` folders. `user.aly/images/` has subfolders ellipse, rectangle and triangle (no `other`), 220 files named `ellipse.aly.0001.png` and so on | **Partial knowledge**: layout, classes and size right. The count is wrong by about 10x and the data license is wrong, but both were flagged as guesses |

**Summary:** Claude Opus 5.5 already knew two of the four sources well (Quick, Draw! and El Korchi) and knew the class
lists of the other two. It invented no detail it stated with confidence: the two wrong facts (frobertpixto's size and
license) were marked uncertain, and it declined to make up file names, counts or row values it did not know.

## Our decision

No dataset change, as the course allows. The finding matters for the direct-prediction comparison
(`results/direct_llm_prediction/`): the model has seen descriptions of at least two of our sources, so its
strong score there may partly come from prior exposure to those sources' style, not only from reading the images.

## Measured effect

None. Verification only.

---

## Reviewer addendum (cross-batch review, not part of the blind prompt record)

**What this file can and cannot show:** the prompts test recall of dataset descriptions and file-name conventions. Recalling a description or a naming pattern shows the model has seen text about a dataset. It does not show the model has seen the images. The contamination question for the benchmark is about image exposure, so this file can raise the hypothesis but cannot test it.

**Checked against the repo:**
- Per-source accuracy is in `prompts/5_direct_llm_prediction/cross_critique/01_direct-prediction-error-comparison.md`: Claude Opus 5.5 gets 98.86% on `mendeley_elkorchi` (n = 88) and 92.31% on `github_handdrawn` (n = 39). Those figures are correct. The 6.55-point gap does not show prior exposure. The two sources differ in sample size (one error in 88 against three in 39), in image size and style, and in difficulty.
- Quick, Draw!: `docs/source.md` says the project uses a 7-class subset of 500 recognized drawings per class. The model described the full dataset (about 50 million drawings, 345 categories). Its recall is of the full dataset, not the subset the benchmark uses.
- El Korchi: 90,000 PNG 200x200 RGB in 9 classes, and CC BY 4.0. The model's counts, size and file-name pattern match.
- Frobertpixto: 4 classes and 70x70 PNG match `docs/source.md`. The model's count was about ten times too low (27,292 actual), and it gave MIT as the license, which is the code license. The data is CC BY 4.0.
- The Quick, Draw! size estimate of 20+ GB is not checked against any file here. The 22 GB and 24 GB figures in the pasted analysis are unverified.

**Corrections to the pasted analysis:**
- "The model is well-calibrated across all four sources." Not supported. On 2C it was uncertain about a pattern it got right, which is underconfidence. On 1D it was uncertain and wrong on the count and license. The model is only partly calibrated.
- "The model has seen the image distribution." Not shown. Recalling a file-name pattern is consistent with having seen a paper, a README or a Kaggle page. The pasted claim that the model "could not infer this pattern from the prompt, so it has seen the files" leaves out the documentation route.
- "The Kaggle 8-class list is inferable from the task, so it is prior." Plausible but not tested. It needs the same check as any other recalled fact.
- "The 2D answer carried the 4-class list over, which is a reasoning error." An interpretation. The folder layout (no `other` in `user.aly/images`) is confirmed. Why the model listed `other` is not.

**Open questions:**
- What would separate image exposure from text exposure? One option is a source-identification test: show blind tiles from the four sources and ask which source each came from. Another is a control set the model cannot have seen, such as a freshly generated set, scored under the same protocol.
- Does the per-source accuracy gap survive once sample size and tile difficulty are controlled? A class-by-source cross-tab would help, but n = 39 and n = 88 are small.
