"""Fill slides.template.html from the results files and print slides.pdf.

    python slides/build_slides.py

Numbers come from results/improvement_table.json, results/direct_llm_prediction/summary.json
and slides/awareness.json (the Gemini column of the dataset-awareness slide). The PDF is
printed by headless Chromium through Playwright (Node); set PLAYWRIGHT_DIR to a folder whose
node_modules holds playwright (default: the sibling ShapeSense_Deployed checkout).
"""

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLIDES = ROOT / "slides"


def improvement_rows(table: dict) -> tuple[str, str]:
    rows = table["rows"]
    base = rows[0]
    out = [f"<tr><td>Baseline: raw collected images, only resized</td><td class='num'>-</td>"
           f"<td class='num'>{base['mean']:.2f} ± {base['std']:.2f}</td><td class='num'>-</td></tr>"]
    for row in rows[1:]:
        d = row["delta_vs_baseline"]
        cls = "pos" if d > 0 else "neg" if d < 0 else ""
        out.append(f"<tr><td>{row['step'].lstrip('+ ')}</td><td class='num'>{base['mean']:.2f}</td>"
                   f"<td class='num'>{row['mean']:.2f} ± {row['std']:.2f}</td>"
                   f"<td class='num {cls}'>{d:+.2f}</td></tr>")
    std = next(r for r in rows if "standardization" in r["step"])
    takeaway = (f"Transformation does most of the work: standardization alone adds {std['delta_vs_baseline']:+.2f}. "
                f"Cleaning's {rows[1]['delta_vs_baseline']:+.2f} is within the seed spread; its point was correct labels. "
                "Feature selection's input size was chosen on validation before the single test read.")
    return "\n    ".join(out), takeaway


def direct_bars(summary: dict, subset: dict) -> str:
    items = [("Trained CNN (A2, seed 0)", summary["models"]["trained_cnn_a2_0"]["macro_f1_points"]),
             ("Gemini 4 Neon", summary["models"]["gemini_4_neon_medium"]["macro_f1_points"]),
             ("Claude Opus 5.5", summary["models"]["claude_opus_5_5_medium"]["macro_f1_points"]),
             ("Baseline CNN (raw, seed 0)", subset["baseline_0"])]
    lo = 50.0
    rows = [f"<div class='barrow'><span>{name}</span><div class='bar' style='width:{(v - lo) / (100 - lo) * 100:.1f}%'></div>"
            f"<b>{v:.2f}</b></div>" for name, v in items]
    return "\n  ".join(rows) + "<p class='claim' style='margin:6px 0 0;font-size:14px'>Macro F1 on the 200 images; bars start at 50.</p>"


def main() -> None:
    table = json.loads((ROOT / "results" / "improvement_table.json").read_text(encoding="utf-8"))
    summary = json.loads((ROOT / "results" / "direct_llm_prediction" / "summary.json").read_text(encoding="utf-8"))
    awareness = json.loads((SLIDES / "awareness.json").read_text(encoding="utf-8"))
    rows_html, takeaway = improvement_rows(table)
    html = (SLIDES / "slides.template.html").read_text(encoding="utf-8")
    fills = {"IMPROVEMENT_ROWS": rows_html, "IMPROVEMENT_TAKEAWAY": takeaway,
             "DIRECT_BARS": direct_bars(summary, table["direct_llm_subset"]), **awareness}
    for key, value in fills.items():
        html = html.replace("{{" + key + "}}", value)
    if "{{" in html:
        raise SystemExit("unfilled token in slides: " + html[html.index("{{"):html.index("{{") + 40])
    out_html = SLIDES / "slides.html"
    out_html.write_text(html, encoding="utf-8")
    pw_dir = Path(os.environ.get("PLAYWRIGHT_DIR", ROOT.parent / "ShapeSense_Deployed"))
    script = ("const { chromium } = require('playwright');"
              "(async () => { const b = await chromium.launch(); const p = await b.newPage();"
              f"await p.goto('file:///{out_html.as_posix()}');"
              f"await p.pdf({{ path: '{(ROOT / 'slides.pdf').as_posix()}', width: '1280px', height: '720px', printBackground: true }});"
              "await b.close(); })();")
    subprocess.run(["node", "-e", script], cwd=pw_dir, check=True)
    print(f"-> {ROOT / 'slides.pdf'}")


if __name__ == "__main__":
    main()
