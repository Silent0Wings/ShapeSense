import { card, el, fmt, note, pageHead, signed, table, tableView } from '../ui.js';
import { lines, valueBars } from '../svg/charts.js';
import { select } from '../widgets/controls.js';
import { ARM_SERIES, boot } from './boot.js';

const SERIES = ARM_SERIES;
const BUDGETS = [['e60', '60 epochs'], ['e30_nostop', '30 epochs, no early stop'], ['e60_nostop', '60 epochs, no early stop']];
const TRANSFORMS = [['all_on', 'All transforms'], ['rotation', 'Rotation only'], ['scale', 'Scale only'], ['noise', 'Noise only'], ['blur', 'Blur only'], ['reframe_only', 'Re-frame only']];
const pm = (x) => `${fmt(x.mean, 1)} ± ${fmt(x.std, 1)}`;
const pct = (x) => `${fmt(x * 100, 1)}%`;
const section = (title, doc, build) => card(title, ...(doc ? build(doc) : [note('This experiment has not finished yet.')]));
const scoreColumns = [{ label: 'Clean macro-F1', num: true, render: (r) => pm(r.clean) }, { label: 'Damaged macro-F1', num: true, render: (r) => pm(r.perturbed) }];

function scarcity(d) {
  const arms = SERIES.filter((s) => d.arms.includes(s.key));
  const chart = (score, title) => el('div', {}, el('h3', { text: title }), lines({
    series: arms.map((s) => ({ ...s, values: d.fractions.map((f) => d.scores[`${s.key}/${f}`][score].mean) })),
    xs: d.fractions.map((_, i) => i), xLabels: d.fractions.map((f) => `${f}%`), xTitle: 'share of real training images', label: `${title} by share of real images`, yLabel: 'macro-F1' }));
  const rows = arms.flatMap((s) => d.fractions.map((f) => ({ arm: s.key, share: `${f}%`, ...d.scores[`${s.key}/${f}`] })));
  return [el('div', { class: 'grid two', style: 'margin:0' }, chart('clean', 'Clean validation'), chart('perturbed', 'Damaged validation')),
    tableView(rows, [{ key: 'arm', label: 'Arm' }, { key: 'share', label: 'Real images' }, ...scoreColumns], 'Show every arm and share as a table')];
}

function paired(d, pairs) {
  const rows = pairs.flatMap(([key, label]) => (d.scores[key] ? [{ label, ...d.scores[key] }] : []));
  return table(rows, [{ key: 'label', label: 'Condition' }, ...scoreColumns]);
}

function budget(d) {
  const arms = Object.keys(d.gains_over_e30[BUDGETS[0][0]]);
  const rows = arms.map((arm) => ({ arm, ...Object.fromEntries(BUDGETS.map(([name]) => [name, d.gains_over_e30[name][arm]])) }));
  return [table(rows, [{ key: 'arm', label: 'Arm' }, ...BUDGETS.map(([name, label]) => ({ label, num: true, render: (r) => signed(r[name]) }))]),
    note(d.adopted ? `Adopted for every arm: ${BUDGETS.find(([name]) => name === d.adopted)[1]}.` : 'No option cleared the rule, so the 30-epoch budget stays for every arm.'),
    note(`Gain in clean validation macro-F1 over 30 epochs with early stopping. An option is adopted only if every tested arm gains at least ${d.rule_points} points.`)];
}

function histograms(d) {
  const sets = [['real', 'Real', 'var(--series-1)'], ['reframed', 'Re-framed', 'var(--series-2)'], ['augmented', 'Augmented', 'var(--series-3)']];
  const shapes = Object.keys(d.profiles.real);
  let shape = 'rectangle';
  const host = el('div', { class: 'grid two', style: 'margin:0' });
  const chart = (key, title, xTitle) => {
    const edges = d.hist_edges[key];
    const series = sets.map(([set, label, color]) => {
      const counts = d.profiles[set][shape][key].hist;
      const total = counts.reduce((a, b) => a + b, 0) || 1;
      return { label, color, values: counts.map((n) => (100 * n) / total) };
    });
    return el('div', {}, el('h3', { text: title }), lines({ series, xs: edges.slice(0, -1).map((e, i) => (e + edges[i + 1]) / 2), xTitle, label: `${title} for ${shape}`, yLabel: '% of images' }));
  };
  const paint = () => host.replaceChildren(chart('aspect_ratio', 'Long side over short side', 'ratio'), chart('stroke_px', 'Stroke width', 'pixels'));
  paint();
  return [el('div', { class: 'toolbar' }, select(shapes, shape, (v) => { shape = v; paint(); }, 'Shape')), host];
}

function preprocess(d) {
  const arms = SERIES.filter((s) => d.scores[s.key]).map((s) => ({ arm: s.key, ...d.scores[s.key] }));
  const shapes = Object.keys(d.profiles.real);
  const measure = (key, digits) => shapes.map((shape) => ({ shape, ...Object.fromEntries(Object.keys(d.profiles).map((set) => [set, d.profiles[set][shape][key]])) }))
    .map((r) => ({ shape: r.shape, real: fmt(r.real.mean, digits), reframed: fmt(r.reframed.mean, digits), augmented: fmt(r.augmented.mean, digits) }));
  const columns = [{ key: 'shape', label: 'Shape' }, { key: 'real', label: 'Real', num: true }, { key: 'reframed', label: 'Re-framed', num: true }, { key: 'augmented', label: 'Augmented', num: true }];
  return [table(arms, [{ key: 'arm', label: 'Arm' }, { label: 'Unchanged images', num: true, render: (r) => pm(r.raw) }, { label: 'Re-framed and binarised', num: true, render: (r) => pm(r.reframed_only) }]),
    note('Macro-F1 on the same validation images, unchanged and after only the re-frame and binarise step.'),
    el('div', { class: 'grid two', style: 'margin:0' }, el('div', {}, el('h3', { text: 'Long side over short side' }), table(measure('aspect_ratio', 2), columns)),
      el('div', {}, el('h3', { text: 'Stroke width (px)' }), table(measure('stroke_px', 2), columns))),
    ...histograms(d)];
}

function oneOn(d) {
  const known = TRANSFORMS.filter(([key]) => d.scores[key]);
  const rows = known.map(([key, label]) => ({ label, value: Number(fmt(d.scores[key].clean.mean, 1)), mark: key === 'all_on' }));
  const values = rows.map((r) => r.value);
  return [valueBars({ rows, label: 'Clean validation macro-F1 with one transform on', domain: [Math.floor(Math.min(...values)) - 1, Math.ceil(Math.max(...values)) + 1] }),
    tableView(known.map(([key, label]) => ({ label, ...d.scores[key] })), [{ key: 'label', label: 'Condition' }, ...scoreColumns])];
}

function shares(title, block) {
  const rows = Object.entries(block.rows).map(([name, r]) => ({ name, ...r }));
  return el('div', {}, el('h3', { text: title }), table(rows, [{ key: 'name', label: title }, { label: 'Validation', num: true, render: (r) => pct(r.val_share) }, { label: 'Test', num: true, render: (r) => pct(r.test_share) }]),
    note(`Total difference between the two: ${pct(block.total_variation)}.`));
}

boot('experiments', (main, d) => {
  main.append(pageHead({ eyebrow: 'CRISP-DM iteration 3 · modeling', title: 'Iteration 3 experiments',
    lede: 'Controlled tests that answer specific questions before the final retraining. Each one trains or scores on validation images only, so none of these numbers is a test result. Validation also guided tuning, so scores run slightly high.',
    chips: ['validation only', 'three seeds unless stated', 'mean ± std'] }));
  main.append(section('Scarcity: fewer real images', d.scarcity, scarcity),
    section('Equal real images per step', d.equal_real, (x) => [paired(x, [['B/normal', 'B'], ['B/equal_real', 'B, equal real'], ['A2/normal', 'A2'], ['A2/equal_real', 'A2, equal real']]),
      note('Equal real keeps the same number of real images per step in every arm, with synthetic images added on top.')]),
    section('BatchNorm recalibration', d.batchnorm, (x) => [paired(x, [['B/saved', 'B, as trained'], ['B/recalibrated', 'B, recalibrated on real images'], ['A2/saved', 'A2, as trained'], ['A2/recalibrated', 'A2, recalibrated on real images']])]),
    section('Training length', d.budget, budget),
    section('Re-frame and binarise alone', d.preprocess, preprocess),
    section('One transform on', d.one_transform_on, oneOn),
    section('Validation against test balance', d.val_vs_test, (x) => [el('div', { class: 'grid two', style: 'margin:0' }, shares('Class', x.class), shares('Source', x.source)),
      note('Computed from aggregate counts only. No test image or prediction was opened.')]));
});
