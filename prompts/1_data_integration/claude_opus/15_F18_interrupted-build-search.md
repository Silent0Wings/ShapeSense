# 1_data_integration - F18: A time limit killed the second holdout build (failure search)
- LLM: Claude Opus 5.5 (claude-opus-5-5), with web search
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Entry: F18 · Question from [failure_search_prompts.md](../../failure_search_prompts.md#f18) · Record: [F18](../inferred_prompts.md#f18)

## Prompt
> Search the web and the research literature to answer the question below. Cite every claim with a link, and prefer papers, official documentation and bug trackers over blogs. Separate what is well established from what is a single report or your own reasoning. Then say how the findings apply to our project: a small CNN that classifies 10 shapes in 64x64 grayscale images merged from four public sources, with five training arms (A0 real only, A1 real + augmented, B real + synthetic, A2 full mix, P synthetic pretraining) compared by macro F1 on sealed test data.
>
> How should long data builds handle being killed part way (time limits, interruptions)? Search for best practices such as writing to a temporary folder and renaming atomically, manifests and checksums, and resumable builds.

## Response

### Well established

- **Rename is the atomic commit step.** Python's documentation for [`os.rename` and `os.replace`](https://docs.python.org/3/library/os.html) says that a successful rename "will be an atomic operation (this is a POSIX requirement)". It also says the operation "may fail if src and dst are on different filesystems". `os.replace` raises `OSError` if the destination is a non-empty directory. On Windows, `os.rename` always raises `FileExistsError` when the destination exists.
- **Atomic does not mean durable.** In an [LWN discussion](https://lwn.net/Articles/323360/), rename guarantees that the name never disappears but says nothing about the file's contents, and POSIX does not define behaviour across a system crash. Hence the usual recipe: write the temp file, fsync it, rename, then fsync the parent directory. Atomic-write libraries such as Google's [renameio](https://pkg.go.dev/github.com/google/renameio) package this temp-file-then-rename pattern. I did not check each library's exact fsync sequence.
- **Applications get this wrong often.** Pillai et al. ([OSDI 2014](https://research.cs.wisc.edu/adsl/Publications/alice-osdi14.html)) found that persistence properties differ widely across six Linux file systems. Their ALICE tool found 60 crash vulnerabilities in eleven widely used systems, including databases and version-control tools.
- **Build tools delete partial outputs.** By default GNU make removes a half-written target only when make itself receives a signal. The `.DELETE_ON_ERROR` special target extends this to failed recipes ([GNU make test suite](https://gnu.googlesource.com/make/+/7d484017077089a/tests/scripts/targets/DELETE_ON_ERROR); [Git's Makefile patch](https://lore.kernel.org/all/xmqqfsx1yyza.fsf@gitster.g/T/)). Neither mechanism helps after an uncatchable kill. The usual answer there is to write to a temporary name and rename only on success ([Innolitics](https://innolitics.com/articles/make-delete-on-error/)).
- **Schedulers kill hard after a short grace period.** Slurm sends SIGTERM at the time limit, then SIGKILL after `KillWait`. SIGKILL cannot be trapped, and `--signal` can be used to get an earlier warning ([CoreWeave SUNK docs](https://docs.coreweave.com/products/sunk/run_workloads/handle-slurm-signals)). Preemption uses a separate `GraceTime`, which defaults to 0 ([SchedMD ticket 5867](https://support.schedmd.com/show_bug.cgi?id=5867)). So a build cannot rely on cleaning up after itself. It has to be safe to kill at any instruction.

### Single reports

- Whether `os.replace` is atomic on Windows is not documented by Microsoft. Python bug-tracker discussions ([issue 8828](https://bugs.python.org/issue8828)) call it best effort. Practitioners rely on it for same-volume renames, but I found no official guarantee.
- One library notes that directory fsync does nothing on Windows and uses `MoveFileEx` with write-through flags instead (from the renameio-style results above). That is a single implementation's choice.

### Reasoning (mine, not from a source)

The sources combine into a pattern for a build that produces a folder plus a manifest:

1. **Stage:** build into `name.tmp-<pid>/` on the same volume as the final folder.
2. **Manifest last:** write the manifest (paths, MD5s, counts per group) into the staging folder after all files are written. Then re-read every file against it.
3. **Commit:** rename the staging folder to the final name. The final folder should not already exist, because `os.replace` refuses a non-empty directory. Any half-done folder therefore always carries a `.tmp` name and is never mistaken for a finished one.
4. **Resume, or restart:** with deterministic, seeded output, it is simpler and safer to delete the staging folder and restart than to resume. Resuming needs a per-item journal and checksums, which is worth it only when the build is very long.
5. **Run long builds under a stall watcher, not a hard cap.** If a cap is unavoidable, catch SIGTERM and stop at a clean boundary.

### How it applies to ShapeSense

The record shows that `fresh_holdout_2.py` writes PNGs as it goes and writes the manifest CSV only at the end. That is why a 500-second kill left images with no manifest. The manifest-last half of the pattern was already in place, and it is what made the partial folder detectable. What was missing is staging plus atomic rename: the partial folder had the final name. The builder replays the first holdout's seeded walk and compares hashes before continuing. That reproducibility proof is stronger than most resumable-build schemes, and it makes deleting and rebuilding the right recovery.

## Validation
The documented cause was a hard 500-second limit that left a partial folder with no manifest. The literature agrees with the cause and with the recovery: delete the untrusted partial output and rebuild deterministically. It also supports the record's own suggested safeguard, a temporary folder renamed only after the manifest is written, and adds that the rename must stay on the same volume. Durability against power loss (fsync) is a separate issue that the record does not cover. It matters less here, because the hash check catches corrupt files. Nothing found contradicts the record.

## Our decision
The project deleted the partial folder, rebuilt with no time limit, and confirmed that the first holdout's manifest reproduced before sealing 4,500 images. Long jobs now run under a stall watcher. The findings suggest one further change: stage the holdout build in a temporary folder and rename it after the manifest is verified, so a kill can never leave a folder that looks finished. Nothing was changed in this pass.

## Measured effect
None. Research only, no run.
