# Dataset awareness - Gemini 4 Neon

Gemini 4 Neon (medium effort) was run twice on the eight prompts of [PROMPT.md](../PROMPT.md), both on 2026-11-20.

Official run: [02_sandboxed-replication.md](02_sandboxed-replication.md). Antigravity CLI (`agy`) in print mode with
`--sandbox --new-project`, started from an empty folder outside the repository, told that using any tool would void the
test. It is the only Gemini run made without access to the project files. Summary table:
[`results/verification/README.md`](../../../../results/verification/README.md).

Not counted, kept as a record:
- [00_out-of-protocol-workspace-run.md](00_out-of-protocol-workspace-run.md): the first run, made by hand in
  Antigravity with access to the project files. Its extra details (reevald's 224x224 size, frobertpixto's 4 classes and
  70x70 size) may have come from the workspace.
- [01_four-sources.md](01_four-sources.md): the same reply as `00_`, reformatted. It was filed as an official app-chat
  run by mistake; corrected 2026-11-26.
