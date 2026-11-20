# 7_meta_and_other - P048: Fill in the course team submission sheet from project details
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P048. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

i need this answered in simple text =[Team ID	Number of Members	Topic	Prediction Task (Classification or Regression)	Target Column	Data Sources and Number of Files per Source	Dataset Size (rows, MB)	LLM 1 (name and version)	LLM 2 (name and version)	Evaluation Metric	Contact Person (name and email)	Presenters (at least two)] i used claude and gemini neon to build the project

## Response

#### Summary

The image counts come from the project's own records: 18,000 images in the unified dataset, split into 12,405 train, 2,819 validation and 2,776 test.

Three fields could not be filled from what I have:
- **Dataset size in MB:** the images (`data_set/`) are not on this machine.
- **Contact person:** no name or email was provided.
- **Presenters:** no names were chosen in the record.

#### Draft for the submission sheet

```
Team ID: 14
Number of Members: 6
Topic: ShapeSense - recognizing hand-drawn and printed 2D geometric shapes from images
Prediction Task (Classification or Regression): Classification - predict which of 10 shapes an image shows (circle, ellipse, triangle, square, rectangle, pentagon, hexagon, octagon, star, diamond)
Target Column: shape label (10 classes)
Data Sources and Number of Files per Source: Google QuickDraw (7 NDJSON files), Kaggle reevald Geometric Shapes Mathematics (20,000 JPG files), Mendeley El Korchi 2D Geometric Shapes (90,000 PNG files), GitHub frobertpixto Hand-Drawn Shapes (27,292 PNG files): 4 sources in total
Dataset Size (rows, MB): 18,000 images (rows) in the unified dataset, [MB]
LLM 1 (name and version): Claude Opus 5.5 (claude-opus-5-5)
LLM 2 (name and version): Gemini Neon [exact version]
Evaluation Metric: Macro F1 score (10 classes)
Contact Person (name and email): [name, Concordia email]
Presenters (at least two): [at least two of: Ray Ntukanyagwe, Fiacre Byiringiro, Damiano Confuorti, Yahya Belgharbi, Jananaa Mahathevan, Yash Dilipkumar Nathani]
```

#### Before you submit

- **MB:** on the machine that has the data, right-click `data_set\unified` and choose Properties. If you would rather report the raw downloads, use the size of the four source folders instead.

##### Why three fields stay open
The sheet needs facts that are not in the repo: the size of the data on disk here, a contact person's name and email, and the presenters. The draft leaves them as bracketed placeholders so nothing is guessed. The presenter list is drawn from the names in the project, but the record does not say who presents.

##### Checks on the other values
- The image counts (12,405, 2,819 and 2,776) are the split counts recorded after the Quick, Draw! diamond exclusion, so they match the current pipeline.
- The 18,000 total is the unified dataset size after selection. The source file counts are the raw downloads and are reported separately.
- The model names are what the answer gives. The Claude version was written from the model running that session, which the record does not confirm for the original build, so it should be checked against the tool you actually used.
- **Claude version:** I wrote Opus 5.5 because that is the model running this session. If you built the project with a different Claude model, use that one.
- **Gemini version:** "Gemini Neon" is your name for it, and I could not check it. Copy the exact model name and version from the app or API you used.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
