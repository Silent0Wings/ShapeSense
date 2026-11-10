import { card, el, fmt, note, pageHead, table, tableView } from '../ui.js';
import { armName } from '../plain.js';
import { heatmap, lines, scoreRows } from '../svg/charts.js';
import { classPicker, select } from '../widgets/controls.js';
import { ARM_SERIES, boot } from './boot.js';

const FAMILIES = [['rotated', 'Rotation'], ['gaussian', 'Gaussian noise'], ['salt_pepper', 'Salt-and-pepper noise'], ['blur', 'Gaussian blur'],
  ['jpeg', 'JPEG compression'], ['brightness', 'Brightness shift'], ['contrast', 'Contrast shift'], ['occlusion', 'Occlusion patch']];
const pm = (x) => `${fmt(x.mean, 1)} ± ${fmt(x.std, 1)}`;

function familyChart(r, series, family, title) {
  const levels = r.sets.filter((s) => s.family === family);
  if (!levels.length) return null;
  const sets = family === 'rotated' ? levels : [r.sets[0], ...levels];
  const data = series.map((a) => ({ ...a, values: sets.map((s) => r.by_arm[a.key][s.name].accuracy.mean) }));
  return el('div', {}, el('h3', { text: title }),
    lines({ series: data, xs: sets.map((_, i) => i), xLabels: sets.map((s) => s.level), xTitle: 'severity', label: `${title}: accuracy by severity`, yLabel: 'accuracy %' }));
}

function rotationDetail(r, series) {
  const arms = series.map((s) => s.key);
  const angles = r.sets.filter((s) => s.family === 'rotated' && s.name !== 'rot0');
  let name = 'rot45'; let arm = arms.includes('A2') ? 'A2' : arms[0];
  const bars = el('div', {}); const matrix = el('div', { style: 'max-width:520px' });
  function paint() {
    bars.replaceChildren(scoreRows({ rows: r.classes.map((label, i) => ({ label, values: Object.fromEntries(arms.map((a) => [a, r.per_class[a][name][i]])) })), series, label: `Accuracy per class at ${name}`, domain: [0, 100] }));
    const counts = r.confusion_summed_over_seeds[arm][name];
    const cells = counts.flatMap((row, y) => { const total = row.reduce((a, b) => a + b, 0) || 1; return row.map((n, x) => ({ x, y, n, t: n / total })); });
    matrix.replaceChildren(heatmap({ cells, xLabels: r.classes, yLabels: r.classes, size: 42, label: `Confusion matrix for ${armName(arm)} at ${name}`, cellText: (c) => (c.n ? String(c.n) : ''), tip: (c) => `${r.classes[c.y]} read as ${r.classes[c.x]}: ${c.n} (all ${r.training_seeds.length} seeds)`, xTitle: 'predicted', yTitle: 'true class' }));
  }
  const picker = select(angles.map((s) => s.name), name, (v) => { name = v; paint(); }, 'Rotation');
  const armPick = classPicker(arms, (i) => { arm = arms[i]; paint(); }, arms.indexOf(arm));
  paint();
  return card('Per class under rotation', el('div', { class: 'toolbar' }, picker), bars,
    note('A circle looks the same at any angle and a square repeats every 90°, so those classes are not a fair test of rotation. Read the classes that have a direction, like triangle, pentagon and star.'),
    armPick.root, matrix);
}

function section(main, r, intro) {
  const series = ARM_SERIES.filter((a) => r.by_arm[a.key]);
  const rows = series.map((a) => ({ name: a.label, ...r.families[a.key] }));
  main.append(card(intro.title, ...intro.body, table(rows, [{ key: 'name', label: 'Arm' },
    { label: 'Clean accuracy %', num: true, render: (x) => pm(x.clean) }, { label: 'Rotated drop', num: true, render: (x) => pm(x.rotated_drop) }, { label: 'Noisy drop', num: true, render: (x) => pm(x.noisy_drop) }]),
  note(`Drop is clean accuracy minus perturbed accuracy, in points, averaged over a family's levels. Lower is better. Mean ± std over ${r.training_seeds.length} training seeds.`)));
  main.append(card('Accuracy by severity', el('div', { class: 'grid two', style: 'margin:0' }, FAMILIES.map(([family, title]) => familyChart(r, series, family, title)))));
  main.append(card('Drop by perturbation family', table(rows, [{ key: 'name', label: 'Arm' },
    ...FAMILIES.slice(1).map(([family, title]) => ({ label: title, num: true, render: (x) => pm(x[`${family}_drop`]) }))])));
  main.append(rotationDetail(r, series));
  main.append(card('Every level', tableView(r.sets, [{ key: 'name', label: 'Set' }, { key: 'level', label: 'Level' },
    ...series.map((a) => ({ label: `${a.label} accuracy`, num: true, render: (s) => pm(r.by_arm[a.key][s.name].accuracy) }))], 'Show every level as a table')));
}

boot('robustness', (main, d) => {
  main.append(pageHead({ eyebrow: 'CRISP-DM evaluation', title: 'Robustness check',
    lede: 'The same images twice: clean, and with rotation, noise, blur, compression, lighting shifts and occlusion added. Every model scores identical saved images.',
    chips: ['sealed holdout read once', 'validation check kept for comparison'] }));
  if (d.sealed) {
    section(main, d.sealed, { title: 'Sealed holdout 2: clean against damaged', body: [
      note(`${d.sealed.n_images.toLocaleString()} images that were never read before, perturbed once inside Stage 5 and saved. This is the data behind the pre-registered iteration 3 verdict.`)] });
    main.append(el('h2', { text: 'Validation check, for comparison' }));
  }
  const r = d.results;
  if (!r) { main.append(card('Results', note('Run python -m robustness.run first.'))); return; }
  section(main, r, { title: 'Validation: clean against damaged', body: [el('img', { class: 'sheet', src: '/img/robustness_examples', alt: 'One square and one star under every perturbation' }),
    note(`${r.n_images.toLocaleString()} validation images, perturbed once with seed ${r.seed} and saved to disk. Each column is one perturbation. Validation also guided tuning, so clean scores run slightly high. It suggested the question and changes no verdict.`)] });
});
