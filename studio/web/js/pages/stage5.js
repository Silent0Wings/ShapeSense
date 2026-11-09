import { get } from '../api.js';
import { badge, card, el, errorBox, fmt, note, pageHead, pixImg, signed, stat, stats, table, tableView } from '../ui.js';
import { ciChart, dots, heatmap } from '../svg/charts.js';
import { classPicker } from '../widgets/controls.js';
import { ARM_SERIES, boot } from './boot.js';

function confusionCard(names, pairs) {
  const host = el('div', { style: 'max-width:640px' }); const detail = el('div', {});
  let arm = 'B';

  async function showErrors(cell) {
    const [t, p] = [cell.y, cell.x];
    const title = el('h3', { text: `True ${names[t]}, predicted ${names[p]}: ${cell.count.toLocaleString()} images` });
    if (t === p) { detail.replaceChildren(title, note('These are correct predictions.')); return; }
    if (arm !== 'B') { detail.replaceChildren(title, note('Stage 5 stored error images for the B ensemble only. Switch to arm B to see them.')); return; }
    try {
      const out = await get(`/api/stage5/errors?true=${t}&pred=${p}`);
      if (!out.available) { detail.replaceChildren(title, note('No images are shown for this cell. Only the three confusable pairs Stage 5 published are displayable.')); return; }
      detail.replaceChildren(title, el('div', { class: 'tiles' }, out.images.map((b64) => pixImg(b64, { alt: 'Misclassified test image', size: 72 }))),
        out.total > out.images.length ? note(`Showing ${out.images.length} of ${out.total}.`) : null);
    } catch (error) { detail.replaceChildren(errorBox(error)); }
  }

  async function load(next) {
    arm = next;
    try {
      const { matrix } = await get(`/api/stage5/confusion/${next}`);
      const cells = matrix.flatMap((row, y) => row.map((count, x) => {
        const total = row.reduce((a, b) => a + b, 0);
        return { x, y, count, share: total ? count / total : 0, t: Math.sqrt(total ? count / total : 0) };
      }));
      host.replaceChildren(heatmap({ cells, xLabels: names, yLabels: names, label: `Confusion matrix, arm ${next}`, size: 50, xTitle: 'predicted class', yTitle: 'true class',
        cellText: (c) => (c.count ? c.count : ''), tip: (c) => `True ${names[c.y]}, predicted ${names[c.x]}: ${c.count} (${(c.share * 100).toFixed(1)}%)`, onClick: showErrors }));
      detail.replaceChildren(note('Select a cell to see what it holds.'));
    } catch (error) { host.replaceChildren(errorBox(error)); }
  }
  load(arm);
  const pick = classPicker(['A0', 'A1', 'B'], (i) => load(['A0', 'A1', 'B'][i]), 2);
  return card('Confusion matrices (soft-vote ensembles)', pick.root, el('div', { style: 'height:10px' }), host, detail,
    note(`Stronger colour means a larger share of that true class (square-root scale). Error images: ${pairs.map((p) => p.join(' / ')).join(', ')}.`));
}

function perClass(rows) {
  const data = rows.map((r) => ({ label: r.class, values: { A0: Number(r.f1_A0), A1: Number(r.f1_A1), B: Number(r.f1_B) }, n: r.n_test, flag: r.flag || '–' }));
  const lo = Math.min(...data.flatMap((d) => Object.values(d.values)));
  return card('F1 per class', dots({ rows: data, series: ARM_SERIES, label: 'Per-class F1 by arm', domain: [Math.floor(lo / 5) * 5, 100] }),
    tableView(data, [{ key: 'label', label: 'Class' }, { key: 'n', label: 'Test images', num: true }, ...ARM_SERIES.map((s) => ({ label: s.label, num: true, render: (r) => fmt(r.values[s.key], 1) })), { key: 'flag', label: 'Guardrail' }]),
    note('An asterisk marks a single-source class. The axis starts above zero to separate the dots.'));
}

boot('stage5', (main, d, meta) => {
  main.append(pageHead({ eyebrow: 'Stage 5 · CRISP-DM evaluation', title: 'Evaluation',
    lede: 'Each model read the sealed test split exactly once. Everything on this page comes from what Stage 5 saved, so this page never reads the split again.' }));
  if (!d.verdict) { main.append(card('Verdict', note('Stage 5 has not run yet.'))); return; }
  const m = d.metrics; const v = d.verdict;
  main.append(card('Verdict', el('div', { class: 'hero' },
    el('span', { class: 'big', text: signed(v.delta) }),
    v.verdict === 'pass' ? badge('pass', 'Pass') : badge('fail', 'Fail'),
    el('span', { text: `B vs A1, macro-F1 points, 95% CI [${fmt(v.ci[0])}, ${fmt(v.ci[1])}]` })),
  el('p', { class: 'note', text: v.reasons.join('. ') }),
  stats(stat('A0 ensemble', fmt(m.ensembles.A0.macro_f1, 1)), stat('A1 ensemble', fmt(m.ensembles.A1.macro_f1, 1)), stat('B ensemble', fmt(m.ensembles.B.macro_f1, 1)),
    stat('Test reads', `${d.checks.test_reads} / ${d.checks.test_reads_expected}`, `extra: ${d.checks.extra_reads}`), stat('Expected half-width', fmt(d.power.expected_test_half_width), `limit ${d.power.limit_points}`))));
  main.append(card('Differences with confidence intervals',
    ciChart({ label: 'Macro-F1 differences with 95% confidence intervals', required: d.criterion.macro_f1_min_gain_points, rows: [
      { label: 'B vs A1', delta: v.delta, ci: v.ci },
      { label: 'A1 vs A0', delta: m.secondary['A1 vs A0'].delta, ci: m.secondary['A1 vs A0'].ci },
      { label: 'B vs A0', delta: m.secondary['B vs A0'].delta, ci: m.secondary['B vs A0'].ci } ] }),
    note('Only B vs A1 is the primary test. A0 used no augmentation and scored higher on this same-source test; the source shortcut check fired, so treat that gap with care.')));
  main.append(confusionCard(meta.classes, d.pairs));
  main.append(perClass(d.per_class));
  main.append(el('div', { class: 'grid two' },
    card('Unseen-source check (9-class)', table(m.loso, [{ key: 'arm', label: 'Arm' }, { key: 'n', label: 'Images', num: true }, { label: 'Macro-F1', num: true, render: (r) => fmt(r.macro_f1, 1) }, { label: 'Accuracy', num: true, render: (r) => `${fmt(r.accuracy * 100, 1)}%` }]),
      note('Trained without Hand-Drawn, scored on Hand-Drawn triangles and rectangles only. Hand-Drawn is the only source of ellipses, so this says nothing about ellipses.')),
    card('Accuracy per source and domain', table(d.per_source.filter((r) => r.kind !== 'held-out source'), [{ key: 'group', label: 'Group' }, { key: 'arm', label: 'Arm' }, { key: 'n', label: 'Images', num: true }, { key: 'accuracy_pct', label: 'Accuracy %', num: true }]))));
  main.append(el('div', { class: 'grid two' },
    card('Power check', stats(stat('Validation half-width', fmt(d.power.half_width_val)), stat('Underpowered?', d.power.underpowered ? 'Yes' : 'No'), stat('Reads before the check', d.power.access_log_reads_at_power_check)), note('Run on validation before the first test read.')),
    card('Test-access log', stats(stat('Lines', d.access.total), stat('Callers', Object.keys(d.access.callers).length)), note(Object.keys(d.access.callers).join(', ')))));
});
