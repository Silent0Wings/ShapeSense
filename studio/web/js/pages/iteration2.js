import { badge, card, el, fmt, note, pageHead, signed, stat, stats, table } from '../ui.js';
import { scoreRows } from '../svg/charts.js';
import { ARM_SERIES, boot } from './boot.js';

const SERIES = ARM_SERIES.filter((s) => ['A0', 'A1', 'B', 'A2'].includes(s.key));
const perClass = (rows) => rows.map((r) => ({ label: r.class, values: Object.fromEntries(SERIES.map((s) => [s.key, Number(r[`f1_${s.key}`])])) }));

boot('iteration2', (main, d) => {
  const m = d.metrics; const f = m.fresh_holdout;
  main.append(pageHead({ eyebrow: 'CRISP-DM iteration 2 · kept unchanged', title: 'Iteration 2 results',
    lede: 'The second experiment fixed the augmentation defects, tuned every arm on validation, added arm A2, and asked whether A2 beats real images alone. It failed on both evaluation sets. These numbers come from frozen copies and never change.',
    chips: ['frozen record', 'rotation ±20°, capped at ±10° for three classes'] }));
  main.append(card('Iteration 2 verdict', el('div', { class: 'hero' },
    el('span', { class: 'big', text: signed(m.delta) }), badge('fail', 'Fail'),
    el('span', { text: `${m.primary.label}, macro-F1 points, 95% CI [${fmt(m.ci[0])}, ${fmt(m.ci[1])}], reused test split` })),
  el('p', { class: 'note', text: m.reasons.join('. ') }),
  stats(...SERIES.map((s) => stat(`${s.key} ensemble`, fmt(m.ensembles[s.key].macro_f1, 1))), stat('Test reads', `${d.checks.test_reads} / ${d.checks.test_reads_expected}`))));
  main.append(card('Fresh holdout', el('div', { class: 'hero' },
    el('span', { class: 'big', text: signed(f.delta) }), badge('fail', 'Fail'),
    el('span', { text: `${f.label}, macro-F1 points, 95% CI [${fmt(f.ci[0])}, ${fmt(f.ci[1])}], ${f.n.toLocaleString()} images` })),
  stats(...SERIES.map((s) => stat(`${s.key} ensemble`, fmt(f.arms[s.key].macro_f1, 1)))),
  scoreRows({ rows: perClass(d.fresh_per_class), series: SERIES, label: 'Iteration 2 fresh holdout per-class F1', domain: [85, 100] })));
  main.append(card('F1 per class', scoreRows({ rows: perClass(d.per_class), series: SERIES, label: 'Iteration 2 per-class F1 by arm', domain: [85, 100] })));
  main.append(card('Comparisons', table(d.comparisons, [{ key: 'comparison', label: 'Comparison' }, { key: 'role', label: 'Role' },
    { key: 'delta_macro_f1_points', label: 'Delta', num: true }, { key: 'ci', label: 'CI' }, { key: 'p_holm', label: 'p (Holm)', num: true }])));
  main.append(card('Confusion matrices', el('div', { class: 'tiles' }, SERIES.map((s) => el('img', { class: 'sheet', style: 'max-width:24%', src: `/img/iter2_confusion_${s.key}`, alt: `${s.key} confusion matrix` })))));
  main.append(note('Reused test split: the same images were read in iteration 1, so its result is weaker evidence than the fresh holdout.'));
});
