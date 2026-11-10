// The network every arm shares, what each arm trains on, and the training loop.
import { ARM_NAMES } from '../plain.js';
import { hover, s, svgRoot, text } from '../svg/core.js';
import { stackedBars } from '../svg/charts.js';
import { el, stat, stats } from '../ui.js';

const shapeText = (dims) => (dims ? dims.join(' × ') : '–');

const OP_TEXT = {
  input: (op) => `The drawing, as ${op.output[1]} by ${op.output[2]} pixels with one channel. Background is 1 and ink is 0.`,
  conv: (op) => `Slides ${op.output[0]} small 3×3 filters across the image. Each learns to respond to a pattern, such as an edge or a corner. Padding keeps the width and height unchanged.`,
  batchnorm: () => 'Rescales each channel using the mean and spread of the batch, which keeps training stable. It stores two learned numbers per channel.',
  relu: () => 'Sets every negative value to zero and leaves the rest alone. Without this step, stacked filters could only do what one filter does.',
  maxpool: () => 'Keeps the largest value in each 2×2 patch, halving width and height. Small shifts in the drawing matter less afterwards, and later filters see a wider area.',
  globalpool: (op) => `Averages each of the ${op.output[0]} channels across all positions, leaving one number per channel. This keeps how strongly a pattern appeared and drops where it was.`,
  dropout: (op, dropout) => `During training only, randomly zeroes ${dropout === null ? 'a tuned share' : `${Math.round(dropout * 100)}%`} of these ${op.output[0]} numbers, so the model cannot lean on a few of them. It does nothing when predicting.`,
  linear: (op) => `Combines the ${op.input[0]} numbers into ${op.output[0]} scores, one per shape. The largest score is the answer, and softmax turns the scores into probabilities.`,
};

const edge = [[0, 0, 0, 9, 9], [0, 0, 0, 9, 9], [0, 0, 0, 9, 9], [0, 0, 9, 9, 9], [0, 0, 9, 9, 9]];
const patch4 = [[1, 3, 0, 2], [4, 2, 1, 1], [0, 1, 8, 3], [2, 0, 5, 6]];
const range = (n) => Array.from({ length: n }, (_, i) => i);
const windowCells = (size, row, col, h, w) => range(h).flatMap((r) => range(w).map((c) => (row + r) * size + col + c));

const DEMOS = {
  conv: { input: edge, title: 'Try it: a filter that finds vertical edges',
    output: range(3).map((r) => range(3).map((c) => range(3).reduce((sum, i) => sum + edge[r + i][c + 2] - edge[r + i][c], 0))),
    windowOf: (k) => windowCells(5, Math.floor(k / 3), k % 3, 3, 3), caption: 'This filter adds the right column of each 3×3 window and subtracts the left, so the largest outputs sit on the edge. The model learns its own filters.' },
  maxpool: { input: patch4, title: 'Try it: max pooling',
    output: range(2).map((r) => range(2).map((c) => Math.max(...windowCells(4, 2 * r, 2 * c, 2, 2).map((i) => patch4.flat()[i])))),
    windowOf: (k) => windowCells(4, 2 * Math.floor(k / 2), 2 * (k % 2), 2, 2), caption: 'Each output keeps the largest value in its 2×2 patch.' },
  globalpool: { input: patch4, title: 'Try it: global average pooling',
    output: [[(patch4.flat().reduce((a, b) => a + b, 0) / 16).toFixed(1)]],
    windowOf: () => range(16), caption: 'The whole channel becomes one number, its average.' },
};

function windowDemo({ input, output, windowOf, title, caption }) {
  const grid = (cells, n) => el('div', { class: 'demo-grid', style: `grid-template-columns:repeat(${n},32px)` }, cells);
  const inputs = input.flat().map((v) => el('span', { class: 'demo-cell', text: v }));
  const pick = (k) => {
    const lit = windowOf(k);
    inputs.forEach((cell, i) => cell.classList.toggle('on', lit.includes(i)));
    outputs.forEach((cell, i) => cell.classList.toggle('on', i === k));
  };
  const outputs = output.flat().map((v, k) => el('button', { type: 'button', class: 'demo-cell out', text: v, 'aria-label': `Output ${v}`, onmouseenter: () => pick(k), onfocus: () => pick(k), onclick: () => pick(k) }));
  pick(0);
  return el('div', { class: 'demo' }, el('h4', { text: title }),
    el('div', { class: 'demo-row' }, grid(inputs, input[0].length), el('span', { class: 'demo-arrow', text: '→' }), grid(outputs, output[0].length)),
    el('p', { class: 'note', text: `${caption} Hover an output to see where it came from. Example numbers.` }));
}

// A block draws one slab per operation, front to back, so the selected one can be picked out.
function slabs(root, dims, x, mid, layers) {
  const spatial = dims.length === 3 ? dims[2] : 1;
  const count = layers > 1 ? layers : Math.min(7, Math.max(1, Math.round(Math.log2(dims[0] + 1))));
  const shift = layers > 1 ? 9 : 4;
  const rects = [];
  const h = dims.length === 3 ? 14 + 92 * (spatial / 64) : Math.min(100, 8 + dims[0] * 0.7);
  const w = dims.length === 3 ? 10 + 42 * (spatial / 64) : 12;
  for (let i = count - 1; i >= 0; i -= 1) {
    rects[i] = s('rect', { x: x - w / 2 + i * shift - count * shift / 2, y: mid - h / 2 - i * shift + count * shift / 2, width: w, height: h, rx: 2, stroke: 'var(--surface-1)', opacity: 1 - i * .09 });
    root.append(rects[i]);
  }
  return rects;
}

// The real model, one clickable operation at a time, with a worked example for the pools.
export function networkExplorer(ops, dropout) {
  const groups = [...new Set(ops.map((op) => op.group))];
  const width = 1090; const col = width / groups.length; const mid = 98; const chipY = 188; const chipH = 27;
  const height = chipY + 4 * (chipH + 5) + 6;
  const total = ops.reduce((sum, op) => sum + op.params, 0);
  const root = svgRoot(width, height, 'Every operation of the network. Select one to read about it.');
  root.style.minWidth = '860px';
  const chips = new Map(); const stacks = new Map(); let current = 1; let timer = null;
  const detail = el('div', { class: 'op-detail' });
  groups.forEach((group, g) => {
    const x = col * (g + .5); const inGroup = ops.filter((op) => op.group === group);
    root.append(text(x, 18, group, { 'text-anchor': 'middle', style: 'font-size:13.5px;font-weight:650;fill:var(--text-primary)' }));
    const out = inGroup[inGroup.length - 1].output;
    const stack = s('g', { class: 'net-stack' });
    stacks.set(group, { stack, rects: slabs(stack, out, x, mid, inGroup.length) });
    root.append(stack);
    root.append(text(x, 172, shapeText(out), { 'text-anchor': 'middle', style: 'font-size:11.5px;font-variant-numeric:tabular-nums' }));
    if (g < groups.length - 1) root.append(s('line', { class: 'axis-line', x1: x + 44, x2: x + col - 46, y1: mid, y2: mid }), s('path', { d: `M${x + col - 46},${mid - 4} L${x + col - 41},${mid} L${x + col - 46},${mid + 4} z`, fill: 'var(--text-muted)' }));
    inGroup.forEach((op, i) => {
      const chip = s('g', { class: 'op-chip', tabindex: 0, role: 'button', 'aria-label': `${group}, ${op.name}` },
        s('rect', { x: x - 58, y: chipY + i * (chipH + 5), width: 116, height: chipH, rx: 6 }),
        text(x, chipY + i * (chipH + 5) + 18, op.name, { 'text-anchor': 'middle' }));
      const index = ops.indexOf(op);
      const choose = () => { stop(); select(index); };
      chip.addEventListener('click', choose);
      chip.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); choose(); } });
      hover(chip, `${op.name}: ${shapeText(op.input)} → ${shapeText(op.output)}`);
      chips.set(index, chip);
      root.append(chip);
    });
  });
  function select(index) {
    current = index;
    chips.forEach((chip, i) => chip.classList.toggle('on', i === index));
    const op = ops[index];
    const position = ops.filter((item) => item.group === op.group).indexOf(op);
    stacks.forEach(({ stack, rects }, group) => {
      stack.classList.toggle('on', group === op.group);
      rects.forEach((rect, i) => rect.classList.toggle('current', group === op.group && i === position));
    });
    detail.replaceChildren(el('h3', { text: `${op.group}: ${op.name}` }),
      stats(stat('Input', shapeText(op.input)), stat('Output', shapeText(op.output)), stat('Learned numbers', op.params.toLocaleString(), op.params ? `${(100 * op.params / total).toFixed(1)}% of ${total.toLocaleString()}` : 'none'),
        stat('Area each value sees', op.sees ? `${op.sees} × ${op.sees} px` : 'whole image')),
      el('p', { text: OP_TEXT[op.kind](op, dropout) }), DEMOS[op.kind] ? windowDemo(DEMOS[op.kind]) : null);
  }
  const move = (by) => { stop(); select((current + by + ops.length) % ops.length); };
  const play = el('button', { type: 'button', text: 'Play', onclick: () => {
    if (timer) { stop(); return; }
    play.textContent = 'Stop';
    timer = setInterval(() => { if (current === ops.length - 1) stop(); else select(current + 1); }, 1800);
  } });
  function stop() { clearInterval(timer); timer = null; play.textContent = 'Play'; }
  select(current);
  return el('div', {}, el('div', { class: 'toolbar' }, play, el('button', { type: 'button', class: 'ghost', text: 'Previous', onclick: () => move(-1) }), el('button', { type: 'button', class: 'ghost', text: 'Next', onclick: () => move(1) })),
    el('div', { style: 'overflow-x:auto' }, root), detail);
}

// How a batch reaches the GPU, including the pool of processes that prepares it.
export function systemExplorer(train) {
  const n = train.prep_workers;
  const nodes = [
    ['Training images', 'Held in memory', 'Every training image is loaded once and indexed by class, so picking a batch does not touch the disk.'],
    ['Batch plan', 'Seed, epoch, step', 'Each step gets its own random generator, built from the seed, the epoch and the step number. A batch comes out the same whichever process builds it, so results do not depend on the number of processes.'],
    [`Pool of ${n} processes`, 'CPU', `${n} CPU processes start together at the beginning of a run and build batches ahead of the GPU. Each one picks real images, draws any computer-generated shapes and applies augmentation. A batch that stalls becomes an error instead of a silent hang.`, n],
    ['Ready batches', 'Waiting queue', 'Finished batches wait as compact 8-bit images, so the GPU rarely has to wait for the CPU.'],
    ['GPU conversion', 'Lookup table', 'A lookup table on the GPU turns each pixel level into exactly the number the CPU would produce. Plain division on the GPU rounds some levels differently, which would change every result.'],
    ['Network and loss', `${train.batch_size} images per step`, 'The batch goes through the network above, and cross-entropy loss measures how wrong the answers were.'],
    ['Weight update', `${train.optimizer === 'adamw' ? 'AdamW' : train.optimizer}, ${train.schedule}`, 'The optimizer nudges all the learned numbers to reduce the loss, and the learning rate falls along a cosine curve over the run.'],
    ['Check validation', 'After each epoch', 'After each epoch the model is scored on validation images, and only the best epoch so far is kept.'],
  ];
  const detail = el('p', { class: 'op-detail' });
  const buttons = nodes.map(([title, sub, body, workers], i) => el('button', { type: 'button', class: 'sys-node', onclick: () => select(i) },
    el('strong', { text: title }), el('span', { text: sub }), workers ? el('span', { class: 'sys-workers', 'aria-hidden': 'true' }, range(workers).map(() => el('i', {}))) : null));
  function select(i) {
    buttons.forEach((b, k) => b.setAttribute('aria-pressed', String(k === i)));
    detail.textContent = nodes[i][2];
  }
  select(2);
  return el('div', {}, el('div', { class: 'sys-flow' }, buttons), detail);
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
