

> **Reconstructed.** This file is not the original chat.
>
> **Evidence file** for this entry, quoting the saved LLM output verbatim: [09_evidence_handle-new-datasets-and-duplicates.md](../claude_opus/09_evidence_handle-new-datasets-and-duplicates.md)

# 0_data_discovery - S06 - Removed duplicate downloads on 2026-10-19

- LLM: Gemini 4 Neon
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-10-19 (deletion date, from the log entry)
- Source: from repo, not a saved chat. Gemini 4 Neon has no transcripts in this repo. A Google Drive search for the original Gemini transcript returned no results (the file search encountered an error for this source), so the transcript could not be recovered from Drive either.

## Prompt
> Several folders in data_set/ look like copies of each other. How do we prove two folders are identical before deleting one?

## Response

No reply exists in this repo. Gemini 4 Neon responses are not reproduced for this item.

**Stand-in answer** *(written 2026-11-20 by Claude Opus 5.5 from the repo's records. It is not Gemini 4 Neon's reply, which is lost, so this file does not count as a Gemini answer in the two-LLM comparison.)*

Matching names and file counts don't prove anything. Compare content:

1. List every file in both folders with its relative path and size. Stop if the lists differ.
2. Hash every file (MD5 is enough here: you're checking for accidental copies, not defending against an attacker) and compare the two maps from path to hash. They must match exactly.
3. For an archive, compare each entry inside the zip with the extracted file of the same path.
4. Only then delete the copy, and write down what was deleted, its file count and which copy was kept.

Applied here, this showed four duplicates: `archive/` = `kaggle_dinesh/` (30,000 files), `test/` = `kaggle_reevald/dataset/test/` (4,000 files), a nested Quick, Draw! copy, and the raw zips. All four were verified by the MD5 of every file and deleted on 2026-10-19 (`docs/source.md`).

## What we can reconstruct from the decision

Even though the Gemini response itself is lost, the decision it produced is recorded in docs/source.md and can be reconstructed in detail. Four duplicate folders were identified and removed after MD5 verification:

### Verification protocol

1. **Build a manifest per folder.** For every file, record its path relative to the folder root, its byte size and its **MD5** hash. Sort by relative path.
2. **Compare counts and bytes first.** If the file count or the total byte count differs, stop: the folders aren't duplicates. This check is cheap and catches truncated or partial copies.
3. **Diff the manifests.** Every `(relative path, MD5)` pair must appear on both sides. Any file missing on one side or with a different hash means "not a duplicate". For renamed copies (for example Windows `(2)` suffixes), match by MD5 rather than by name.
4. **Zips:** don't hash the zip file against a folder. Hash **each entry** inside the archive and compare entry-for-entry with the extracted folder.
5. **Dry run.** List exactly what would be deleted and which kept copy each one matches. Review it, then delete.
6. **Record it.** Write the removed path, the kept path, the file count and the date in the source map, so the deletion can be audited later.

### Why MD5 is fine here

- MD5 is no longer considered secure against attack, but the goal here is not security. It is detecting accidental copies.
- For this use case (comparing two local folders you control), MD5 is fast and sufficient. If you were verifying a download from an untrusted source, you'd want SHA256 instead.
- The PowerShell `Get-FileHash` cmdlet defaults to SHA256, so you'd need to pass `-Algorithm MD5` explicitly if you use PowerShell.

### The four candidates

| Candidate to remove | Kept copy | Check | Recommendation |
|---|---|---|---|
| `data_set/archive/` | `data_set/kaggle_dinesh/` | MD5 of all 30,000 files | Delete if the manifests match |
| `data_set/test/` | `data_set/kaggle_reevald/dataset/test/` | MD5 of all 4,000 files | Delete if the manifests match |
| `data_set/quickdraw-dataset-master/quickdraw-dataset-master/` | the outer QuickDraw copy | Match the nested `(2)` files by MD5 | Delete if every `(2)` file matches |
| `data_set/Zip/` (5 raw zips) | the extracted folders | Entry-for-entry MD5 against each extracted folder | Delete if every entry matches |

### Per-candidate detail

**`data_set/archive/` vs `data_set/kaggle_dinesh/`**
- 30,000 files each (10,000 circle, 10,000 square, 10,000 triangle), 200x200 RGB PNG.
- The `archive/` folder is likely an earlier download of the same Kaggle dinesh dataset that was later re-downloaded into `kaggle_dinesh/`.
- Since the Kaggle dinesh dataset was ultimately excluded from the unified dataset (S02), both copies are now dead weight. Deleting the duplicate is safe either way.

**`data_set/test/` vs `data_set/kaggle_reevald/dataset/test/`**
- 4,000 files each (8 classes x 500 test images), 224x224 RGB JPG.
- The `test/` folder is likely a partial extraction of the reevald dataset that was later fully extracted into `kaggle_reevald/dataset/`.
- Since reevald is one of your four kept sources, you need exactly one copy. Deleting the duplicate is correct.

**`data_set/quickdraw-dataset-master/quickdraw-dataset-master/`**
- This is a nested duplicate, likely from unzipping a GitHub repo zip that already contained a folder with the same name.
- The `(2)` suffix on files is a Windows artefact from re-extracting into an existing folder.
- Since Quick, Draw! is one of your four kept sources, you need exactly one copy. Deleting the nested duplicate is correct.

**`data_set/Zip/` (5 raw zips)**
- These are the original downloaded zip archives for the five datasets (four kept + one rejected).
- Since the extracted folders already exist and are verified, the zips are redundant.
- **Caveat:** if you ever need to re-download a dataset (for example, if the origin link changes or the extracted folder gets corrupted), having the original zip can save a re-download. Consider keeping the zips for the four kept sources and deleting only the zip for the rejected dinesh dataset, or keep all five if disk space is not a concern.

### Safety notes

- `data_set/` is git-ignored, so git can't undo a deletion. Make sure every kept dataset can still be re-downloaded from its origin link before you delete anything.
- Keep exactly one copy of each dataset, and point the build script only at that copy.

### Recommendation

Run the manifest diff for all four candidates, delete only those that match exactly, and log each removal with its file count and date.

## Validation
- MD5 of every file compared with the kept copy, per docs/source.md and inferred_prompts.md S06.
- **Gemini transcript not recoverable:** a Google Drive search for the original Gemini S06 chat transcript returned no results (the file search encountered an error for this source), so the transcript could not be recovered from Drive either. The response section remains empty, which is correct for an unrecoverable transcript.
- Not re-checked in this pass: the actual MD5 manifests for the four candidate pairs, the exact file counts (30,000 / 4,000 / nested / 5 zips), the zip entry-level hashes.

## Our decision
Removed four duplicate folders (archive/, test/, a nested QuickDraw copy, raw zips). Each was verified identical to the kept copy by the MD5 of every file, then deleted.

## Measured effect
Duplicate folders deleted on 2026-10-19. No macro F1 change applies.

## Notes on the log

- **Gemini transcript is genuinely lost:** like S01 through S05, this one has no transcript anywhere (not in the repo, not in Drive). The response section correctly stays empty rather than fabricating a reply.
- **The decision is still fully reconstructable:** even without the Gemini response, the verification protocol, the four candidates, and the per-candidate detail are all reconstructable from docs/source.md and the earlier expanded S06 entry. This means the decision itself is auditable even if the reasoning that produced it is not.
- **Deletion date is recorded:** unlike the other S-entries, this one has an actual date (2026-10-19), which is good practice for an auditable deletion log.
- **The Zip/ folder caveat:** the log says to delete all 5 zips, but doesn't consider whether you might want to keep the zips for the 4 kept sources in case you need to re-download. This is a judgment call worth revisiting if disk space is tight.
- **Cross-reference to S02:** the `data_set/archive/` folder was a duplicate of `kaggle_dinesh/`, which was itself excluded in S02. This means the 30,000 files were downloaded twice before being excluded, which is a minor inefficiency in the data discovery phase.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.