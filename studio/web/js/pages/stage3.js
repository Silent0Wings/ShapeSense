import { get, post } from '../api.js';
import { card, el, errorBox, fmt, note, pageHead, pixImg, singleFlight, stat, stats, table, tableView } from '../ui.js';
import { animateButton, classPicker, sliderRow } from '../widgets/controls.js';
import { stageBrief, stageNav } from '../widgets/stage-brief.js';
import { boot } from './boot.js';

const SLIDERS = [
  ['radius_lo', 'Radius, minimum (px)', 8, 30, 1], ['radius_hi', 'Radius, maximum (px)', 8, 30, 1],
  ['center_jitter_px', 'Centre jitter (±px)', 0, 12, 1], ['vertex_jitter_px', 'Vertex jitter (±px)', 0, 4, 0.1],
  ['ellipse_max_axis_ratio', 'Ellipse, largest axis ratio', 1.25, 4, 0.05, 'ellipse'],
  ['rectangle_max_side_ratio', 'Rectangle, largest side ratio', 1.25, 4, 0.05, 'rectangle'],
  ['diamond_lo', 'Diamond angle, minimum (°)', 20, 80, 1, 'diamond'], ['diamond_hi', 'Diamond angle, maximum (°)', 20, 80, 1, 'diamond'],
  ['star_lo', 'Star inner ratio, minimum', 0.2, 0.6, 0.01, 'star'], ['star_hi', 'Star inner ratio, maximum', 0.2, 0.6, 0.01, 'star'],
];
const sentence = (key) => { const text = key.replace(/_/g, ' '); return text.charAt(0).toUpperCase() + text.slice(1); };
const checkRows = (checks = {}) => Object.entries(checks).map(([key, ok]) => ({ label: sentence(key), ok: typeof ok === 'boolean' ? ok : null }));

boot('stage3', (main, d, meta) => {
  main.append(pageHead({ eyebrow: 'Stage 3 · CRISP-DM data preparation', title: 'Synthetic generator',
    lede: 'Arms B and A2 draw part of each training batch from this generator, and arm P trains on it alone before moving to real images. These samples come from the real Stage 3 code, including the margins that stop a shape looking like its neighbouring class.',
    chips: ['arms B, A2 and P', 'starts from the tuned settings', 'margins enforced'] }));
  main.append(stageBrief({
    job: 'Draws extra training shapes from their geometric definition, without a person.',
    input: "A shape's definition and its allowed ranges.",
    process: 'Draws random examples within limits that stop a shape being mistaken for a neighbouring one.',
    output: 'Generated shapes, used in training by the models that draw on this generator.',
    finding: 'The generated strokes were first thinner than real ones, and the ranges had been guessed. Stroke width was matched to the real drawings and the ranges were tuned.',
    checks: checkRows(d.checks),
  }));

  const realBox = el('div', {}); const madeBox = el('div', {}); const caption = el('p', { class: 'note' });
  main.append(card('Real against generated', caption,
    el('div', { class: 'compare' },
      el('div', {}, el('h3', { style: 'margin-top:0', text: 'Real' }), realBox),
      el('div', { style: 'flex:1;min-width:0' }, el('h3', { style: 'margin-top:0', text: 'Generated' }), madeBox))));

  let seed = 3; let chosen = null;
  const grid = el('div', { class: 'tiles' }); const detail = el('div', {});
  const sliders = {};
  const keepOrdered = (key) => {
    for (const name of ['radius', 'diamond', 'star']) {
      const lo = sliders[`${name}_lo`]; const hi = sliders[`${name}_hi`];
      if (lo.get() > hi.get()) (key === `${name}_lo` ? hi.set(lo.get()) : lo.set(hi.get()));
    }
  };
  const values = () => Object.fromEntries(Object.entries(sliders).map(([k, s]) => [k, s.get()]));

  function showParams(item, button) {
    chosen?.setAttribute('aria-pressed', 'false');
    button?.setAttribute('aria-pressed', 'true'); chosen = button;
    const show = (name, value) => {
      if (!Array.isArray(value)) return fmt(value, 2);
      const flat = value.flat();
      return name === 'vertex_jitter_px'
        ? `${value.length} vertices, largest ±${fmt(Math.max(...flat.map(Math.abs)), 2)}`
        : flat.map((v) => fmt(v, 1)).join(', ');
    };
    const rows = Object.entries(item.params).map(([name, value]) => ({ name, value: show(name, value) }));
    detail.replaceChildren(el('h3', { text: 'Drawn parameters of the selected shape' }),
      table(rows, [{ key: 'name', label: 'Parameter' }, { key: 'value', label: 'Value', num: true }]));
  }

  const refresh = singleFlight(async () => {
    const v = values();
    try {
      const out = await post('/api/synth', { label: picker.value(), seed, n: 24, values: v });
      chosen = null;
      const buttons = out.items.map((item) => {
        const b = el('button', { type: 'button', class: 'tile clickable', 'aria-pressed': 'false', 'aria-label': 'Show parameters', onclick: () => showParams(item, b) }, pixImg(item.image, { alt: 'Synthetic shape', size: 88, tip: 'Select to see the values used to draw this shape.' }));
        return b;
      });
      grid.replaceChildren(...buttons);
      showParams(out.items[0], buttons[0]);
      madeBox.replaceChildren(pixImg(out.items[0].image, { alt: 'Generated shape', size: 128, tip: 'A shape drawn by the Stage 3 generator for this class.' }));
    } catch (error) { grid.replaceChildren(errorBox(error)); }
  });

  // One real drawing of the picked class, fetched only when the class changes.
  async function showReal(label) {
    caption.textContent = `Class: ${meta.classes[label]}. A real training drawing next to one generated for the same class.`;
    try {
      const out = await get(`/api/samples?label=${label}&split=train&n=1`);
      if (picker.value() !== label) return;
      realBox.replaceChildren(out.items[0]
        ? pixImg(out.items[0].image, { alt: 'Real shape', size: 128, tip: 'A real training drawing of this class.' })
        : note('No real drawing is available for this class.'));
    } catch (error) { if (picker.value() === label) realBox.replaceChildren(errorBox(error)); }
  }

  const applyClass = () => {
    const name = meta.classes[picker.value()];
    for (const [key, , , , , only] of SLIDERS) if (only) sliders[key].enable(only === name, `Only used for ${only}`);
  };
  const picker = classPicker(meta.classes, () => { applyClass(); showReal(picker.value()); refresh(); }, 8);
  for (const [key, label, min, max, step] of SLIDERS) sliders[key] = sliderRow({ label, min, max, step, value: d.defaults[key], note: ' ', onInput: () => { keepOrdered(key); refresh(); } });
  applyClass();
  const animation = animateButton({ sliders, onStep: keepOrdered, refresh });

  const ranges = Object.entries(d.ranges).filter(([k]) => k !== 'margins_in_force').flatMap(([name, params]) =>
    Object.entries(params).map(([param, [min, max]]) => ({ name, param, min, max })));
  main.append(el('div', { class: 'grid side' },
    card('Controls', ...Object.values(sliders).map((s) => s.root),
      el('div', { class: 'toolbar' }, el('button', { type: 'button', text: 'Resample', onclick: () => { seed += 100; refresh(); } }), animation.button,
        el('button', { type: 'button', class: 'ghost', text: 'Reset to config', onclick: () => { animation.stop(); for (const k of Object.keys(sliders)) sliders[k].set(d.defaults[k]); refresh(); } }))),
    el('div', {}, card('Generated samples', picker.root, el('div', { style: 'height:10px' }), grid, detail))));
  main.append(el('div', { class: 'grid two' },
    card('Ambiguity margins', stats(...Object.entries(d.margins).map(([k, v]) => stat(k.replace(/_/g, ' '), v))),
      note('A generated ellipse must be clearly not a circle, a rectangle clearly not a square, and a diamond clearly not a square.'),
      tableView(ranges, [{ key: 'name', label: 'Class' }, { key: 'param', label: 'Parameter' }, { label: 'Min seen', num: true, render: (r) => fmt(r.min) }, { label: 'Max seen', num: true, render: (r) => fmt(r.max) }], 'Show the ranges recorded by Stage 3')),
    card('QA sheet from Stage 3', el('img', { class: 'sheet', src: '/img/qa3', alt: 'Stage 3 quality-check sheet' }))));
  main.append(stageNav(3));
  showReal(picker.value());
  refresh();
});
