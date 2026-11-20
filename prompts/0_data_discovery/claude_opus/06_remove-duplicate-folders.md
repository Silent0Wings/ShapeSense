

> **Reconstructed.** This file is not the original chat.
>
> **Evidence file** for this entry, quoting the saved LLM output verbatim: [09_evidence_handle-new-datasets-and-duplicates.md](09_evidence_handle-new-datasets-and-duplicates.md)

# 0_data_discovery - S06 - Removed duplicate downloads on 2026-10-19

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-10-19 (deletion date, from the log entry)
- Source: Reconstructed exchange grounded in docs/source.md, docs/data_sets.md, configs/taxonomy.yaml and inferred_prompts.md. The original Phase 1 chat transcript was not saved. The PowerShell `Get-FileHash` documentation was re-checked on 2026-11-20.

## Prompt
> Several folders in data_set/ look like copies of each other. How do we prove two folders are identical before deleting one?

## Response (augmented)

Don't rely on folder names, file counts or total size. Two folders can match on all three and still differ. Compare the **content of every file** with a hash manifest, and delete only when the manifests match exactly.

### Verification protocol

1. **Build a manifest per folder.** For every file, record its path relative to the folder root, its byte size and its **MD5** hash. Sort by relative path. The PowerShell `Get-FileHash` cmdlet supports MD5 as an algorithm, and its docs confirm that a hash value uniquely corresponds to file content, so identical hashes mean identical content. [learn.microsoft](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/get-filehash)
2. **Compare counts and bytes first.** If the file count or the total byte count differs, stop: the folders aren't duplicates. This check is cheap and catches truncated or partial copies.
3. **Diff the manifests.** Every `(relative path, MD5)` pair must appear on both sides. Any file missing on one side or with a different hash means "not a duplicate". For renamed copies (for example Windows `(2)` suffixes), match by MD5 rather than by name. The `Get-FileHash` docs confirm that file names and extensions can change without altering the hash, and that changing even one character in the contents changes the hash. [learn.microsoft](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/get-filehash)
4. **Zips:** don't hash the zip file against a folder. Hash **each entry** inside the archive and compare entry-for-entry with the extracted folder. This is because a zip file's own hash will differ from any single file inside it, so you need to unpack and hash each entry individually.
5. **Dry run.** List exactly what would be deleted and which kept copy each one matches. Review it, then delete.
6. **Record it.** Write the removed path, the kept path, the file count and the date in the source map, so the deletion can be audited later.

### Why MD5 is fine here

- MD5 is no longer considered secure against attack, but the goal here is not security. It is detecting accidental copies. The `Get-FileHash` docs explicitly note that MD5 and SHA1 are no longer secure against attack but are still fine for "simple change validation". [learn.microsoft](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/get-filehash)
- For this use case (comparing two local folders you control), MD5 is fast and sufficient. If you were verifying a download from an untrusted source, you'd want SHA256 instead.
- The `Get-FileHash` cmdlet defaults to SHA256, so you'd need to pass `-Algorithm MD5` explicitly if you use PowerShell. [learn.microsoft](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/get-filehash)

### Applying it to your candidates

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
- The `Get-FileHash` cmdlet is the right tool for this on Windows, since it's built into PowerShell and supports MD5, SHA1, SHA256, SHA384, and SHA512. [learn.microsoft](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/get-filehash)

### Recommendation

Run the manifest diff for all four candidates, delete only those that match exactly, and log each removal with its file count and date.

## Validation
- MD5 of every file compared with the kept copy, per docs/source.md and inferred_prompts.md S06.
- Re-checked against the PowerShell `Get-FileHash` documentation: MD5 is a supported algorithm, identical hashes mean identical content, and MD5 is fine for non-security use cases like duplicate detection. [learn.microsoft](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/get-filehash)
- Not re-checked in this pass: the actual MD5 manifests for the four candidate pairs, the exact file counts (30,000 / 4,000 / nested / 5 zips), the zip entry-level hashes.

## Our decision
Removed four duplicate folders (archive/, test/, a nested QuickDraw copy, raw zips). Each was verified identical to the kept copy by the MD5 of every file, then deleted.

## Measured effect
Duplicate folders deleted on 2026-10-19. No macro F1 change applies.

## Notes on the log

- **MD5 vs SHA256:** the log correctly uses MD5 for this task. The `Get-FileHash` docs confirm MD5 is fine for "simple change validation" but not for security-critical use cases. Since you're comparing two local folders you control, MD5 is the right choice for speed. [learn.microsoft](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/get-filehash)
- **Zip handling is the tricky part:** the log correctly notes that you can't hash a zip file against a folder. You need to unpack and hash each entry. This is a detail that's easy to get wrong and worth calling out.
- **The `(2)` suffix case:** the log correctly identifies this as a Windows re-extraction artefact and notes that you should match by MD5, not by name. This is a practical detail that saves a lot of confusion.
- **The Zip/ folder caveat:** the log says to delete all 5 zips, but doesn't consider whether you might want to keep the zips for the 4 kept sources in case you need to re-download. This is a judgment call worth revisiting if disk space is tight.
- **Deletion date is recorded:** unlike the other S-entries, this one has an actual date (2026-10-19), which is good practice for an auditable deletion log.
- **No macro F1 change:** correct, since this is a data hygiene step, not a modelling or evaluation step.