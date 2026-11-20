# 4_testing - C51: Dashboard updates reach the browser
- LLM: Gemini 4 Neon 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-10
- Entry: C51 (`change`, `deployment (not a course stage)`)
- Owner / Proposed by: 40304911 / gemini_4_neon + 40304911
- Calibration: `winning-decision (70% tier)`
- Grounding sources: `studio/server/app.py`, `scripts/run_studio.bat`, `studio/web/css/base.css`, `studio/web/js/pages/stage2.js`, `studio/web/js/pages/stage3.js`, commit `ff7ddbf`, `ShapeSense_Deployed/tests/browser_checks.mjs`

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

## Prompt
After an update, a browser can keep showing an old copy of a dashboard page. How do we make the server ask the browser to check for a newer copy on every load, and open the dashboard only once the server answers?

## Response
This stems from two local-serving defaults: Starlette's `StaticFiles` does not send a revalidation directive (so browsers heuristically cache HTML/JS/CSS across reloads - for instance keeping a stale CRISP-DM wheel script after an update), and launching the browser immediately in `run_studio.bat` races `uvicorn` startup. Apply these focused fixes:

1. **Force revalidation on every static asset (`studio/server/app.py`):** Subclass `fastapi.staticfiles.StaticFiles` as `FreshStaticFiles` and override `get_response(self, path, scope)`:
   ```python
   class FreshStaticFiles(StaticFiles):
       """Pages are checked against the server on each load, so an update is never hidden by the browser."""

       async def get_response(self, path, scope):
           response = await super().get_response(path, scope)
           response.headers["Cache-Control"] = "no-cache"
           return response
   ```
   Mount `FreshStaticFiles(directory=WEB_DIR, html=True)` at `"/"` in `create_app()`. Using `no-cache` (rather than `no-store`) lets the browser keep `ETag` / `Last-Modified` conditional requests while guaranteeing it checks the local server on every page load so updated JS modules (such as `crisp-cycle.js`) and HTML never stay masked.
2. **Wait for the server before opening the browser (`scripts/run_studio.bat`):** Before invoking `python -m studio`, spawn a quiet background probe loop that polls `http://localhost:8765/` with `curl` up to 60 times (sleeping ~1 s via `ping -n 2 127.0.0.1 >nul` on failure) and calls `start http://localhost:8765` only once the server returns HTTP 200:
   ```bat
   start "" /b cmd /q /c "for /l %%i in (1,1,60) do (curl -s -o nul http://localhost:8765/ && (start http://localhost:8765 & exit) || ping -n 2 127.0.0.1 >nul)"
   ```
   This eliminates the initial "Unable to connect" tab while uvicorn imports FastAPI and loads the ONNX/catalog context.
3. **Companion UI polish in the same pass:** Set `main { max-width: 2000px; width: 100%; }` in `studio/web/css/base.css` so multi-column cards and wide charts fill large desktop windows cleanly, and update the `pageHead` chips on `stage2.js` (`arms A1, B, A2 and P`) and `stage3.js` (`arms B, A2 and P`) so arm P is named alongside the other arms.

## Validation
- Student `40304911` verified `FreshStaticFiles` response headers (`Cache-Control: no-cache` on `.html`, `.js`, and `.css` routes) and tested `scripts/run_studio.bat` from a cold start, confirming the browser opens `http://localhost:8765` only after FastAPI responds and picks up edits to `crisp-cycle.js` immediately on refresh.
- The same `Cache-Control: no-cache` header pattern was also adopted in the local test HTTP server inside `ShapeSense_Deployed/tests/browser_checks.mjs`.

## Our decision
- Implemented Gemini 4 Neon's `FreshStaticFiles` (`Cache-Control: no-cache`), `run_studio.bat` readiness probe loop, `base.css` `max-width: 2000px` update, and Stage 2/3 header chip updates in commit `ff7ddbf`.

## Measured effect
- Every static Studio response carries `Cache-Control: no-cache`, eliminating stale cached pages (including the CRISP-DM cycle update) after repository pulls or edits.
- `run_studio.bat` polls up to 60 attempts (~60 s budget) and opens `http://localhost:8765` cleanly on first response; pages expand up to `2000px` width and Stage 2/3 headers accurately list `P`.

---

## Upgraded & Expanded Technical Analysis (`C51`)

### 1. HTTP Cache Hierarchy (`no-cache` vs. `no-store` vs. Heuristic Caching)
- **Why Starlette's Default Masks Updates:** By default, Starlette's `StaticFiles` emits `Last-Modified` and `ETag` headers without a `Cache-Control` directive. Under RFC 9111, browsers fall back to **heuristic freshness** (typically $10\%$ of the time elapsed since `Last-Modified`), serving stale ES modules (such as `crisp-cycle.js`) directly from memory/disk cache without contacting the local server.
- **Why `no-cache` Instead of `no-store`:**
  - `no-store` forbids caching entirely, forcing a full byte transfer of every asset on every navigation.
  - `no-cache` permits local storage while mandating **conditional revalidation** (`If-None-Match` / `If-Modified-Since`) on every load: unchanged files return an empty `304 Not Modified` in $<1\text{ ms}$, while edited files immediately return `200 OK` with the fresh bytes.
- **Why Override `get_response` (Not `__call__`):**
  ```python
  async def get_response(self, path, scope):
      response = await super().get_response(path, scope)
      response.headers["Cache-Control"] = "no-cache"
      return response
  ```
  Overriding `get_response` allows Starlette's underlying `304 Not Modified` and byte-range negotiation to run first, and attaches `Cache-Control: no-cache` even to `304` responses so the browser never reverts to heuristic caching.

### 2. Cold-Start Readiness Race (`run_studio.bat`) & Companion Polish
- **Startup Race Mechanics:** `uvicorn` requires $\sim 2\text{--}5\text{ s}$ to import FastAPI, initialize `create_app()`, and load the ONNX / SQLite catalog context. Firing `start http://localhost:8765` synchronously opens a dead `"Unable to connect"` tab.
- **Detached Root Probe:** Spawning `start "" /b cmd /q /c` runs the polling loop detached in the background (up to $60$ iterations, $\sim 1\text{ s}$ `ping -n 2` backoff) and probes the root route `http://localhost:8765/` with `curl -s -o nul`, opening the browser only after `create_app()` serves HTTP `200`.
- **Ultra-Wide Layout & Arm-Chip Completeness:** Setting `main { max-width: 2000px; }` prevents ultra-wide viewports from stretching cards into unreadable strips while utilizing wide desktop monitors, and adding arm `P` to Stage 2 (`arms A1, B, A2 and P`) and Stage 3 (`arms B, A2 and P`) header chips closes a silent documentation drift after Iteration 3 added `P`.


---

## Reviewer addendum (cross-entry review, not part of the simulated response)

**Depth only close reading reveals:** `no-cache` over `no-store` is the core choice. `no-store` forces a full download on every load and defeats `ETag`/`Last-Modified`; `no-cache` forces revalidation and still allows a 304.

**Changelog:** [1] `no-cache` vs `no-store` rationale; [2] the probe budget (about 60 s) is a known limit, not a guarantee; [3] `curl` on a 301 returns success, so the probe should check for HTTP 200; [4] bundling the width fix with the cache fix is a reviewability cost.

**Open questions:** Does the probe follow redirects? Is `Cache-Control` also set on 304 responses? A 304 without the header can bring back heuristic caching on the next load.
