import { get } from '../api.js';
import { badge, card, el, errorBox, fmt, note, pageHead, stat, stats, table, tableView } from '../ui.js';
import { lines, heatmap, dots } from '../svg/charts.js';
import { select, sliderRow } from '../widgets/controls.js';
import { ARM_SERIES, boot } from './boot.js';

function tuningCard(t) {
  const lrs = [...new Set(t.grid.map((g) => g.lr))]; const drops = [...new Set(t.grid.map((g) => g.dropout))];
  const lo = Math.min(...t.grid.map((g) => g.val_macro_f1)); const hi = Math.max(...t.grid.map((g) => g.val_macro_f1));
  const cells = t.grid.map((g) => ({ x: lrs.indexOf(g.lr), y: drops.indexOf(g.dropout), t: (g.val_macro_f1 - lo) / ((hi - lo) || 1), g }));
  return card('Iteration 1 tuning grid (A1 validation, seed 0)',
    el('div', { style: 'max-width:360px' }, heatmap({ cells, xLabels: lrs.map(String), yLabels: drops.map(String), label: 'Validation macro-F1 by learning rate and dropout', size: 68,
      cellText: (c) => fmt(c.g.val_macro_f1, 1), tip: (c) => `lr ${c.g.lr}, dropout ${c.g.dropout}: ${fmt(c.g.val_macro_f1, 2)} (best epoch ${c.g.best_epoch})`,
      marked: (c) => c.g.lr === t.winner.lr && c.g.dropout === t.winner.dropout, xTitle: 'learning rate', yTitle: 'dropout' })),
    note(`Winner (outlined): learning rate ${t.winner.lr}, dropout ${t.winner.dropout}. Iteration 1 tuned once on A1 and froze this for every arm; iteration 2 tuned each arm separately.`));
}

function runsCard(d) {
  const names = d.runs.map((r) => r.name);
  const host = el('div', {}); const tiles = el('div', {}); let current = null; let epoch = 1;
  const slider = sliderRow({ label: 'Epoch', min: 1, max: 30, step: 1, value: 1, onInput: () => { epoch = slider.get(); paint(); } });

  function paint() {
    if (!current) return;
    const { log } = current; const xs = log.map((r) => r.epoch);
    const point = log.find((r) => r.epoch === epoch) || log[log.length - 1];
    host.replaceChildren(el('div', { class: 'grid two', style: 'margin:0' },
      lines({ series: [{ label: 'train loss', color: 'var(--series-1)', values: log.map((r) => r.train_loss) }, { label: 'validation loss', color: 'var(--series-2)', values: log.map((r) => r.val_loss) }], xs, label: 'Loss per epoch', yLabel: 'loss', marker: point.epoch }),
      lines({ series: [{ label: 'validation macro-F1', color: 'var(--series-3)', values: log.map((r) => r.val_macro_f1) }], xs, label: 'Validation macro-F1 per epoch', yLabel: 'macro-F1', marker: point.epoch })));
    tiles.replaceChildren(stats(stat('Epoch', point.epoch), stat('Train loss', fmt(point.train_loss, 3)), stat('Validation loss', fmt(point.val_loss, 3)), stat('Validation macro-F1', fmt(point.val_macro_f1, 1)), stat('Learning rate', point.lr.toExponential(1))));
  }

  async function load(run) {
    try {
      current = await get(`/api/stage4/run/${encodeURIComponent(run)}`);
      const last = current.log.length;
      slider.root.querySelector('input').max = last;
      epoch = Math.min(current.info.best_epoch, last); slider.set(epoch);
      paint();
    } catch (error) { host.replaceChildren(errorBox(error)); }
  }
  load(names[0]);
  return card('Training curves', el('div', { class: 'toolbar' }, select(names, names[0], load, 'Run')), slider.root, tiles, host,
    note('The slider moves through the training log only. Only each run\'s best epoch was saved as a model, so predictions at other epochs do not exist.'));
}

function compareCard(d) {
  const rows = d.runs.filter((r) => !r.holdout_source).reduce((acc, r) => {
    (acc[r.seed] ??= { label: `seed ${r.seed}`, values: {} }).values[r.arm] = r.val_macro_f1; return acc;
  }, {});
  const all = Object.values(rows);
  return card('Validation macro-F1 by arm and seed',
    dots({ rows: all, series: ARM_SERIES, label: 'Validation macro-F1 by seed and arm', domain: [86, 98] }),
    tableView(d.runs, [{ key: 'name', label: 'Run' }, { label: 'Val macro-F1', num: true, render: (r) => fmt(r.val_macro_f1) }, { key: 'best_epoch', label: 'Best epoch', num: true }, { key: 'epochs_run', label: 'Epochs run', num: true }, { label: 'Held-out source', render: (r) => r.holdout_source || '–' }]),
    note('Selection used validation only. These are not test results.'));
}

boot('stage4', (main, d) => {
  main.append(pageHead({ eyebrow: 'Stage 4 · CRISP-DM modeling', title: 'Training',
    lede: 'One small CNN, the same step budget for every arm, five seeds per arm, plus runs that hold out a whole source. Settings were tuned on validation only.',
    chips: ['one GPU', 'same steps per arm', 'early stopping on validation'] }));
  const info = d.benchmark; const seeds = d.seed.per_arm;
  main.append(card('Run setup', stats(stat('Steps per epoch', d.train.steps_per_epoch), stat('Max epochs', d.train.max_epochs), stat('Batch size', d.train.batch_size),
    stat('Heaviest stream', `${Math.round(info.images_per_s).toLocaleString()} img/s`, 'arm B loader'), stat('Model parameters', info.n_params?.toLocaleString() ?? '–')),
  el('div', { class: 'toolbar' }, d.checks.no_test_reads ? badge('good', 'No test reads in this stage') : badge('bad', 'Test split was read'))));
  main.append(el('div', { class: 'grid two' },
    card('Architecture', table(d.layers, [{ key: 'layer', label: 'Layer' }, { key: 'detail', label: 'Detail' }, { key: 'shape', label: 'Output', num: true }])),
    tuningCard(d.tuning)));
  if (d.winners) {
    main.append(card('Search on validation (iteration 2)', table(Object.entries(d.winners.winners).map(([arm, w]) => ({ arm, mean: w.mean_val_macro_f1, seeds: w.val_macro_f1_by_seed.map((v) => fmt(v, 1)).join(', '), trials: d.winners.trials_per_arm[arm], lr: w.hparams.lr, dropout: w.hparams.dropout })),
      [{ key: 'arm', label: 'Arm' }, { label: 'Mean val macro-F1', num: true, render: (r) => fmt(r.mean, 2) }, { key: 'seeds', label: 'Seeds 0, 1, 2' }, { key: 'lr', label: 'Learning rate', num: true }, { key: 'dropout', label: 'Dropout', num: true }, { key: 'trials', label: 'Trials', num: true }]),
    note('Each arm got its own learning-rate and dropout tuning. A0 has no augmentation settings to search, so it had fewer trials.')));
  }
  main.append(compareCard(d));
  main.append(runsCard(d));
  main.append(el('div', { class: 'grid two' },
    card('Seed agreement', stats(...Object.entries(seeds).map(([arm, s]) => stat(`${arm}: seeds disagree`, `${fmt(s.mean_pairwise_disagreement * 100, 1)}%`))), note('Share of validation images where two seeds of the same arm predict different classes. A robustness number, not the power check.')),
    card('Baselines (validation)', stats(stat('Logistic regression on pixels', fmt(d.baselines.logreg_pixels.val_macro_f1, 1)), stat('Linear SVM on HOG', fmt(d.baselines.svm_hog.val_macro_f1, 1))), note('Reference points only. Macro-F1 in points.'))));
});
