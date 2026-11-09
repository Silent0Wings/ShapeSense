import { get } from '../api.js';
import { badge, card, debounce, el, errorBox, fmt, note, pageHead, pixImg, stat, stats, table, tableView } from '../ui.js';
import { classPicker, select } from '../widgets/controls.js';
import { stackedBars } from '../svg/charts.js';
import { boot } from './boot.js';

const SOURCES = [
  { key: 'quickdraw', label: 'Quick, Draw!', color: 'var(--series-1)' },
  { key: 'kaggle_reevald', label: 'reevald', color: 'var(--series-2)' },
  { key: 'mendeley_elkorchi', label: 'El Korchi', color: 'var(--series-3)' },
  { key: 'github_handdrawn', label: 'Hand-Drawn', color: 'var(--series-4)' },
];

function byClass(stats_, names) {
  return names.map((name) => {
    const values = {}; let total = 0;
    stats_.filter((r) => r.label_name === name).forEach((r) => { values[r.source_id] = (values[r.source_id] || 0) + Number(r.n); total += Number(r.n); });
    return { label: name, values, total };
  });
}

const split = (rows, s) => rows.filter((r) => r.split === s).reduce((n, r) => n + Number(r.n), 0);

function browser(names, pool) {
  let splitName = 'train'; let seed = 1;
  const grid = el('div', { class: 'tiles' }); const summary = el('div', { class: 'compare' });
  const load = debounce(async () => {
    try {
      const label = picker.value();
      const [items, st] = await Promise.all([get(`/api/samples?label=${label}&split=${splitName}&n=12&seed=${seed}`),
        get(`/api/class-stats?label=${label}&split=${splitName}&seed=${seed}`)]);
      grid.replaceChildren(...items.items.map((it) => el('div', { class: 'tile' }, pixImg(it.image, { alt: 'Sample', size: 88 }), it.source)));
      summary.replaceChildren(
        el('div', { class: 'tile' }, pixImg(st.mean, { alt: 'Mean image', size: 120 }), `Mean of ${st.n}`),
        el('div', { class: 'tile' }, pixImg(st.spread, { alt: 'Spread image', size: 120 }), 'Spread (brighter = more varied)'));
    } catch (error) { grid.replaceChildren(errorBox(error)); }
  }, 60);
  const picker = classPicker(names, load);
  load();
  return card('Browse the real images', picker.root,
    el('div', { class: 'toolbar' },
      select(['train', 'val'], 'train', (v) => { splitName = v; load(); }, 'Split'),
      el('button', { type: 'button', class: 'ghost', text: 'Shuffle', onclick: () => { seed += 1; load(); } })),
    el('div', { class: 'grid side', style: 'margin:0' }, summary, grid),
    note(`Train and val only, chosen through the manifests. Images stored in the old test folder are skipped, leaving ${pool.train.kept.toLocaleString()} of ${pool.train.total_manifest.toLocaleString()} train images here. The test split cannot be opened from this page.`));
}

function duplicates(groups, names) {
  const view = el('div', { class: 'tiles' });
  const show = async (g) => {
    try {
      const r = await get(`/api/group?group=${encodeURIComponent(g.group)}`);
      view.replaceChildren(...r.images.map((b64) => pixImg(b64, { alt: 'Near-duplicate', size: 72 })));
    } catch (error) { view.replaceChildren(errorBox(error)); }
  };
  show(groups[0]);
  return card('Near-duplicate groups', el('div', { class: 'toolbar' }, groups.map((g) => el('button', { type: 'button', class: 'ghost',
    text: `${names[g.label]} · ${g.size}`, onclick: () => show(g) }))), view,
  note('Images within 2 bits of perceptual hash share a group, and a group is never split across train, validation and test. These are the largest groups in the browsable training pool.'));
}

function diamonds(d) {
  const rows = Object.entries(d.iteration.runs).map(([run, r]) => ({ run, macro: r.macro_f1, f1: r.diamond_f1,
    reevald: r.recall_by_source.kaggle_reevald.recall, qd: r.recall_by_source.quickdraw.recall }));
  let n = 0; const img = el('img', { class: 'sheet', src: '/img/contact0', alt: 'Quick, Draw! diamond review sheet' });
  const flip = (step) => { n = (n + step + d.contact_sheets) % d.contact_sheets; img.src = `/img/contact${n}`; };
  return card('CRISP-DM iteration 1: Quick, Draw! diamonds',
    el('p', { text: 'Most drawings labelled diamond were gems, cones or scribbles, not rhombi, so they were removed by rule before the split.' }),
    table(rows, [{ key: 'run', label: 'Run (first freeze, validation)' }, { label: 'macro-F1', num: true, render: (r) => fmt(r.macro, 1) },
      { label: 'Diamond F1', num: true, render: (r) => fmt(r.f1, 1) }, { label: 'Recall, reevald', num: true, render: (r) => fmt(r.reevald, 1) },
      { label: 'Recall, Quick Draw', num: true, render: (r) => fmt(r.qd, 1) }]),
    el('div', { class: 'toolbar' }, el('button', { type: 'button', class: 'ghost', text: 'Previous sheet', onclick: () => flip(-1) }),
      el('button', { type: 'button', class: 'ghost', text: 'Next sheet', onclick: () => flip(1) })), img);
}

boot('stage1', (main, d, meta) => {
  const names = meta.classes; const rows = byClass(d.split_stats, names);
  main.append(pageHead({ eyebrow: 'Stage 1 · CRISP-DM data understanding and preparation', title: 'Data freeze',
    lede: 'Four public sources become one frozen split with no near-duplicates crossing it, and a check for whether the source itself gives the answer away.' }));
  main.append(card('Frozen split', stats(stat('Train', split(d.split_stats, 'train').toLocaleString()),
    stat('Validation', split(d.split_stats, 'val').toLocaleString()), stat('Test', split(d.split_stats, 'test').toLocaleString(), 'counts only'))));
  main.append(card('Class distribution by source',
    stackedBars({ rows, series: SOURCES, label: 'Images per class by source', valueLabel: 'images' }),
    tableView(rows, [{ key: 'label', label: 'Class' }, ...SOURCES.map((s) => ({ label: s.label, num: true, render: (r) => r.values[s.key] || 0 })), { key: 'total', label: 'Total', num: true }])));
  main.append(browser(names, d.pool));
  main.append(el('div', { class: 'grid two' },
    card('Source shortcut check', stats(stat('Source classifier', `${fmt(d.source_check.pooled_accuracy * 100, 1)}%`), stat('Majority-source guess', `${fmt(d.source_check.pooled_majority_rate * 100, 1)}%`), stat('Gain', `${fmt(d.source_check.gain_points, 1)} pts`, `trigger: ${d.source_check.trigger_points}`)),
      el('div', { class: 'toolbar' }, d.source_check.shortcut_detected ? badge('warn', 'Shortcut detected') : badge('good', 'No shortcut')),
      note('If shape can be told from source, a model may learn the source. Firing this check makes the leave-one-source-out runs mandatory.')),
    card('Functional dependencies', table(Object.entries(d.fd).map(([rule, r]) => ({ rule, ...r })), [{ key: 'rule', label: 'Must hold' },
      { key: 'n_violations', label: 'Violations', num: true }, { label: 'Result', render: (r) => (r.holds ? badge('good', 'Holds') : badge('bad', 'Broken')) }]))));
  main.append(duplicates(d.duplicates, names));
  main.append(diamonds(d));
});
