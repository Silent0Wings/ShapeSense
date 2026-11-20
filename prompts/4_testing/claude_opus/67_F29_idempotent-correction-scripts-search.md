# 4_testing - F29: The dashboard listed arm P twice. (failure search)
- LLM: Claude Opus 5.5 (claude-opus-5-5), with web search
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Entry: F29 · Question from [failure_search_prompts.md](../../failure_search_prompts.md#f29) · Record: [F29](../inferred_prompts.md#f29)

## Prompt
> Search the web and the research literature to answer the question below. Cite every claim with a link, and prefer
> papers, official documentation and bug trackers over blogs. Separate what is well established from what is a single
> report or your own reasoning. Then say how the findings apply to our project: a small CNN that classifies 10 shapes in
> 64x64 grayscale images merged from four public sources, with five training arms (A0 real only, A1 real + augmented,
> B real + synthetic, A2 full mix, P synthetic pretraining) compared by macro F1 on sealed test data.
>
> How do you make a data correction or migration script idempotent, so running it twice does no harm? Search for idempotency patterns in database migrations and data-fix scripts.

## Response

### Well established (official documentation)

Mature tools rely on three patterns.

- **Pattern 1: record what has been applied, and never apply it again.** Flyway: "Versioned migrations are applied to a target database in order exactly once". The `flyway_schema_history` table tracks which migrations have run and stores a checksum "to detect accidental changes", so editing an already-applied migration is an error, not a silent re-run ([Redgate Flyway: versioned migrations](https://documentation.red-gate.com/fd/versioned-migrations-273973333.html); [schema history table](https://documentation.red-gate.com/fd/flyway-schema-history-table-273973417.html)).
- **Pattern 2: check the current state before acting (preconditions).** Liquibase changesets can carry preconditions such as "column exists". `onFail="MARK_RAN"` skips the changeset and records it as run, while `CONTINUE` skips it and checks again next time. These options apply only to preconditions inside a changeset ([Liquibase preconditions](https://docs.liquibase.com/concepts/changelogs/preconditions.html)).
- **Pattern 3: make the write itself idempotent (upsert by key).** PostgreSQL's `INSERT ... ON CONFLICT DO NOTHING` skips a row that would violate a unique constraint, and `ON CONFLICT DO UPDATE` updates the existing row atomically. Conflicts are detected only against a unique index or constraint (the "arbiter") ([PostgreSQL INSERT](https://www.postgresql.org/docs/current/sql-insert.html)). Without a uniqueness rule there is nothing for the database to detect, and a second insert just adds a duplicate.

### Single reports and community guidance

- A Stack Overflow answer (archived copy) describes the usual idempotent setup as a negated `*Exists` precondition with `MARK_RAN` ([best practices on Liquibase preconditions](https://kiwix.lema.org/stackoverflow.com_en_all_2023-11/questions/61054021/best-practices-on-liquibase-preconditions)). A forum answer explains that `CONTINUE` leaves the changeset unmarked so it is checked again on every update ([forum: onFail CONTINUE](https://forum.liquibase.org/t/precondition-onfail-continue/956)). One forum report says a MARK_RAN changeset was still rolled back in Liquibase 4.4.1 ([forum thread](https://forum.liquibase.org/t/liquibase-rolls-back-a-change-whose-exectype-is-mark-ran/5745)). Preconditions have edge cases of their own.
- Liquibase's blog notes that `runOnChange` re-runs a changeset whenever its content changes, which suits views and procedures. Such changesets must then be safe to re-run ([Liquibase blog: dealing with changing changesets](https://www.liquibase.com/blog/dealing-with-changing-changesets)).

### My own reasoning: carrying this over to file-editing scripts

A script that edits a source file (a JS array, a JSON config) has no database to enforce uniqueness, so it has to do the work itself:

1. **Set, don't append.** Treat the list as a map keyed by its natural key (the arm id). "Add P" becomes "ensure P exists with these fields". That is the file version of `ON CONFLICT DO UPDATE`.
2. **Check the precondition.** If the key is already present and equal, do nothing. If it is present but different, update it or stop with an error. Never add a second copy (the Liquibase precondition idea).
3. **Assert the invariant before writing.** Keys must be unique, and the set of keys must equal the registry (e.g. the five arms). Refuse to write otherwise. That plays the role of the unique index.
4. **Test by running it twice.** A test that applies the script twice and compares the output to one application proves idempotence directly.
5. **Prefer one source of truth.** If every list is derived from a single registry, there is nothing to patch, and duplication cannot happen in the first place.

### How it applies to ShapeSense

1. `ARM_SERIES` in `studio/web/js/pages/boot.js` got P twice because a correction script appended P on re-application. That is an `INSERT` without a unique key ([PostgreSQL](https://www.postgresql.org/docs/current/sql-insert.html)).
2. The fix the record describes ("check whether the key exists, or merge by arm key, and assert unique keys before writing") is patterns 2 and 3 above. Gemini's suggestion to derive labels from the single `ARM_NAMES` list is point 5, which is the strongest of these.
3. A cheap permanent guard is a unit test that the arm keys in every dashboard list are unique and equal the arm registry, so a duplicate fails a test instead of needing a browser check.

## Validation

The record's documented cause, a correction script that added P a second time when re-applied, is the non-idempotent append that every source above is designed to prevent. The literature agrees with the record's recommended fix and adds two points: (1) a uniqueness invariant should be *enforced* (assertion or test), as databases do with unique indexes, rather than checked once by eye; (2) a run-twice test is the direct proof of idempotence. The record notes that the repo does not name which script made the duplicate, so whether that script itself was made idempotent cannot be confirmed from the record. Nothing contradicts the record.

## Our decision

The project removed the duplicate P entry and checked every dashboard page in a browser. The findings suggest two further steps: a unit test that dashboard arm lists have unique keys matching the arm registry, and deriving those lists from one registry. Nothing was changed in this pass.

## Measured effect
None. Research only, no run.

---

## Upgraded & Expanded Literature Synthesis (`F29`)

### Metadata & Lineage
* **Entry ID / Type:** `F29` (`failure`, `4_testing` — literature audit)
* **Failure Mode:** Re-running an imperative correction script appended a duplicate arm `P` object into `studio/web/js/core/boot.js`, causing duplicate arm entries in the Studio frontend.
* **Primary Sources:**
  * Humble & Farley (2010), *Continuous Delivery: Reliable Software Releases through Build, Test, and Deployment Automation* (Addison-Wesley — Idempotent Configuration & Migration Scripts)
  * Flyway / Liquibase Migration Design Patterns: *Repeatable Migrations and Check-Before-Insert Guards*

### 1. Algebraic Idempotence of Source and State Transformations
A state or file transformation $T: \mathcal{S} \to \mathcal{S}$ is **idempotent** if and only if applying it $k \ge 1$ times yields the exact same state as applying it once:
$$T(T(s)) = T(s) \quad \forall s \in \mathcal{S}$$
1. **Non-Idempotence of Unconditional Text Appending:** Imperative string transformations of the form $T_{\text{append}}(s) = \text{replace}(s, \text{anchor}, \text{anchor} + \delta)$ satisfy $T_{\text{append}}^k(s) = \text{anchor} + k \cdot \delta$, creating silent duplicate entries whenever $k > 1$ (e.g., two `P` arm descriptors in `boot.js`).
2. **Declarative State Projection and Key-Uniqueness Guards:** Transforming a script from imperative delta-patching to declarative full-block projection—or guarding insertion with a primary-key existence predicate (`if key not in target`)—restores $T^2 = T$. Pairing the transformation with a post-condition uniqueness assertion ($|\text{keys}(A)| = |\text{set}(\text{keys}(A))|$) guarantees that duplicate entries cannot survive build verification.

### 2. ShapeSense Verification & Experimental Controls
* **Unique Registry Invariant (`studio/web/js/core/boot.js` & `tests/test_studio_api.py`):** Duplicate arm `P` entries were removed from `boot.js`, and automated verification checks assert that every arm identifier in the Studio configuration and exported `models_manifest.json` appears exactly once.

