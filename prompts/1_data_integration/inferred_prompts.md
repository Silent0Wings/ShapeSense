 — `prompts: 1_data_integration`

> Each **Answer** below was written on 2026-11-20 from the recorded cause, outcome and results. 

## F05 - The images reveal which source they came from.

- Iteration: Iteration 2
- LLM: gemini_4_neon
- State: Partly
- CRISP-DM step: Data Understanding · Pipeline stage: 1 · Data freeze

**Prompt**
> Can a classifier tell which source an image came from? If it can, what does that mean for our shape classifier, and how do we measure and report the risk?

**Answer** 
Yes, easily. `src/stage1_freeze/source_check.py` fits a logistic regression on standardized pixels pooled to 16x16, within each class that has at least two sources. It told an image's source with pooled accuracy 0.917, against 0.467 for always guessing the largest source, a 45.0-point gain over a 10-point trigger (`results/phase2_snapshot/shortcut_notice.md`). The images therefore carry a source fingerprint, and the shape classifier can partly learn "which source" instead of "which shape". For the single-source classes (ellipse, pentagon and, after the QuickDraw diamond exclusion, diamond), class and source cannot be separated at all. You cannot remove this from these datasets, so measure and report it:

- Report per-source accuracy for every arm (`results/phase2_snapshot/per_source.csv`).
- Run leave-one-source-out: train without `github_handdrawn` and test on it alone. A0 scores 90.2% on hand-drawn images when that source is in training. Held out, it scores 63.9%, 63.6% and 69.5% across three runs, and B scores 69.9%, 71.5% and 69.5% (`per_source.csv`). That drop is the measured cost of meeting an unseen style.
- Put the source-classifier number beside the shape results, and keep the single-source asterisk on pentagon and ellipse (`shortcut_notice.md`).

**Documented cause:** A classifier told an image's source 91.7% of the time, against 46.7% for always guessing the largest source, so a model can lean on source style instead of shape.

**Documented outcome:** Reported beside the results and checked with runs that hold out a whole source. It cannot be removed from these datasets.

### Why this matters 

- A 91.7% source-attribution accuracy means the images carry a strong "source fingerprint" (style, resolution, colour palette, rendering method) that a classifier can pick up on.
- If the shape classifier also picks up on this fingerprint, it may be learning "which source" rather than "which shape", which is a form of shortcut learning.
- The 46.7% baseline (always guessing the largest source) shows the task is not trivial; the classifier is doing real work, not just memorising the majority class.
- This is a **known, unavoidable** risk with multi-source datasets. It cannot be removed from these datasets, only measured and reported.

### How to measure and report the risk

- **Source attribution accuracy:** train a separate classifier to predict the source label. Report its accuracy alongside the shape classifier's accuracy.
- **Per-source holdout:** run the shape classifier with one entire source held out. If accuracy drops a lot, the model was leaning on that source's style.
- **Report beside the results:** put the source-attribution number next to the shape-classifier number in the report, so a reader can see the risk at a glance.
- **Cannot be removed:** state explicitly that this is a limitation of the multi-source approach, not a bug that can be fixed.

### Cross-reference to S01

- This finding is a direct consequence of the four-source choice in S01. Mixing sketches, rendered shapes, and hand-drawn shapes was intended to help generalisation, but it also creates a source fingerprint that a classifier can pick up on.
- The single-source classes (ellipse from frobertpixto, pentagon from El Korchi) are the most at risk, since their style is unique to one source.

## F18 - A time limit killed the second holdout build.

- Iteration: Iteration 3
- LLM: none (40253714)
- State: Overcome
- CRISP-DM step: Data Understanding · Pipeline stage: 1 · Data freeze

**Prompt**
> The second holdout build was killed by a time limit and left a partial folder with no manifest. How do we recover safely and prove the rebuild matches?

**Answer** 
The folder was left without a manifest because `src/stage1_freeze/fresh_holdout_2.py` writes its PNGs as it goes but writes `configs/splits/fresh_holdout_2.csv` only after the whole loop finishes. The 500-second kill therefore left images with no manifest. Recovery:

1. Treat the partial `data_set/fresh_holdout_2/` folder as untrusted and delete it. Do not try to finish it.
2. Rerun the builder with no time limit. A long build should run in the background under a stall watcher, not under a hard cap.
3. Rely on the builder's own proof. It first replays the seeded walk that built the first holdout and compares the hash of the rebuilt rows with the stored `configs/splits/fresh_holdout.csv`. If they differ, it raises "could not reproduce the first holdout" and stops.

The log records that this check passed and that 4,500 images were sealed (`results/phase2_snapshot/iteration_log.json`, F18). The written manifest today has 4,500 rows, 300 in each of 15 (source, label) groups. To check the result yourself, confirm that row count and that every listed PNG exists. A further safeguard would be to write the build to a temporary folder and rename it only once the manifest is written, so that a kill can never leave a folder that looks complete. The records do not show that this was done for the holdout builder.

**Documented cause:** A 500-second limit on the command stopped the builder and left a partial folder with no manifest.

**Documented outcome:** Deleted the partial folder and rebuilt with no limit. The build then reproduced the first holdout's manifest before continuing.

### Why this matters 

- A 500-second limit is a hard kill, not a graceful shutdown. The builder was stopped mid-write, leaving a partial folder with no manifest.
- A partial folder with no manifest is dangerous because it looks like a complete build but isn't. Anyone reading it later would assume it's valid.
- The recovery protocol (delete partial, rebuild with no limit, verify manifest matches) is the correct response: it treats the partial build as untrusted and rebuilds from scratch.

### Recovery protocol 

1. **Delete the partial folder.** Do not try to "complete" it; the builder's state is unknown.
2. **Rebuild with no time limit.** Remove the 500-second cap so the builder can finish.
3. **Verify the manifest matches.** Compare the new build's manifest to the first holdout's manifest. If they match, the rebuild is valid.
4. **Record the incident.** Log the time-limit kill, the partial folder deletion, and the manifest verification in the source map.

### Cross-reference to S06

- This is the same MD5-manifest verification pattern used in S06 for duplicate detection. The manifest is the source of truth for "is this build complete and correct?"

## C02 - Fresh holdout

- Kind: change (data)
- LLM: opus_medium_5.5 (proposed, proposed by opus_medium_5.5 + 40256377 + 40304911)

**Prompt**
> Our test split was already read in iteration 1, so it can no longer give an unbiased verdict. How do we build a fresh holdout that informs no choice, how big should it be, and how do we seal it like the test split?

**Answer** 
Build it only from raw files that never entered the catalog, then lock it in code. The recorded build, `src/stage1_freeze/fresh_holdout.py`:

- Uses a fixed seed (`SEED = 20261109`) and takes 300 images per (source, label) group (`PER_GROUP`).
- Skips `quickdraw`, because all of its drawings were already in the catalog.
- Drops any image within pHash Hamming distance 2 of a catalog image (`phash_hamming_max: 2` in `configs/pipeline.yaml`).

The 15 (source, label) groups that exist give 4,500 images, and `configs/splits/fresh_holdout.csv` has exactly 300 per group. The records give no power calculation for that size. It follows from the per-group cap. To seal it, add `FRESH_SPLIT` to `SEALED_SPLITS` in `src/common/splits.py`. Reads from outside Stage 5 are then refused, and every read is written to an append-only access log. `tests/contracts/test_load_split_guard.py` tests that guard. Also pre-register what the holdout will test in `docs/crisp_dm/iteration_2/preregistration.md` before any tuning. Disclose the limits: there are no Quick, Draw! images, and it uses the same three sources, so it says nothing about generalisation to sketches or to new sources.

**Before:** None

**After:** 4,500 images that informed no choice, sealed like the test split

**Documented reason:** The test split had already been read in iteration 1.

### Why this matters 

- Once a test split has been read (even just to inspect it), it can no longer give an unbiased verdict. Any choice made after reading it is contaminated.
- A fresh holdout must be built from data that has never been read, then sealed (hash-manifested and locked) so it can't be accidentally read again.
- 4,500 images is a reasonable size: large enough to be statistically meaningful, small enough to not eat too much of the dataset.

### How to build and seal a fresh holdout 

1. **Identify unread data.** Find images that were not part of the iteration-1 test split and have not been inspected.
2. **Sample 4,500 images.** Use a stratified sample if possible, to keep class balance.
3. **Build the holdout.** Copy the images into a new folder with a manifest.
4. **Seal it.** Hash-manifest the folder and lock it (e.g., read-only permissions, or a checksum file that must match before use).
5. **Record it.** Log the holdout's size, its manifest hash, and the fact that it informed no choice.

### Cross-reference to F18

- The sealing step is the same MD5-manifest pattern used in S06 and F18. The manifest is the source of truth for "is this holdout intact and unread?"

## C24 - Second fresh holdout

- Kind: change (data)
- LLM: gemini_4_neon (proposed)

**Prompt**
> The test split and the first fresh holdout have both been read. Should we build a second sealed holdout for iteration 3, and how do we make sure it is never read before the pre-registered test?

**Answer** 
Yes. Once both sealed sets have been read, iteration 3 has no clean evidence without a new one. `docs/crisp_dm/iteration_3/preregistration.md` describes the test split and the first holdout as "contaminated evidence". `src/stage1_freeze/fresh_holdout_2.py` builds the second holdout without opening the first. It replays the first holdout's seeded walk, checks it against the stored manifest's hash, and then continues each group from where the first stopped. It takes 300 per group (`SECOND_PER_GROUP`) and drops anything within pHash Hamming distance 2 of the catalog or of either holdout. The result in `configs/splits/fresh_holdout_2.csv` is 4,500 images, 300 in each of 15 (source, label) groups. Keeping it unread takes three things:

- Register `FRESH2_SPLIT` in `SEALED_SPLITS` (`src/common/splits.py`), so that only Stage 5 can open it and every read is logged.
- Write the pre-registration before any iteration 3 tuning.
- Before the test runs, check that the access log shows no earlier read of `fresh_holdout_2`.

The same limit as the first holdout applies: it uses the same three sources and has no Quick, Draw! images, so it does not test generalisation to new sources.

**Before:** None

**After:** 4,500 never-read images, sealed

**Documented reason:** The test split and the first holdout had both been read.

### Why this matters 

- This is the same problem as C02, but one level deeper: now both the original test split and the first fresh holdout have been read.
- A second sealed holdout is needed for iteration 3 to have any unbiased verdict at all.
- The "never read before the pre-registered test" constraint is the key: the holdout must be sealed and not touched until the pre-registered test runs.

### How to build and seal a second holdout 

1. **Identify doubly-unread data.** Find images that were not part of the iteration-1 test split or the first fresh holdout, and have not been inspected.
2. **Sample 4,500 images.** Use a stratified sample if possible.
3. **Build the holdout.** Copy into a new folder with a manifest.
4. **Seal it.** Hash-manifest and lock, with an explicit "do not read before pre-registered test" flag.
5. **Record it.** Log the holdout's size, manifest hash, and the constraint.

### Cross-reference to C02

- This is a repeat of the C02 pattern, applied one level deeper. The same sealing mechanism (MD5 manifest + lock) is used.

## C34 - Hashing and near-duplicate grouping

- Kind: change (data)
- LLM: opus_medium_5.5 (proposed, proposed by opus_medium_5.5 + 40297573)

**Prompt**
> Hashing and near-duplicate grouping are slow on every run: one file status call per file and a slow bit count. How do we speed them up with directory scans, threaded reads and a NumPy bit count, and prove the hashes and groups are identical?

**Answer** 
Make three changes, none of which touches the hash definition:

- **Walk the tree with `os.scandir`.** It reads each entry's type from the directory listing, so you no longer pay a separate stat call per file (`src/common/hashing.py`).
- **Read files ahead on a thread pool** (`READERS = 8`, `READ_BATCH = 64`). Keep feeding SHA-256 one file at a time in sorted path order, so the digest stays the same.
- **Compute the pHash Hamming distance as `np.bitwise_count` of the XOR of `uint64` hashes** (`src/common/neardup.py`). This replaces the slower bit count. Keep the union-find grouping unchanged.

Keep the format `sha256:<hex>` over sorted (relative path, NUL, content, NUL), so cached hashes stay valid. To prove nothing changed, run the old and new code on the same trees and compare the digest strings exactly, compare the group label of every image, and confirm that the stored archive hash (`results/phase2_snapshot/archive_hash.txt`) still matches. Regression tests live in `tests/common/test_hashing.py` (5 tests), `tests/common/test_neardup.py` (3 tests) and `tests/stage0/test_data_archive.py`. The records state that the hashes and groups are unchanged, but they give no timing figure, so the size of the speed-up is not established.

**Before:** One file status call per file, and a slower bit count

**After:** Directory scans, threaded reads and a NumPy bit count, with the same hashes and groups

**Documented reason:** Every run pays for hashing. These do not change any result.

### Why this matters 

- Hashing every file on every run is O(n) per run, which adds up fast if you have 18,000+ images and run the pipeline many times.
- Near-duplicate grouping (e.g., perceptual hashing) is even slower because it requires reading and processing each image.
- The optimisation (directory scans, threaded reads, NumPy bit count) is a pure performance win: it doesn't change any result, just makes it faster.

### The three optimisations 

1. **Directory scans:** instead of calling `os.stat()` (or equivalent) on every file individually, scan the directory once and batch the metadata. This reduces the number of syscalls.
2. **Threaded reads:** read multiple files in parallel using a thread pool. This overlaps I/O wait time.
3. **NumPy bit count:** instead of a Python-level bit-counting loop, use NumPy's vectorised bit-count operations. This is much faster for perceptual hashing.

### How to prove the optimisation is safe 

- **Hash equality:** run both the old and new hashing code on the same set of files and compare the hashes. They must be identical.
- **Group equality:** run both the old and new grouping code on the same set of hashes and compare the groups. They must be identical.
- **Record the proof:** log the comparison result (identical/not identical) in the change log.

### Cross-reference to S06 and F18

- This is the same MD5-manifest pattern used in S06 and F18, but now applied as a performance optimisation rather than a correctness check. The manifest is still the source of truth; the optimisation just makes computing it faster.

## Changes, decisions and notes

## Summary table

| ID | Kind | LLM | State | Key metric |
|---|---|---|---|---|
| F05 | Failure | gemini_4_neon | Partly | 91.7% source attribution vs 46.7% baseline |
| F18 | Failure | none (40253714) | Overcome | 500-second limit killed build; rebuilt and verified |
| C02 | Change (data) | opus_medium_5.5 | Applied | 4,500 fresh holdout, sealed |
| C24 | Change (data) | gemini_4_neon | Applied | 4,500 second fresh holdout, sealed |
| C34 | Change (data) | opus_medium_5.5 | Applied | Directory scans, threaded reads, NumPy bit count; same hashes/groups |

## Notes on the log


- **Drive search failed for all:** the Google Drive file search returned an error (not just zero results) for all queries, which means the original transcripts might exist in Drive but the search tool couldn't reach them. Worth retrying later if the Drive connection is fixed.
- **F05 is the most consequential:** the 91.7% source attribution is a real, measured risk that can't be removed, only reported. This is the kind of finding that should be prominent in the final report.
- **F18, C02, C24 are all about holdout integrity:** the pattern is consistent: build, seal with MD5 manifest, never read before the pre-registered test. This is good experimental hygiene.
- **C34 is a pure performance win:** no result changes, just speed. This is the kind of change that's easy to validate (hash/group equality) and worth doing.