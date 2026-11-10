import { armName, finding, nameArms, verdictPicture } from '../plain.js';
import { badge, card, el, fmt, note, pageHead, signed, stat, stats, table } from '../ui.js';
import { scoreRows } from '../svg/charts.js';
import { ARM_SERIES, boot } from './boot.js';

const SERIES = ARM_SERIES.filter((s) => ['A0', 'A1', 'B'].includes(s.key));

boot('iteration1', (main, d) => {
  const m = d.metrics; const primary = { verdict: 'fail', label: m.primary.label, delta: m.delta, ci: m.ci };
  main.append(pageHead({ eyebrow: 'CRISP-DM iteration 1 · kept unchanged', title: 'Iteration 1 results',
    lede: 'The first experiment asked whether synthetic data beats augmentation alone. It failed, and that finding started iteration 2. These numbers come from frozen copies and never change.',
    chips: ['frozen record', 'augmentation rotated ±180°'] }));
  main.append(card('Iteration 1 verdict', el('div', { class: 'hero' },
    el('span', { class: 'big', text: signed(m.delta) }), badge('fail', 'Fail'),
    el('span', { text: `${nameArms(m.primary.label)}, macro-F1 points, 95% CI [${fmt(m.ci[0])}, ${fmt(m.ci[1])}]` })),
  el('p', { class: 'note', text: m.reasons.join('. ') }),
  el('p', { class: 'finding', text: finding(primary) }), verdictPicture(primary, d.criterion.macro_f1_min_gain_points),
  stats(...SERIES.map((s) => stat(`${s.label}`, fmt(m.ensembles[s.key].macro_f1, 1))), stat('Test reads', `${d.checks.test_reads} / ${d.checks.test_reads_expected}`))));
  const rows = d.per_class.map((r) => ({ label: r.class, values: Object.fromEntries(SERIES.map((s) => [s.key, Number(r[`f1_${s.key}`])])) }));
  const spread = (x) => Math.max(...Object.values(x.values)) - Math.min(...Object.values(x.values));
  rows.sort((a, b) => spread(b) - spread(a));
  main.append(card('F1 per class', scoreRows({ rows, series: SERIES, label: 'Iteration 1 per-class F1 by arm', domain: [75, 100] }),
    note('The classes separated by orientation or proportions lost the most. An investigation traced this to the ±180° rotation range.')));
  main.append(card('Comparisons', table(d.comparisons, [{ label: 'Comparison', render: (r) => nameArms(r.comparison) }, { key: 'role', label: 'Role' },
    { key: 'delta_macro_f1_points', label: 'Delta', num: true }, { key: 'ci', label: 'CI' }, { key: 'p_holm', label: 'p (Holm)', num: true }])));
  main.append(card('Confusion matrices', el('div', { class: 'tiles' }, SERIES.map((s) => el('img', { class: 'sheet', style: 'max-width:32%', src: `/img/iter1_confusion_${s.key}`, alt: `${armName(s.key)} confusion matrix` })))));
});
