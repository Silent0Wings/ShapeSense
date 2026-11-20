# 7_meta_and_other - P061: Filling attribution worksheet rows from the user's own account
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P061. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

this was done by neon =[

<pasted_content id="588d">
CRISP-DM evaluation

Robustness check
The same images twice: clean, and with rotation, noise, blur, compression, lighting shifts and occlusion added. Every model scores identical saved images.

sealed holdout read once
validation check kept for comparison
How this test differs from training
Design, data handling and storage behind the results above, summarised from the source repository at the snapshot commit. Open a section to read it.

Training augmentation against test damage
Sealed holdout 2 (the verdict)
Validation check, for comparison
Sealed holdout 2: clean against damaged
4,500 images that were never read before, perturbed once inside Stage 5 and saved. This is the data behind the pre-registered iteration 3 verdict.

Arm	Clean accuracy %	Rotated drop	Noisy drop
Real only (A0)	97.2 ± 0.1	17.7 ± 0.6	24.0 ± 1.7
Real + augmented (A1)	97.8 ± 0.1	11.4 ± 0.2	15.9 ± 2.3
Real + synthetic (B)	97.5 ± 0.1	8.7 ± 0.4	16.3 ± 3.2
Full mix (A2)	98.0 ± 0.1	9.0 ± 0.3	14.9 ± 1.1
Synthetic pretraining (P)	97.6 ± 0.2	9.7 ± 0.2	14.3 ± 3.6
Drop is clean accuracy minus perturbed accuracy, in points, averaged over a family's levels. Lower is better. Mean ± std over 5 training seeds.

Accuracy by severity
Rotation
Real only (A0)
Real + augmented (A1)
Real + synthetic (B)
Full mix (A2)
Synthetic pretraining (P)
70
80
90
15°
30°
45°
90°
135°
180°
severity
accuracy %
Gaussian noise
Real only (A0)
Real + augmented (A1)
Real + synthetic (B)
Full mix (A2)
Synthetic pretraining (P)
40
60
80
100
clean
σ 0.02
σ 0.05
σ 0.1
σ 0.2
severity
accuracy %
Salt-and-pepper noise
Real only (A0)
Real + augmented (A1)
Real + synthetic (B)
Full mix (A2)
Synthetic pretraining (P)
25
50
75
100
clean
1%
5%
severity
accuracy %
Gaussian blur
Real only (A0)
Real + augmented (A1)
Real + synthetic (B)
Full mix (A2)
Synthetic pretraining (P)
40
60
80
100
clean
radius 1
severity
accuracy %
JPEG compression
Real only (A0)
Real + augmented (A1)
Real + synthetic (B)
Full mix (A2)
Synthetic pretraining (P)
85
90
95
clean
quality 90
quality 50
quality 20
severity
accuracy %
Brightness shift
Real only (A0)
Real + augmented (A1)
Real + synthetic (B)
Full mix (A2)
Synthetic pretraining (P)
40
60
80
100
clean
-0.2
+0.2
+0.4
severity
accuracy %
Contrast shift
Real only (A0)
Real + augmented (A1)
Real + synthetic (B)
Full mix (A2)
Synthetic pretraining (P)
40
60
80
100
clean
× 0.75
severity
accuracy %
Occlusion patch
Real only (A0)
Real + augmented (A1)
Real + synthetic (B)
Full mix (A2)
Synthetic pretraining (P)
92.5
95
97.5
clean
8 px
16 px
24 px
severity
accuracy %
Drop by perturbation family
Arm	Gaussian noise	Salt-and-pepper noise	Gaussian blur	JPEG compression	Brightness shift	Contrast shift	Occlusion patch
Real only (A0)	16.1 ± 4.3	52.6 ± 3.9	62.3 ± 8.2	4.7 ± 0.9	34.0 ± 4.4	53.7 ± 5.5	1.9 ± 0.7
Real + augmented (A1)	5.0 ± 0.2	37.5 ± 2.7	42.7 ± 6.1	1.1 ± 0.7	27.0 ± 6.3	41.7 ± 18.6	2.5 ± 0.6
Real + synthetic (B)	4.7 ± 0.7	25.2 ± 5.1	44.4 ± 6.0	1.1 ± 0.4	33.0 ± 7.5	53.2 ± 25.0	2.8 ± 1.5
Full mix (A2)	4.5 ± 1.9	28.4 ± 4.0	42.4 ± 9.2	1.1 ± 0.4	27.6 ± 4.3	44.6 ± 9.1	1.7 ± 0.2
Synthetic pretraining (P)	5.1 ± 1.6	23.4 ± 1.7	41.6 ± 6.3	0.9 ± 0.6	26.0 ± 8.5	46.7 ± 26.7	2.2 ± 0.8
Per class under rotation

rot45
Real only (A0)
Real + augmented (A1)
Real + synthetic (B)
Full mix (A2)
Synthetic pretraining (P)
0
20
40
60
80
100
A0
A1
B
A2
P
circle
99.4
95.8
96.3
96.5
95.5
ellipse
36.3
83.3
85.9
83.6
85.0
triangle
87.6
91.9
89.5
89.8
90.8
square
60.6
54.1
65.5
66.2
65.7
rectangle
20.7
45.3
49.3
50.4
49.6
pentagon
91.3
99.9
99.6
99.7
99.9
hexagon
85.6
100.0
100.0
99.9
100.0
octagon
83.3
99.1
99.3
98.7
98.9
star
100.0
100.0
100.0
100.0
100.0
diamond
0.9
0.0
10.9
19.3
0.3
Dots with nearly the same score are spread up and down so each one shows. Only left and right position carries the score.

A circle looks the same at any angle and a square repeats every 90°, so those classes are not a fair test of rotation. Read the classes that have a direction, like triangle, pentagon and star.

A0
A1
B
A2
P
circle
ellipse
triangle
square
rectangle
pentagon
hexagon
octagon
star
diamond
circle
ellipse
triangle
square
rectangle
pentagon
hexagon
octagon
star
diamond
2894
90
1
9
6
173
1254
63
10
4
88
4039
116
2
251
58
1985
2
4
951
79
83
158
179
1512
1
988
2
1
1496
1
1
1499
19
1481
1500
45
87
173
281
617
8
289
predicted
true class
Every level
Show every level as a table
</pasted_content id="588d">

] it was due to us not know wether we should do weighted voting , or just striaght equal weight , or weight each class and givve each model a weight per class , also the robustness checkk was to confimr which class failied === also the main goal was to find out why is it that the augmentation and the syhtnethic generation toogles were making performance worst , neon suggested to hyper parameter tune the synthethic data and the augmentation  and train hundreds of model to see which toggle switch ended up confusing the model , the question was why is it that the audemtnation performed worst even thouggh every avaialable resource stated that augmenation supposedly increased , our suspeiction was that the model was missconfigured

## Response

#### What your account covers

Your account gives real attribution for 9 rows. I filled those rows and marked each one `recollection`. Rows your account does not cover stay blank.

I filled these in [results/llm_comparison/attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv):

| Row | What it is | proposed_by | caught_by |
|---|---|---|---|
| F04 | B vs A1 failed: augmentation and synthetic data made results worse | | test |
| F06, C04, C08, C11, C12 | Per-arm search over the augmentation, synthetic-generator and training settings (166 trials, hundreds of models) | gemini_neo | team (you suspected misconfiguration) |
| C17 | Robustness check added, to find which classes fail | gemini_neo | team |
| C28 | Robustness check moved into Stage 5, on the sealed holdout | gemini_neo | |
| C40 | Equal vs. weighted vs. per-class weighted vote | | team (your open question) |

#### Open question

Did Gemini Neo also suggest or run the vote comparison (C40, and the related failure F30)? Your message ties the voting question to the robustness page, but it does not say who proposed the comparison. I left `proposed_by` blank until you confirm.

#### Why the robustness check matters

Your main goal was to find out why the augmentation and synthetic generation toggles made performance worse. Your suspicion was that the model was misconfigured. Gemini Neo suggested tuning the synthetic data and the augmentation for each arm and training hundreds of models, to see which toggle confused the model.

This gives a strong story for the 30% section, and it fits slides 3 and 5:

1. **Your judgment:** every source said augmentation should help, but it made results worse (F04). You did not accept that, and suspected the setup instead.
2. **The LLM's suggestion:** Gemini Neo proposed tuning every arm separately and training hundreds of models to find the setting that confused the model.
3. **Checked by experiment:** the search found real defects:
   - Rotation up to 180 degrees erased the difference between square and diamond (F07).
   - Augmented shapes were about 6 px too small (F08).
   - Thin strokes broke apart after warping (F09).
   - Synthetic strokes were too thin (F10).
4. **Result:** after the fixes, the robustness check that Gemini proposed gave iteration 3's passing result: +9.20 macro-F1 points on damaged images, 95% CI [8.89, 9.53]. The per-class table also shows where every model still fails: diamonds and rectangles rotated 45 degrees.

##### How the rows were chosen
Only rows where your account names a specific model or a specific step were filled. A row needs a claim about who proposed it and who caught it. Rows that your account does not cover were left blank rather than guessed, which is why only 9 rows are filled. Each filled row is marked `recollection`, because the account is a memory, not an exported chat.

##### What was checked
- The claims in the table were matched to the failure and change IDs (F04, F06, C04, C08, C11, C12, C17, C28, C40) in the worksheet.
- The open question about C40 and F30 is unresolved. Whether Gemini Neo suggested the vote comparison is not stated, so `proposed_by` stays blank.

##### Why the sequence matters for the report
The story runs from a human judgment (the team suspected misconfiguration) to an LLM suggestion (the per-arm search) to experimental checks that found specific defects, and then to a result. Each step has its own evidence, which is what the 30% per-stage section asks for. The +9.20 figure is taken from the record as written, and its confidence interval is reported as given.

##### Next steps
- Confirm who proposed the vote comparison, then fill `proposed_by` for C40 and F30.
- Export the Gemini chat if one exists, so the `recollection` rows can be upgraded to `chat`.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
