// The network every arm shares, what each arm trains on, and the training loop.
import { ARM_NAMES } from '../plain.js';
import { hover, s, svgRoot, text } from '../svg/core.js';
import { stackedBars } from '../svg/charts.js';
import { el } from '../ui.js';

// One block per layer. Height follows the image size left at that point, and width the channels.
export function networkDiagram(layers) {
  const width = 860; const height = 230; const mid = 112; const col = width / layers.length;
  const parts = layers.map((layer) => {
    const dims = layer.shape.split(' x ').map(Number);
    return dims.length === 3 ? { h: 26 + 112 * (dims[2] / 64), w: 24 + 34 * (dims[0] / 128) } : { h: 22, w: 58 };
  });
  const root = svgRoot(width, height, 'The convolutional network shared by every model');
  layers.forEach((layer, i) => {
    const x = col * (i + .5); const { h, w } = parts[i];
    if (i < layers.length - 1) {
      const end = col * (i + 1.5) - parts[i + 1].w / 2 - 5;
      root.append(s('line', { class: 'axis-line', x1: x + w / 2 + 3, x2: end, y1: mid, y2: mid }),
        s('path', { d: `M${end},${mid - 4} L${end + 5},${mid} L${end},${mid + 4} z`, fill: 'var(--text-muted)' }));
    }
    root.append(s('rect', { x: x - w / 2, y: mid - h / 2, width: w, height: h, rx: 5, fill: i ? 'var(--series-1)' : 'var(--text-muted)' }));
    root.append(text(x, 20, layer.layer, { 'text-anchor': 'middle', style: 'font-size:12.5px;fill:var(--text-primary)' }));
    root.append(text(x, height - 16, layer.shape, { 'text-anchor': 'middle', style: 'font-variant-numeric:tabular-nums' }));
    const band = s('rect', { x: col * i, y: 0, width: col, height, fill: 'transparent' });
    hover(band, `${layer.layer}: ${layer.detail}. Output ${layer.shape}.`);
    root.append(band);
  });
  return root;
}

const BATCH_SERIES = [{ key: 'clean', label: 'Real, unchanged', color: 'var(--series-1)' },
  { key: 'augmented', label: 'Real, augmented', color: 'var(--series-2)' },
  { key: 'synthetic', label: 'Computer-generated, augmented', color: 'var(--series-3)' }];

// One bar per arm, and two for an arm that trains in two phases.
export function recipeBars(recipes, maxEpochs) {
  const rows = recipes.flatMap((r) => {
    const name = `${ARM_NAMES[r.arm] ?? r.arm} (${r.arm})`;
    const usual = { clean: r.clean, augmented: r.augmented, synthetic: r.synthetic };
    if (!r.pretrain_epochs) return [{ label: name, values: usual }];
    return [{ label: `${r.arm}, epochs 1 to ${r.pretrain_epochs}`, values: { synthetic: r.pretrain_synthetic } },
      { label: `${r.arm}, epochs ${r.pretrain_epochs + 1} to ${maxEpochs}`, values: usual }];
  });
  return stackedBars({ rows, series: BATCH_SERIES, label: 'What each model trained on, per batch', valueLabel: 'images per batch', left: 176 });
}

// The loop every arm ran, with its settings read from the stored config and run list.
export function trainingFlow(train, runs) {
  const main = runs.filter((r) => !r.holdout_source);
  const seeds = new Set(main.map((r) => r.seed)).size;
  const held = runs.filter((r) => r.holdout_source && r.arm === main[0]?.arm).length;
  const stopping = train.early_stopping_patience >= train.max_epochs ? 'no early stopping' : `early stopping after ${train.early_stopping_patience} epochs`;
  const steps = [
    ['Build a batch', `${train.batch_size} images, mixed as shown below`],
    ['Run the network', 'The same layers for every model'],
    ['Update the weights', `Cross-entropy loss, ${train.optimizer === 'adamw' ? 'AdamW' : train.optimizer} with a ${train.schedule} schedule`],
    ['Repeat', `${train.steps_per_epoch} steps per epoch, ${train.max_epochs} epochs, ${stopping}`],
    ['Keep the best epoch', 'The one with the highest validation macro-F1'],
    ['Repeat per seed', `${seeds} seeds per model, averaged for evaluation, plus ${held} runs that each hold out one source`],
  ];
  return el('ol', { class: 'arch-flow' }, steps.map(([title, body]) => el('li', {}, el('strong', { text: title }), el('span', { text: body }))));
}
