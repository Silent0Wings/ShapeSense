// One picture per failure: recorded measurements, small diagrams and live examples.
import { get, page, post } from '../api.js';
import { ciChart, lines, valueBars } from '../svg/charts.js';
import { s, svgRoot, text } from '../svg/core.js';
import { el, errorBox, note, pixImg } from '../ui.js';

const tile = (b64, caption, tip) => el('div', { class: 'tile' }, pixImg(b64, { alt: caption, size: 88, tip }), caption);
const tileRow = (title, tiles) => el('div', {}, el('p', { class: 'note', text: title }), el('div', { class: 'tiles' }, tiles));

function flowRow(tag, steps) {
  return el('div', { class: 'flow-row' }, el('span', { class: 'flow-tag', text: tag }),
    steps.flatMap((step, i) => [i ? el('span', { class: 'flow-arrow', text: '→' }) : null, el('span', { class: 'flow-step', text: step })]));
}

function field(b) {
  const unit = 3; const side = b.frame * unit;
  const panel = (x, seen, title) => {
    const mid = x + side / 2; const y = 8 + side / 2;
    const box = (px, attrs) => s('rect', { x: mid - (px * unit) / 2, y: y - (px * unit) / 2, width: px * unit, height: px * unit, ...attrs });
    return [s('rect', { x, y: 8, width: side, height: side, fill: 'var(--surface-2)', stroke: 'var(--line)' }),
      box(seen, { fill: 'var(--accent)', 'fill-opacity': 0.4, stroke: 'var(--accent)' }),
      box(b.shape, { fill: 'none', stroke: 'var(--text-primary)', 'stroke-width': 2 }),
      text(mid, side + 28, title, { 'text-anchor': 'middle', style: 'font-size:14px;fill:var(--text-primary)' })];
  };
  const root = svgRoot(side * 2 + 60, side + 40, b.title);
  root.append(...panel(0, b.before, `Three blocks: ${b.before} px`), ...panel(side + 60, b.after, `Four blocks: ${b.after} px`));
  return root;
}

async function augment(b, meta) {
  const label = meta.classes.indexOf(b.label);
  const { defaults } = await page('stage2');
  const outs = await Promise.all(b.rows.map((row) => post('/api/augment', { label, index: 0, seed: 7, n: 7, values: { ...defaults, ...row.values }, uncapped: Boolean(row.uncapped) })));
  return el('div', {}, tileRow('Original training image', [tile(outs[0].original, b.label, `From ${outs[0].source}.`)]),
    outs.map((out, i) => tileRow(b.rows[i].title, out.variants.map((v, k) => tile(v, `draw ${k + 1}`, 'One random draw through the real augmentation code.')))));
}

async function synth(b, meta) {
  const label = meta.classes.indexOf(b.label);
  const [real, stage3] = await Promise.all([get(`/api/samples?label=${label}&split=train&n=7`), page('stage3')]);
  const made = await post('/api/synth', { label, seed: 7, n: 7, values: stage3.defaults });
  return el('div', {}, tileRow('Real training images', real.items.map((item) => tile(item.image, item.source, 'A real training image.'))),
    tileRow('Generated images', made.items.map((item, k) => tile(item.image, `sample ${k + 1}`, 'Drawn by the synthetic generator.'))));
}

// Iteration 3 is the live one. An earlier failure reads the frozen record of its own iteration.
const LIVE_ITERATION = 3;
const FROZEN_VERDICT = { 1: 'iteration1', 2: 'iteration2' };
const iterationNumber = (label) => Number((label.match(/\d+/) || [0])[0]);

async function curve(b, meta) {
  // Frozen iteration records keep no per-epoch log, so an earlier run's curve is not drawn from the live folder.
  if (meta.iteration < LIVE_ITERATION) return note('The per-epoch log of this run is not kept in the frozen record, so no curve is drawn.');
  const { log } = await get(`/api/stage4/run/${b.run}`);
  const values = log.map((r) => r.val_macro_f1);
  const worst = Math.max(...values.slice(1).map((v, i) => values[i] - v));
  return el('div', {}, lines({ series: [{ label: 'validation macro-F1', color: 'var(--series-1)', values }], xs: log.map((r) => r.epoch), label: b.title, yLabel: 'macro-F1' }),
    note(`Largest drop between two epochs in this run: ${worst.toFixed(1)} points.`));
}

async function verdict(b, meta) {
  const source = b.source === 'stage5' && FROZEN_VERDICT[meta.iteration] ? FROZEN_VERDICT[meta.iteration] : b.source;
  const d = await page(source);
  const m = d.metrics;
  const fresh = d.fresh ?? m.fresh_holdout;
  const rows = source === 'iteration1'
    ? [{ label: m.primary.label, delta: m.delta, ci: m.ci }, ...Object.entries(m.secondary).map(([label, x]) => ({ label, delta: x.delta, ci: x.ci }))]
    : [{ label: 'Test split', delta: m.delta, ci: m.ci }, { label: 'Fresh holdout', delta: fresh.delta, ci: fresh.ci }];
  return ciChart({ rows, label: b.title, required: b.required });
}

const RENDER = {
  bars: (b) => valueBars({ rows: b.rows, label: b.title, unit: b.unit, domain: b.domain }),
  images: (b) => el('div', {}, b.keys.map((key) => el('img', { class: 'sheet', src: `/img/${key}`, alt: b.title, style: 'margin-bottom:8px' }))),
  flow: (b) => el('div', {}, flowRow('Failed', b.before), flowRow('Fixed', b.after)),
  field, augment, synth, curve, verdict,
};

function block(b, meta) {
  const host = el('div', {}, note('Loading…'));
  Promise.resolve().then(() => RENDER[b.kind](b, meta)).then((node) => host.replaceChildren(node)).catch((error) => host.replaceChildren(errorBox(error)));
  return el('div', { class: 'visual-block' }, el('h3', { text: b.title }), host, b.caption ? note(b.caption) : null);
}

export const failureVisual = (blocks, meta, iteration) => blocks.map((b) => block(b, { ...meta, iteration: iterationNumber(iteration) }));
