# 4_testing - C57: Files that should never have been tracked purged from history
- LLM: Gemini 4 Neon 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-10
- Entry: C57 (`change`, `deployment (not a course stage)`)
- Owner / Proposed by: 40248536 / gemini_4_neon
- Calibration: `winning-decision (70% tier)`
- Grounding sources: `docs/crisp_dm/iteration_log.json`, `.gitignore`, commit `f3b3bdb`, `ShapeSense_Deployed/README.md`, `ShapeSense_Deployed/snapshot/manifest.json`

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

## Prompt
Some files that our ignore rules and project rules exclude are tracked in Git history, including local notes and unused images. How do we remove them from every commit on every branch and tag, keep them on disk, and check that all remaining commits still pass the commit guard?

## Response
To publish or share branches cleanly without losing local working files on disk, rewrite the full Git history rather than adding a single tip `git rm`:

1. **Back up local working files before rewriting:** Copy the target files that you want to preserve outside Git tracking into an ignored local archive (e.g., `ignore/purged_files/`, since `ignore/` is already in `.gitignore`) before running any destructive filter, and ensure `.gitignore` explicitly covers `plan_issues.md`, `artifacts/stage4_cpu_recipe_2880473b/`, `results/llm_comparison/README.md`, `ignore/`, `.commit_guard/`, and `.pre-commit-config.yaml`.
2. **Inventory every excluded/unwanted path in history:** Group all paths to strip across branches and tags:
   - Local working notes & backups: two local working notes, the to-do list, nine planning notes under `ignore/`, `plan_issues.md`, and `artifacts/stage4_cpu_recipe_2880473b/.gitkeep`.
   - Early setup/research notes: `docs/setup.md`, `docs/goal.md`, `reports/`, and `research_notes/` (7 files).
   - Unused media & source files: 15 sample images, two unused banner/icon images, and a Paint project file (18 files).
3. **Purge paths and rewrite referencing commit messages across all refs:** Use `git filter-repo` (operating on `--refs` across every branch and tag) with `--invert-paths --paths-from-file <list>` so those files never appear in any historical tree, and pass `--prune-empty always` so the commits that touched only those files (4 commits) are cleanly dropped rather than left as empty commits. Simultaneously pass a `--message-callback` (or `commit-callback`) to reword lines in commit messages that referenced local working notes or quoted the attribution string banned by the commit guard.
4. **Restore local untracked copies and lock `.gitignore`:** Place the preserved notes and images back under `ignore/purged_files/` (untracked) and commit the updated `.gitignore` rules (`plan_issues.md`, `artifacts/stage4_cpu_recipe_2880473b/`) alongside the audit record.
5. **Re-verify every remaining commit against the commit guard:** Run the commit guard's message, identity, and content checks over the full rewritten commit range (`git rev-list --all`) to confirm zero banned attribution strings, zero excluded paths, and valid author/committer identities remain, and verify the working tree's pipeline outputs and test suite still pass untouched.

## Validation
- Student `40248536` executed the history purge on 2026-11-10 across all branches and tags, backed up the removed notes and images locally under `ignore/purged_files/`, updated `.gitignore`, and ran the commit guard across every remaining commit (message, identity, and content checks all passing) as well as the full 535-test suite and 157-read test-access log audit.
- Commit `f3b3bdb` recorded the cleanup in `docs/crisp_dm/iteration_log.json` (`changes` entry "Files that should never have been tracked purged from history"), and `ShapeSense_Deployed/tools/snapshot.py` verified `f3b3bdb` at 518 tracked files (`tracked_tree_sha256: 9d250038b2dd9bddc4a9eb256972ff776e353e274b4c9b003575dbe1a9176e7a`).

## Our decision
- Executed Gemini 4 Neon's full-history purge plan on 2026-11-10, dropping the 4 commits that touched only excluded files, rewording affected commit messages, preserving untracked copies in `ignore/purged_files/`, adding `.gitignore` entries for `plan_issues.md` and `artifacts/stage4_cpu_recipe_2880473b/`, and recording the audit in commit `f3b3bdb`.

## Measured effect
- Excluded local notes (including the one quoting banned attribution text), 7 early research/setup notes, and 18 unused images/source files were removed from every commit across all branches and tags; 4 empty commits were dropped.
- Remaining commits (518 tracked files at `f3b3bdb`) pass 100% of the commit guard's message, identity, and content checks, and all 535 project tests and 157-read `test_access.log` invariants hold.

---

## Upgraded & Expanded Technical Analysis (`C57`)

### 1. History-Rewrite Mechanics (`git filter-repo` vs. Tip `git rm`)
- **Why Tip `git rm` Is Insufficient:** Deleting an excluded file at `HEAD` leaves its blob reachable in every ancestor tree object; checking out any historical commit or tag still exposes the local notes, banned attribution text, or unused binaries, and full-history commit guards (`git rev-list --all`) continue to fail.
- **Filter-Repo Tree & Message Transformation:**
  - `--invert-paths --paths-from-file <list>` strips all 38 target paths (13 local working/planning notes and `.gitkeep` under `ignore/`, `plan_issues.md`, `artifacts/stage4_cpu_recipe_2880473b/.gitkeep`; 7 early setup/research notes under `docs/setup.md`, `docs/goal.md`, `reports/`, `research_notes/`; and 18 unused media/Paint files) from every commit tree across `--refs` (all branches and tags).
  - `--prune-empty always` drops the 4 commits whose tree diffs became empty after path removal, preventing degenerate zero-diff commits in `git log`.
  - `--message-callback` rewrites commit messages that referenced purged working notes or quoted banned attribution strings so historical commit metadata satisfies the commit guard.

### 2. Verification Algebra & Working-Tree Preservation
1. **Pre-Flight Local Backup (`ignore/purged_files/`):** Copying all target files into the gitignored `ignore/purged_files/` directory *before* history rewriting guarantees zero data loss on the local workstation while keeping the files invisible to Git.
2. **Universal Quantifier Commit-Guard Audit:**
   - Iterate over $\forall c \in \texttt{git rev-list --all}$: verify message check (zero banned attribution substrings), identity check (valid author/committer), and tree content check (`git ls-tree -r <c> --name-only` contains zero excluded paths).
   - Verify tip tree equivalence at commit `f3b3bdb`: `518` tracked files (`tracked_tree_sha256: 9d250038b2dd9bddc4a9eb256972ff776e353e274b4c9b003575dbe1a9176e7a`), `535` passing tests, and `157` cumulative audited entries in `artifacts/test_access.log`.


---

## Reviewer addendum (cross-entry review, not part of the simulated response)

**Depth only close reading reveals:** `--prune-empty always` is load-bearing. Without it, the four commits that touched only excluded files remain as empty commits. The message rewrite is a separate pass from the path purge: `--invert-paths` alone leaves the banned string in the message, and the guard would still fail on a clean tree.

**Changelog:** [1] `--prune-empty` rationale; [2] message rewrite as a separate pass; [3] full-history rewrite vs tip `git rm`; [4] guard re-run scope is `git rev-list --all`.

**Open questions:** Every commit hash after the first purged one changes. Do any PRs, issue links or deployment pins reference old hashes? `git filter-repo` needs a clean working tree; the entry should say so.
