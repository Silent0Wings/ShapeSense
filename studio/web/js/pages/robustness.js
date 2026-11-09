import { card, el, fmt, note, pageHead, table, tableView } from '../ui.js';
import { heatmap, lines, scoreRows } from '../svg/charts.js';
import { classPicker, select } from '../widgets/controls.js';
import { ARM_SERIES, boot } from './boot.js';

const ARMS = ARM_SERIES.map((s) => s.key);
const FAMILIES = [['rotated', 'Rotation'], ['gaussian', 'Gaussian noise'], ['salt_pepper', 'Salt-and-pepper noise'], ['blur', 'Gaussian blur'],
  ['jpeg', 'JPEG compression'], ['brightness', 'Brightness shift'], ['contrast', 'Contrast shift'], ['occlusion', 'Occlusion patch']];
const pm = (x) => `${fmt(x.mean, 1)} ± ${fmt(x.std, 1)}`;

function familyChart(r, family, title) {
  const levels = r.sets.filter((s) => s.family === family);
  const sets = family === 'rotated' ? levels : [r.sets[0], ...levels];
  const series = ARM_SERIES.map((a) => ({ ...a, values: sets.map((s) => r.by_arm[a.key][s.name].accuracy.mean) }));
  return el('div', {}, el('h3', { text: title }),
    lines({ series, xs: sets.map((_, i) => i), xLabels: sets.map((s) => s.level), xTitle: 'severity', label: `${title}: accuracy by severity`, yLabel: 'accuracy %' }));
}

function rotationDetail(r) {
  const angles = r.sets.filter((s) => s.family === 'rotated' && s.name !== 'rot0');
  let name = 'rot45'; let arm = 'A2';
  const bars = el('div', {}); const matrix = el('div', { style: 'max-width:520px' });
  function paint() {
    bars.replaceChildren(scoreRows({ rows: r.classes.map((label, i) => ({ label, values: Object.fromEntries(ARMS.map((a) => [a, r.per_class[a][name][i]])) })), series: ARM_SERIES, label: `Accuracy per class at ${name}`, domain: [0, 100] }));
    const counts = r.confusion_summed_over_seeds[arm][name];
    const cells = counts.flatMap((row, y) => { const total = row.reduce((a, b) => a + b, 0) || 1; return row.map((n, x) => ({ x, y, n, t: n / total })); });
    matrix.replaceChildren(heatmap({ cells, xLabels: r.classes, yLabels: r.classes, size: 42, label: `Confusion matrix for ${arm} at ${name}`, cellText: (c) => (c.n ? String(c.n) : ''), tip: (c) => `${r.classes[c.y]} read as ${r.classes[c.x]}: ${c.n} (all ${r.training_seeds.length} seeds)`, xTitle: 'predicted', yTitle: 'true class' }));
  }
  const picker = select(angles.map((s) => s.name), name, (v) => { name = v; paint(); }, 'Rotation');
  const armPick = classPicker(ARMS, (i) => { arm = ARMS[i]; paint(); }, ARMS.indexOf(arm));
  paint();
  return card('Per class under rotation', el('div', { class: 'toolbar' }, picker), bars,
    note('A circle looks the same at any angle and a square repeats every 90°, so those classes are not a fair test of rotation. Read the classes that have a direction, like triangle, pentagon and star.'),
    armPick.root, matrix);
}

boot('robustness', (main, d) => {
  main.append(pageHead({ eyebrow: 'CRISP-DM evaluation · extra check', title: 'Robustness check',
    lede: 'The same validation images twice: the current clean set, and a new set with rotation, noise, blur, compression, lighting shifts and occlusion added. Every model scores identical saved images.',
    chips: ['validation only', 'made after iteration 2 closed', 'changes no verdict'] }));
  const r = d.results;
  if (!r) { main.append(card('Results', note('Run python -m robustness.run first.'))); return; }
  main.append(card('The two validation sets', el('img', { class: 'sheet', src: '/img/robustness_examples', alt: 'One square and one star under every perturbation' }),
    note(`${r.n_images.toLocaleString()} images, perturbed once with seed ${r.seed} and saved to disk. Each column is one perturbation. The test split and the fresh holdout stay sealed, so these are not test results. Validation also guided tuning, so clean scores run slightly high.`)));
  main.append(card('Current against new validation', table(ARMS.map((arm) => ({ arm, ...r.families[arm] })), [{ key: 'arm', label: 'Arm' },
    { label: 'Clean accuracy %', num: true, render: (x) => pm(x.clean) }, { label: 'Rotated drop', num: true, render: (x) => pm(x.rotated_drop) }, { label: 'Noisy drop', num: true, render: (x) => pm(x.noisy_drop) }]),
  note(`Drop is clean accuracy minus perturbed accuracy, in points, averaged over a family's levels. Lower is better. Mean ± std over ${r.training_seeds.length} training seeds.`)));
  main.append(card('Accuracy by severity', el('div', { class: 'grid two', style: 'margin:0' }, FAMILIES.map(([family, title]) => familyChart(r, family, title)))));
  main.append(card('Drop by perturbation family', table(ARMS.map((arm) => ({ arm, ...r.families[arm] })), [{ key: 'arm', label: 'Arm' },
    ...FAMILIES.slice(1).map(([family, title]) => ({ label: title, num: true, render: (x) => pm(x[`${family}_drop`]) }))])));
  main.append(rotationDetail(r));
  main.append(card('Every level', tableView(r.sets, [{ key: 'name', label: 'Set' }, { key: 'level', label: 'Level' },
    ...ARMS.map((arm) => ({ label: `${arm} accuracy`, num: true, render: (s) => pm(r.by_arm[arm][s.name].accuracy) }))], 'Show every level as a table')));
});
