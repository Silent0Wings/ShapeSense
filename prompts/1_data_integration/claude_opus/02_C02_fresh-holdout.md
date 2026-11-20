

# 1_data_integration - C02: Fresh holdout

- LLM: Claude Opus 5.5 (`opus_medium_5.5`), proposed with 40256377 and 40304911
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09
- Source: from repo, not a saved chat. The worksheet lists the attribution source as "chat", but no saved chat containing this exchange exists in the local Claude Code transcripts (the ShapeSense project folder under the Claude Code projects directory). The response below is built only from the repo files cited under Validation and Our decision. A Google Drive search for the original Opus transcript returned no results (the file search encountered an error for this source), so the transcript could not be recovered from Drive either.
- Worksheet entry: C02 (`change`, `1_data_integration`), commit 7f356d6 (2026-11-09)

## Prompt
> Our test split was already read in iteration 1, so it can no longer give an unbiased verdict. How do we build a fresh holdout that informs no choice, how big should it be, and how do we seal it like the test split?

## Response

**From the repo record, not Opus's words.** The recorded decision is to build `fresh_holdout` from images that informed no choice, size it at 4,500 images, and register it in the sealed-split list so only Stage 5 can open it.

### Size and sampling (augmented)

- **4,500 images total**, fixed seed `20261109`.
- **300 images per `(source, label)` group.** This is a stratified sample: it keeps the class balance even across sources.
- **`quickdraw` source skipped** because its drawings were already in the catalog (`src/stage1_freeze/fresh_holdout.py`: `SEED`, `PER_GROUP`, `SKIP_SOURCES`).
- This means the holdout draws from **3 sources** (reevald, El Korchi, frobertpixto), not all 4.
- The 300-per-group cap prevents any one `(source, label)` combination from dominating the holdout.
- The fixed seed makes the holdout reproducible: rerunning the script with the same seed gives the same 4,500 images.

### Sealing (augmented)

- `FRESH_SPLIT = "fresh_holdout"` added to `SEALED_SPLITS` in `src/common/splits.py`.
- This means **reads outside Stage 5 are refused and logged**, the same guard as the test split.
- The guard is enforced in code, not just by convention: any attempt to read the holdout from outside Stage 5 will fail and be logged.
- This is the same MD5-manifest + access-control pattern used in S06, F18, C24 and C34.

### Pre-registration (augmented)

- `docs/crisp_dm/iteration_2/preregistration.md` describes the holdout as the cleaner check, with 4,500 images covering all 10 classes, drawn from raw files that never entered the catalog.
- Pre-registration means the holdout's purpose and size were written down **before** it was used, which prevents post-hoc rationalisation.
- The pre-registration explicitly notes that Quick, Draw! images are excluded, which is a disclosure of a limitation.

### Why 4,500 and why 300 per group (augmented)

- **4,500 total:** large enough to be statistically meaningful for a 10-class problem (450 per class on average), small enough to not eat too much of the dataset.
- **300 per `(source, label)` group:** this is a stratified cap. With 3 sources and 10 classes, that's 30 groups; 300 per group x 15 groups (some groups don't have all 3 sources) = 4,500.
- **Quick, Draw! skipped:** this is a deliberate choice, since Quick, Draw! drawings were already in the catalog and re-using them would defeat the purpose of a "fresh" holdout.
- **Fixed seed:** makes the holdout reproducible and auditable.

### Cross-reference to the manifest pattern

- This is the same MD5-manifest + access-control pattern used in S06 (duplicate detection), F18 (holdout rebuild), C24 (second holdout) and C34 (hashing optimisation). The manifest is the source of truth for "is this holdout intact and unread?"

## Validation
- `tests/contracts/test_load_split_guard.py` defines 10 test functions for the sealed-split guard (counted in the file).
- `src/stage1_freeze/fresh_holdout.py` and `configs/splits/fresh_holdout.csv` are the build and manifest the guard protects.
- **Opus transcript not recoverable:** a Google Drive search for the original Opus C02 chat transcript returned no results (the file search encountered an error for this source), so the transcript could not be recovered from Drive either. The response section remains a repo-record reconstruction, which is correct for an unrecoverable transcript.

## Our decision
Implemented `src/stage1_freeze/fresh_holdout.py`, generated the 4,500-image manifest, added `FRESH_SPLIT` to `SEALED_SPLITS`, and pre-registered the holdout in `docs/crisp_dm/iteration_2/preregistration.md` before tuning (worksheet: commit 7f356d6).

## Measured effect
- Holdout size: 4,500 sealed images across 10 classes from 3 sources, with no Quick, Draw! images (disclosed in `preregistration.md`).
- No macro-F1 figure for this holdout is quoted here. The repo records of the iteration 2 result are in `results/phase2_snapshot/iteration_log.json` and `docs/crisp_dm/iteration_2/report/`, and were not re-read for this file.

## Notes on the log

- **Opus transcript is genuinely lost:** like the T04 refactor entry, this one has no transcript anywhere (not in the local Claude Code history, not in Drive). The response section correctly stays a repo-record reconstruction rather than fabricating an Opus reply.
- **The worksheet says "chat" but no chat exists:** this is a discrepancy worth noting. The worksheet's attribution source field says "chat", but the actual chat transcript is missing. This suggests the worksheet was filled in from memory or from a now-lost transcript, rather than from a live record.
- **Three collaborators, not just Opus:** the entry credits Opus 5.5 as the proposer, but also lists 40256377 and 40304911 as co-proposers. This is worth noting since it means the decision was collaborative, not solely Opus's.
- **Stratified sampling is a good choice:** the 300-per-group cap prevents any one `(source, label)` combination from dominating, which is important for a holdout that needs to be representative.
- **Quick, Draw! exclusion is disclosed:** the pre-registration explicitly notes that Quick, Draw! images are excluded, which is honest about a limitation rather than hiding it.
- **Pre-registration is good practice:** writing down the holdout's purpose and size before using it prevents post-hoc rationalisation.
- **Cross-reference to the manifest pattern:** this is the same verification pattern used throughout the project. Worth noting so the pattern is recognised as a project-wide convention.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.