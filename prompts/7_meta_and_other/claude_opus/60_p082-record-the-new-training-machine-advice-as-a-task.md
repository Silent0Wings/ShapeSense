# 7_meta_and_other - P082: Record the new-training-machine advice as a task with an owner
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P082. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

did you record this as  task with a owner , 40256377 =[

<pasted_content id="588d">
name: advise-new-training-machine
description: "Advise the user to move ShapeSense GPU/CNN training to their new machine (32 GB RAM, NVIDIA RTX 3080, high-core CPU)"
metadata:
  node_type: memory
  type: project
  originSessionId: [session ID removed]
  modified: 2026-11-08T09:09:25.160Z
---

The user has a new machine available: 32 GB RAM, NVIDIA RTX 3080, high-core-count CPU. Advise moving ShapeSense training there whenever training work comes up (new CRISP-DM iterations, 5 seeds, the deferred ablations). Prefer it over Colab and over the current 14-core CPU-only machine.

**Why:** Stage 4 is CPU-only on the current machine, so one CRISP-DM loop costs most of a day (2026-11-08). The 3080 covers the CNN and the high-core CPU covers augmentation and synthetic rendering, which is the bottleneck once a GPU is used. Estimated 1–2 h for the 17-run budget instead of 12+ h (estimate, not measured).

**When (stage):** Advise it at **Stage 4 (training), before launching it** (`python run_pipeline.py --stages 4`): after Stages 1-3 have passed, before the tuning grid and arm x seed sweep start. Advise it again whenever Stage 4 must be rerun, such as a CRISP-DM iteration or re-freeze of Stage 1, a recipe change, more seeds or the ablations. Not needed for Stages 0-3, 5 and 6, which run fine on CPU; Stage 5 and 6 can stay on the current machine if the trained artifacts are copied back.

**How to apply:** Give the advice before a Stage 4 run starts, not in the middle of one. Before moving, the code needs GPU support (Stage 4 training and Stage 5 inference run on CPU only) and a CUDA build of PyTorch. Train every arm of one experiment on the same hardware and software, because GPU and CPU runs aren't numerically identical and mixing them breaks the "arms differ only in data" rule; record the machine in the report. Copy `data_set/unified/` and `configs/splits/`.
</pasted_content id="588d">

]

## Response

No. It is not recorded as its own task yet. The closest entry is N01 (training ran on the CPU, about 24 h per run, owner 40256377). N01 records the problem, not the move to the new machine. The memory is evidence for the move, so I added it as decision **D04** and linked it to N01 and the GPU commits.

**D04 in the worksheet**

It is recorded in `results/llm_comparison/attribution_worksheet.csv`, which now has 94 entries.

| Field | Value |
|---|---|
| What | Move training from the CPU-only machine to the new one (RTX 3080, 32 GB RAM, high-core CPU) |
| Owner | **40256377** |
| proposed_by / llm_involved | opus_medium_5.5 / opus_medium_5.5 |
| llm_role | `proposed` |
| attribution_source | `chat`: the advice is in Claude Code's project memory from 2026-11-08 |
| Commits | `a71b5e1` (GPU pinned), `52f6e64` (GPU tuning winner), `8984a50` (report GPU statements), `ed7f55a` (README needs CUDA). Linked as tasks T18, T23, T24 and T25. |
| Related | N01 (the CPU training problem), C39 (the measured speed afterwards) |

I did not put the memory file's path in the notes, because it contains the local Windows user folder and the repo will be public.

**Expected versus measured**
The memory estimated 1 to 2 h instead of 12+ h for the 17-run budget. The log later measured 175 trainings in about 3 h 50 min in the iteration 3 search. That makes a good validation example, because the LLM's estimate can be checked against measured times.

**Two differences between the memory and N01**
- Cause: N01 says training ran on the CPU by mistake. The memory says the old machine was CPU-only, so there was no GPU to use. Both can be true, for example if a run stayed on the CPU after the move. Check which wording is right.
- Time: N01 says about 24 h per run. The memory says a CRISP-DM loop cost 'most of a day' and estimates 12+ h for the run budget. Pick one figure for the slides, or present 24 h as your measured worst case.

##### Why D04 is a decision, not a failure
The move to the new machine is a choice the team made in response to the CPU-only runs. Recording it as D04 links the cause (N01), the fix (the GPU commits) and the measured result (C39) in one place, so a grader can follow the reasoning from the problem to the decision.

##### Why the memory is cited without its path
The memory file's path contains the local Windows user folder. The repo is planned to be public, so the path is left out and the source is described as the project memory from 2026-11-08.

##### What is unverified
- The 1 to 2 h estimate is the memory's own estimate. The answer notes that the log later measured 175 trainings in about 3 h 50 min, which is a different quantity (the iteration 3 search), so the two are not directly comparable.
- The claim that the GPU commits (`a71b5e1`, `52f6e64`, `8984a50`, `ed7f55a`) were made for this decision is an attribution by the answer, based on their messages.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
