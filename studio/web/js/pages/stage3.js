import { post } from '../api.js';
import { card, el, errorBox, fmt, note, pageHead, pixImg, singleFlight, stat, stats, table, tableView } from '../ui.js';
import { classPicker, sliderRow } from '../widgets/controls.js';
import { boot } from './boot.js';

const SLIDERS = [
  ['radius_lo', 'Radius, minimum (px)', 8, 30, 1], ['radius_hi', 'Radius, maximum (px)', 8, 30, 1],
  ['center_jitter_px', 'Centre jitter (±px)', 0, 12, 1], ['vertex_jitter_px', 'Vertex jitter (±px)', 0, 4, 0.1],
  ['ellipse_max_axis_ratio', 'Ellipse, largest axis ratio', 1.25, 4, 0.05, 'ellipse'],
  ['rectangle_max_side_ratio', 'Rectangle, largest side ratio', 1.25, 4, 0.05, 'rectangle'],
  ['diamond_lo', 'Diamond angle, minimum (°)', 20, 80, 1, 'diamond'], ['diamond_hi', 'Diamond angle, maximum (°)', 20, 80, 1, 'diamond'],
  ['star_lo', 'Star inner ratio, minimum', 0.2, 0.6, 0.01, 'star'], ['star_hi', 'Star inner ratio, maximum', 0.2, 0.6, 0.01, 'star'],
];

boot('stage3', (main, d, meta) => {
  main.append(pageHead({ eyebrow: 'Stage 3 · CRISP-DM data preparation', title: 'Synthetic generator',
    lede: 'Arm B draws 30% of each training batch from this generator. These samples come from the real Stage 3 code, including the margins that stop a shape looking like its neighbouring class.',
    chips: ['arm B only', 'margins enforced'] }));

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
    } catch (error) { grid.replaceChildren(errorBox(error)); }
  });

  const applyClass = () => {
    const name = meta.classes[picker.value()];
    for (const [key, , , , , only] of SLIDERS) if (only) sliders[key].enable(only === name, `Only used for ${only}`);
  };
  const picker = classPicker(meta.classes, () => { applyClass(); refresh(); }, 8);
  for (const [key, label, min, max, step] of SLIDERS) sliders[key] = sliderRow({ label, min, max, step, value: d.defaults[key], note: ' ', onInput: () => { keepOrdered(key); refresh(); } });
  applyClass();

  const ranges = Object.entries(d.ranges).filter(([k]) => k !== 'margins_in_force').flatMap(([name, params]) =>
    Object.entries(params).map(([param, [min, max]]) => ({ name, param, min, max })));
  main.append(el('div', { class: 'grid side' },
    card('Controls', ...Object.values(sliders).map((s) => s.root),
      el('div', { class: 'toolbar' }, el('button', { type: 'button', text: 'Resample', onclick: () => { seed += 100; refresh(); } }),
        el('button', { type: 'button', class: 'ghost', text: 'Reset to config', onclick: () => { for (const k of Object.keys(sliders)) sliders[k].set(d.defaults[k]); refresh(); } }))),
    el('div', {}, card('Generated samples', picker.root, el('div', { style: 'height:10px' }), grid, detail))));
  main.append(el('div', { class: 'grid two' },
    card('Ambiguity margins', stats(...Object.entries(d.margins).map(([k, v]) => stat(k.replace(/_/g, ' '), v))),
      note('A generated ellipse must be clearly not a circle, a rectangle clearly not a square, and a diamond clearly not a square.'),
      tableView(ranges, [{ key: 'name', label: 'Class' }, { key: 'param', label: 'Parameter' }, { label: 'Min seen', num: true, render: (r) => fmt(r.min) }, { label: 'Max seen', num: true, render: (r) => fmt(r.max) }], 'Show the ranges recorded by Stage 3')),
    card('QA sheet from Stage 3', el('img', { class: 'sheet', src: '/img/qa3', alt: 'Stage 3 quality-check sheet' }))));
  refresh();
});
