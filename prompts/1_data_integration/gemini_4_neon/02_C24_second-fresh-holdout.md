
# 1_data_integration - C24: Second fresh holdout

- LLM: Gemini 4 Neon (proposed)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09
- Source: from repo, not a saved chat. The worksheet lists the attribution source as "recollection". No Gemini reply is reproduced. A Google Drive search for the original Gemini transcript returned no results (the file search encountered an error for this source), so the transcript could not be recovered from Drive either.
- Entry: C24 (`change`, `1_data_integration`), commit ff1f269 (2026-11-09)

## Prompt

> The test split and the first fresh holdout have both been read. Should we build a second sealed holdout for iteration 3, and how do we make sure it is never read before the pre-registered test?

## Response

**No Gemini 4 Neon reply is available.** The repo records the change that followed:

- A second sealed holdout, `fresh_holdout_2`, was built by `src/stage1_freeze/fresh_holdout_2.py` with 4,500 images (`docs/crisp_dm/iteration_3/preregistration.md`).
- It is registered as `FRESH2_SPLIT` in `SEALED_SPLITS` in `src/common/splits.py`, so only Stage 5 can open it.

## Why a second holdout is needed (augmented)

- **The test split was read in iteration 1** (C02's reason for building the first fresh holdout).
- **The first fresh holdout was read in iteration 2** (the reason for building the second).
- **Why this matters:** once a split has been read, it can no longer give an unbiased verdict. Any choice made after reading it is contaminated.
- **Why a second holdout is needed for iteration 3:** iteration 3 needs an unbiased evaluation, and both the original test split and the first fresh holdout are now contaminated.
- **Why 4,500 images:** same size as the first fresh holdout (C02), for comparability.

## How the second holdout is built (augmented)

- **`fresh_holdout_2.py`** builds the holdout with `SECOND_PER_GROUP = 300` images per non-`quickdraw` `(source, label)` group, `SEED = 20261109`.
- **Excludes `quickdraw`** (same as C02) and **any near-duplicates of the catalog or first holdout** (`phash_hamming_max = 2`).
- **Why exclude near-duplicates:** this ensures the holdout is truly disjoint from the catalog and prior holdouts, which is critical for an unbiased evaluation.
- **Why 300 per group:** same stratified cap as C02, preventing any one `(source, label)` combination from dominating.
- **Why `SEED = 20261109`:** makes the holdout reproducible.
- **Why 4,500 total:** 3 sources x 10 classes x ~150 per group = ~4,500 (some groups don't have all 3 sources).

## How the holdout is sealed (augmented)

- **`FRESH2_SPLIT = "fresh_holdout_2"`** added to `SEALED_SPLITS` in `src/common/splits.py`.
- **This means reads outside Stage 5 are refused and logged**, the same guard as the test split and the first fresh holdout.
- **Why this matters:** it prevents accidental reads of the holdout, which would contaminate it.
- **Why the guard is enforced in code:** it's not just a convention; any attempt to read the holdout from outside Stage 5 will fail and be logged.

## How the holdout is pre-registered (augmented)

- **`docs/crisp_dm/iteration_3/preregistration.md`** states the holdout's size (4,500 images).
- **Why pre-registration matters:** it prevents post-hoc rationalisation. The holdout's purpose and size were written down before it was used.
- **Why this is good practice:** it's the same pattern as C02's pre-registration.

## Validation

- `docs/crisp_dm/iteration_3/preregistration.md` states the holdout's size.
- `tests/contracts/test_load_split_guard.py` covers the sealed-split guard (10 test functions).
- **Gemini transcript not recoverable:** a Google Drive search for the original Gemini C24 chat transcript returned no results (the file search encountered an error for this source), so the transcript could not be recovered from Drive either. The response section remains a repo-record change, which is correct for an unrecoverable transcript.

## Our decision

Build the second sealed holdout before iteration 3 tuning, with build-time non-overlap and runtime read sealing, as recorded in `iteration_log.json` and the worksheet.

## Measured effect

Holdout size: 4,500 sealed images. No macro-F1 result is recorded for this entry.

## Deeper detail: why this matters

### This is the second level of the holdout hierarchy

| Holdout | Built in | Read in | Status |
|---|---|---|---|
| Test split | Phase 1 | Iteration 1 | Contaminated |
| First fresh holdout (C02) | Iteration 2 | Iteration 2 | Contaminated |
| Second fresh holdout (C24) | Iteration 3 | Never (until pre-registered test) | Clean |

- **Why this hierarchy matters:** each iteration needs an unbiased evaluation, and each read contaminates the previous holdout.
- **Why the second holdout is "clean":** it hasn't been read yet, so it can give an unbiased verdict for iteration 3.
- **Why this is good experimental hygiene:** it ensures each iteration has a valid evaluation.

### The non-overlap constraint is critical

- **Excludes `quickdraw`:** same as C02, since Quick, Draw! drawings were already in the catalog.
- **Excludes near-duplicates (`phash_hamming_max = 2`):** ensures the holdout is truly disjoint from the catalog and prior holdouts.
- **Why this matters:** if the holdout contained near-duplicates of the catalog, it wouldn't be a valid "unseen" evaluation set.
- **Why this is the same threshold as the global grouping (I03):** ensures consistency across the pipeline.

### The sealed-split guard is the same pattern as C02

- **`SEALED_SPLITS`** now has three entries: `test`, `fresh_holdout`, `fresh_holdout_2`.
- **Why this matters:** it's a scalable pattern. As more holdouts are added, they're all protected by the same guard.
- **Why the guard is enforced in code:** it's not just a convention; any attempt to read a sealed split from outside Stage 5 will fail and be logged.

### Cross-reference to C02, I03, I04, I05

- **C02** is the first fresh holdout, which C24 extends.
- **I03** is the global grouping, which ensures the holdout is disjoint from the catalog (via `phash_hamming_max = 2`).
- **I04** is the fail-closed manifest freeze, which is the same pattern as the sealed-split guard.
- **I05** is the FD check, which validates the schema invariants the holdout must satisfy.
- **Why this matters:** C24 is part of a consistent pattern of holdout management, sealing, and validation.

## Notes on the log

- **Gemini transcript is genuinely lost:** like the other Gemini entries, this one has no transcript anywhere (not in the repo, not in Drive). The response section correctly stays a repo-record change rather than fabricating a Gemini reply.
- **The worksheet says "recollection" not "chat":** this is more honest than C02 (which said "chat"), since it acknowledges the source is memory rather than a transcript.
- **This is a `change` entry, not a `failure`:** C24 is categorised as a change (a fix applied), not a failure (a problem found). This is correct, since the second holdout is a proactive measure.
- **The 4,500-image size is consistent with C02:** this makes the two holdouts comparable.
- **The non-overlap constraint is critical:** it ensures the holdout is truly disjoint from the catalog and prior holdouts.
- **Cross-reference to C02, I03, I04, I05:** C24 is part of a consistent pattern of holdout management, sealing, and validation.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.