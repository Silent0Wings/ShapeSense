# NOTICE: source shortcut detected (Decision 12, stage_1.md R14)

A source classifier on standardized pixels reached pooled accuracy 0.917 against a majority-source rate of 0.467 (gain 45.0 points > trigger 10).

Consequences for Stages 4-6 (now REQUIRED, not optional):
- Stage 5: per-source accuracy tables for every arm.
- Stage 4/5: leave-one-source-out runs for A1 and B without the Hand-Drawn source (`github_handdrawn`), tested on Hand-Drawn only.
- Stage 6: pentagon and ellipse results keep their single-source asterisk.

Classes that come from one source only: ellipse, pentagon, diamond. A leave-one-source-out run that holds out such a source has no real images of that class, so it must train and score without it (P-61).

Details: artifacts/stage1/source_classifier.json
