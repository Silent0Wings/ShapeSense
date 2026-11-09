import { post } from '../api.js';
import { card, el, errorBox, note, pageHead, pixImg, singleFlight, stat, stats } from '../ui.js';
import { classPicker, select, sliderRow } from '../widgets/controls.js';
import { boot } from './boot.js';

const deg = (v) => `±${v}°`;
const SLIDERS = [
  ['rotate_deg', 'Rotation range', 0, 180, 1, deg],
  ['scale_lo', 'Scale, minimum', 0.5, 1.5, 0.01, (v) => v.toFixed(2)],
  ['scale_hi', 'Scale, maximum', 0.5, 1.5, 0.01, (v) => v.toFixed(2)],
  ['nonuniform_scale', 'Non-uniform scale', 0, 1, 0.01, (v) => `±${v.toFixed(2)}`],
  ['shear_deg', 'Shear range', 0, 45, 1, deg],
  ['translate_px', 'Translation range', 0, 16, 1, (v) => `±${v} px`],
  ['noise_p', 'Noise probability', 0, 1, 0.05, (v) => `${Math.round(v * 100)}%`],
  ['blur_p', 'Blur probability', 0, 1, 0.05, (v) => `${Math.round(v * 100)}%`],
];
const CLASS_RISK = ['nonuniform_scale', 'shear_deg'];

boot('stage2', (main, d, meta) => {
  main.append(pageHead({ eyebrow: 'Stage 2 · CRISP-DM data preparation', title: 'Augmentation',
    lede: 'Every preview below runs the real Stage 2 code. Pick a class, then change the ranges and see how training images would be altered.',
    chips: ['train side only', 'arms A1, B and A2', 'starts from the tuned settings', 'output is re-framed and binarised'] }));

  let index = 0; let seed = 7; let count = 12;
  const original = el('div', {}); const variants = el('div', { class: 'tiles' }); const status = el('p', { class: 'note' });
  const sliders = {};
  const keepOrdered = (key) => {
    const lo = sliders.scale_lo; const hi = sliders.scale_hi;
    if (lo.get() > hi.get()) (key === 'scale_lo' ? hi.set(lo.get()) : lo.set(hi.get()));
  };
  const values = () => Object.fromEntries(Object.entries(sliders).map(([k, s]) => [k, s.get()]));

  const refresh = singleFlight(async () => {
    const label = picker.value();
    const safe = d.no_shear.includes(meta.classes[label]);
    const body = values();
    if (safe) CLASS_RISK.forEach((k) => { body[k] = 0; });
    try {
      const out = await post('/api/augment', { label, index, seed, n: count, values: body });
      original.replaceChildren(pixImg(out.original, { alt: 'Original image', size: 192, tip: 'The training image before augmentation.' }));
      variants.replaceChildren(...out.variants.map((b64, i) => el('div', { class: 'tile' }, pixImg(b64, { alt: `Variant ${i + 1}`, size: 96, tip: 'One independent random draw of this image.' }))));
      const cap = d.rotate_limits[meta.classes[label]];
      status.textContent = `Source: ${out.source}. Each tile is an independent draw.${cap ? ` Rotation for this class is capped at ±${cap}°.` : ''}`;
    } catch (error) { variants.replaceChildren(errorBox(error)); }
  });

  const applyClassRules = () => {
    const safe = d.no_shear.includes(meta.classes[picker.value()]);
    CLASS_RISK.forEach((k) => sliders[k].enable(!safe, 'Off for this class: it would change the label'));
  };
  const picker = classPicker(meta.classes, () => { index = 0; applyClassRules(); refresh(); }, 3);
  for (const [key, label, min, max, step, format] of SLIDERS) {
    sliders[key] = sliderRow({ label, min, max, step, value: d.defaults[key], format, note: ' ', onInput: () => { keepOrdered(key); refresh(); } });
  }
  const reset = () => { for (const k of Object.keys(sliders)) sliders[k].set(d.defaults[k]); refresh(); };
  applyClassRules();

  main.append(el('div', { class: 'grid side' },
    card('Controls', ...Object.values(sliders).map((s) => s.root),
      el('div', { class: 'toolbar' }, el('button', { type: 'button', text: 'New random draw', onclick: () => { seed += 100; refresh(); } }),
        el('button', { type: 'button', class: 'ghost', text: 'Reset to config', onclick: reset }))),
    el('div', {},
      card('Original and augmented', picker.root,
        el('div', { class: 'toolbar' },
          el('button', { type: 'button', class: 'ghost', text: 'Next image', onclick: () => { index += 1; refresh(); } }),
          select([{ value: '6', label: '6 variants' }, { value: '12', label: '12 variants' }, { value: '24', label: '24 variants' }, { value: '48', label: '48 variants' }], '12', (v) => { count = Number(v); refresh(); }, 'Variants')),
        el('div', { class: 'compare' },
          el('div', {}, el('h3', { style: 'margin-top:0', text: 'Original' }), original),
          el('div', { style: 'flex:1;min-width:0' }, el('h3', { style: 'margin-top:0', text: 'Augmented' }), variants)),
        status),
      card('What each step does', el('ol', { style: 'margin:0;padding-left:20px' },
        ['Rotate by a random angle (any rotation keeps the class)', 'Scale, and for allowed classes stretch or shear', 'Re-frame so the shape fills the image like real data', 'Translate slightly', 'Optionally blur, then return to pure black and white', 'Optionally add ink next to the outline'].map((t) => el('li', { text: t }))),
      note('Sliders set the range each random draw comes from. With everything at zero the output is still re-framed and made binary, which is why it can differ a little from the original. The same random draw is kept while you move a slider, so a probability slider only changes the tiles whose roll crosses the new value.')))));
  main.append(el('div', { class: 'grid two' },
    card('Pool used here', stats(stat('Train images browsable', d.pool.train.kept.toLocaleString(), `of ${d.pool.train.total_manifest.toLocaleString()}`)), note('Augmentation runs only on the training side, after the split.')),
    card('QA sheet from Stage 2', el('img', { class: 'sheet', src: '/img/qa2', alt: 'Stage 2 quality-check sheet' }))));
  refresh();
});
