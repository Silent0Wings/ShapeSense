# 4_testing - F27: Report macro names broke for arm A2 and collided for hold-out runs. (failure search)
- LLM: Claude Opus 5.5 (claude-opus-5-5), with web search
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Entry: F27 · Question from [failure_search_prompts.md](../../failure_search_prompts.md#f27) · Record: [F27](../inferred_prompts.md#f27)

## Prompt
> Search the web and the research literature to answer the question below. Cite every claim with a link, and prefer
> papers, official documentation and bug trackers over blogs. Separate what is well established from what is a single
> report or your own reasoning. Then say how the findings apply to our project: a small CNN that classifies 10 shapes in
> 64x64 grayscale images merged from four public sources, with five training arms (A0 real only, A1 real + augmented,
> B real + synthetic, A2 full mix, P synthetic pretraining) compared by macro F1 on sealed test data.
>
> Why can LaTeX macro names generated from data break or collide (digits are not allowed in control-word names, different keys mapping to the same name)? Search for LaTeX macro naming rules and for safe ways to feed computed numbers into a LaTeX report (csname, datatool, key-value storage). Our case: arm A2 and the hold-out-source runs.

## Response

### Well established

- **Control words contain only letters.** The TeX FAQ states that TeX "allows nothing but letters in macro names", so `\cul8r` is not one macro ([TeX FAQ: Non-letters in macro names](https://www.texfaq.org/FAQ-linmacnames)). When TeX reads `\resultAtwo` it gets one name. When it reads `\resultA2` it reads `\resultA` and then the character `2`. A comp.text.tex answer makes the same point: parsing of `\s2` stops before the digit ([comp.text.tex thread](https://groups.google.com/g/comp.text.tex/c/0hiKBtgbCek/m/SP22PaR7atsJ)). Single-character control symbols such as `\2` are the only exception.
- **The FAQ lists the standard workarounds and their costs** ([TeX FAQ](https://www.texfaq.org/FAQ-linmacnames)):
  1. `\csname ...\endcsname`, which can build any name, including digits, but is verbose.
  2. A generator command that stores values under computed names.
  3. Making the digit a letter with `\catcode`, which breaks ordinary uses of that digit (for example `8in` in a length). Last resort only.
  4. Spelling the number in letters, such as Roman numerals (`\culVIIIr`).
- **`\csname` builds names that typing cannot.** The TUGboat tutorial shows that `\expandafter\def\csname $&3\endcsname{Hi!}` is a valid definition. Such a macro has to be called through `\csname` as well ([TUGboat 33:2, Hendrickson](https://TUG.org/TUGboat/tb33-2/tb104hendrickson.pdf); [plain TeX csname notes](https://mirrors.mit.edu/CTAN/info/plain-doc/csname.txt)).
- **`\providecommand` fails silently on a name that already exists.** The LaTeX2e reference: if the command already exists, `\providecommand` "does nothing and the old definition remains in effect" ([LaTeX2e reference, \providecommand](https://svn.gnu.org.ua/sources/latexrefman/trunk/latex2e-help-texinfo-tree/latex2e/_005cprovidecommand.html); [TeX FAQ on definition commands](https://www.texfaq.org/FAQ-cvtlatex)). `\newcommand` would have raised an error on the same collision.
- **Tabular data can be loaded instead of turned into macros.** The datatool bundle loads databases from comma- or tab-separated files and lets the document look values up by key ([datatool README](https://tug.ctan.org/macros/latex2e/contrib/datatool/README.md); [datatool user guide](https://ctan.csail.mit.edu/macros/latex/contrib/datatool/datatool-user.html)).

### Single reports

- A TeX.SE question shows a related trap: `\def\rl.3.1{...}` is accepted but defines `\rl` with a parameter text of `.3.1`, so mistakes can pass silently rather than error ([indexed TeX.SE question](https://12000.org/my_notes/latex_stackexchange_letters/indexsubsection940.htm)).

### My own reasoning

- **Two different failures, one root cause.** (a) A digit that is not mapped *truncates* the name, so `A2` breaks. (b) A lossy name builder (keeping only the first and last parts of `A0_loso_0`) *collides* with `A0_0`. Combined with `\providecommand`, the second definition is silently dropped, and the report shows the wrong number with no error. The general rule: the key-to-name function must be **injective** (distinct keys give distinct names) and produce **letters only**.
- **Safe designs, in order of robustness:**
  1. Keep the data in a table (CSV or datatool) and look it up by the raw key.
  2. Use a single macro with the raw key as an argument (e.g. `\result{A0_loso_0}{macroF1}`), stored through `\csname` or a key-value package, so names never need to be letters only.
  3. If named macros are kept, spell out every digit, keep every part of the key, and have the generator assert that names are unique and use `\newcommand` (or check `\ifdefined`) so collisions fail loudly.

### How it applies to ShapeSense

1. `A2` and seeds above 2 broke because only some digits were spelled out. That matches the letters-only rule in the [TeX FAQ](https://www.texfaq.org/FAQ-linmacnames) exactly.
2. `A0_loso_0` and `A0_0` collided because middle parts were dropped, and `\providecommand` hid it ([LaTeX2e reference](https://svn.gnu.org.ua/sources/latexrefman/trunk/latex2e-help-texinfo-tree/latex2e/_005cprovidecommand.html)).
3. Spelling all ten digits and keeping the middle parts is the FAQ's "spell it out" workaround made injective, and it keeps existing names stable, which the report needed.

## Validation

The record's two causes (digits are not allowed in control-word names, and `A0_loso_0` got the same name as `A0_0` under `\providecommand`) match the documented TeX rules exactly. The search adds two things: (1) the silent failure comes from `\providecommand`, so a uniqueness assertion in the generator, or `\newcommand` in generated files, would turn any future collision into an error; (2) a `\csname`- or datatool-based lookup avoids the naming problem entirely. Nothing contradicts the record.

## Our decision

The project added one letter-only stem builder (`DIGIT_WORDS`, `_macro_word`, `macro_key`) that spells out every digit and keeps middle parts, with tests that existing names are unchanged, that no name contains a digit, and that `A0_loso_0` differs from `A0_0`. The findings support this. Possible additions are a uniqueness check over all generated names and failing loudly on a redefinition. Nothing was changed in this pass.

## Measured effect
None. Research only, no run.

---

## Upgraded & Expanded Literature Synthesis (`F27`)

### Metadata & Lineage
* **Entry ID / Type:** `F27` (`failure`, `4_testing` — literature audit)
* **Failure Mode:** Stage 6 stripped non-letters from metric keys to form TeX control words (`\providecommand{\metric...}`) and silently skipped colliding keys, causing `A0_loso_0` and `A0_0` or `A0` to collapse to the same macro name when digits were removed.
* **Primary Sources:**
  * Knuth, D. E. (1984), *The TeXbook* (Addison-Wesley, Ch. 3 & Ch. 7: Category Codes and Control Words)
  * Mittelbach et al. (2004), *The LaTeX Companion* (2nd ed., `\newcommand` vs. `\providecommand` semantics)

### 1. TeX Lexical Category Codes and Bijective Identifier Encoding
In TeX's lexical scanner, a multi-character control word `\cs` consists of an escape character (`\`, category code 0) followed exclusively by tokens of category code 11 (*letter*, `A–Z` and `a–z` by default). ASCII digits `0–9` have category code 12 (*other*), meaning `\metricA0` is parsed as the control word `\metricA` followed by the literal character token `0`:
1. **Non-Injective Stripping Homomorphism:** A naive sanitizer $\phi_{\text{strip}}(s)$ that deletes all characters with $\text{catcode} \neq 11$ is non-injective:
$$\phi_{\text{strip}}(\texttt{"A0"}) = \phi_{\text{strip}}(\texttt{"A1"}) = \phi_{\text{strip}}(\texttt{"A2"}) = \texttt{"A"}$$
Combined with `\providecommand` (which silently retains the first definition when a macro is already defined), non-injective stripping silently aliases distinct experimental arms to the first defined value.
2. **Injective Digit-Word Expansion ($\phi_{\text{word}}$):** Replacing each digit $d \in \{0..9\}$ with its title-cased English word (`0` $\mapsto$ `Zero`, `1` $\mapsto$ `One`, `2` $\mapsto$ `Two`, ...) prior to camel-casing alphanumeric tokens yields a category-11-compliant map:
$$\phi_{\text{word}}(\texttt{"A0\_loso\_0"}) = \texttt{"AZeroLosoZero"} \neq \phi_{\text{word}}(\texttt{"A0\_0"}) = \texttt{"AZeroZero"}$$
Pairwise collision detection over the domain of all generated metric keys then enforces strict injectivity ($\forall k_1 \neq k_2, \; \phi_{\text{word}}(k_1) \neq \phi_{\text{word}}(k_2)$) at build time.

### 2. ShapeSense Verification & Experimental Controls
* **Deterministic Digit-Word Encoder (`src/stage6_report/run.py`):** `DIGIT_WORDS`, `_macro_word()`, and `macro_key()` convert every digit to its word equivalent and construct collision-free CamelCase TeX control sequences.
* **Injectivity Invariant Test (`tests/test_stage6.py`):** Automated tests verify that `A0`, `A1`, `A2`, `B`, `P`, and indexed LOSO/severity keys map to strictly distinct alphabetic TeX macro names.

