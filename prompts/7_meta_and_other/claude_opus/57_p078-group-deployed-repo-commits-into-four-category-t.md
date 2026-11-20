# 7_meta_and_other - P078: Group deployed-repo commits into four category tasks instead of one by one
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P078. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

@ignore/deployed_commits.txt  but you dont need to add each 1 by 1 , its perferd if you group them by category

## Response

`ignore/deployed_commits.txt` (not in the repository) has the same 85 commits as this repo: the same hashes, ending with today's `5f65ae9`. The command was run inside `ShapeSense` instead of `ShapeSense_Deployed`, so the file adds nothing new.

#### Deployed tasks, grouped by category

In [commit_tasks.md](../../../results/llm_comparison/commit_tasks.md), the 13 one-by-one tasks became 4 groups under the umbrella task T86. Each group lists its commits:

| Task | Category | Deployed commits |
|---|---|---|
| T86 | Whole deployment (ONNX, Vercel, in-browser prediction, presentation) | umbrella |
| T87 | Releases: protected preview, 3 public freezes, phone layout, 11-16 and 11-17 releases | 4 freeze files, `c671315`, `610d76c` |
| T88 | Interactive presentation: six parts, one per presenter, 90% of the repo, graphic slides | `44e3230`, `b19e25d`, `6c67833` |
| T89 | Interactive explanations: stage design, CRISP-DM wheel, hover help, sliders, stepper | `b16b172`, `863ee07`, `5fef3bb` |
| T90 | Live prediction: Predict button and drawing toolbar | `24f7170` |

The task list now has 90 tasks: T01 to T85 from this repo, and T86 to T90 for the deployed site.

##### Why the grouping changed
The earlier version listed 13 deployed tasks one by one. Grouping them by category keeps each row about one kind of work (releases, presentation, interactive explanations, live prediction), which matches the user's request. The commits are the same, so the grouping changes the presentation, not the coverage.

##### Correction to the earlier count
The earlier answer (P077) gave a total of 99 tasks. This answer replaces that with 90. The 13 one-by-one rows (T87 to T99) became 4 category rows (T87 to T90), which removes 9 rows from the total. The 99 figure is superseded.

##### What the new file did and did not add
The file `ignore/deployed_commits.txt` lists the same 85 commits as this repo, so it could not supply the missing early deployed commits. The command was run in the wrong folder, which is why the file adds nothing new. The corrected command uses `git -C` to point at the deployed repo.

#### What is still missing

The deployed site's early build commits (11-11 to 11-16) are still missing. To get them, run this from the `ShapeSense` folder. `-C` points git at the deployed repo:

```
git -C <home>\Github\ShapeSense_Deployed log --reverse --date=short --format="%h|%ad|%s" > ignore\deployed_commits.txt
```

Those commits will go into the same categories, or into new ones if needed, not one by one.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
