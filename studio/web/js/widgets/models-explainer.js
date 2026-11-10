// What each kind of training data is, shown with real images, and what each model trained on.
import { ARM_NAMES, ARM_TIPS } from '../plain.js';
import { post } from '../api.js';
import { el, errorBox, pixImg } from '../ui.js';

const KINDS = [
  { key: 'clean', label: 'Real', color: 'var(--series-1)', body: 'A person\'s drawing from one of four public datasets, standardised to 64×64 black and white.' },
  { key: 'augmented', label: 'Real, augmented', color: 'var(--series-2)', body: 'A real drawing changed at random: rotated, scaled, moved, blurred or given noise. It is still the same shape.' },
  { key: 'synthetic', label: 'Computer-generated', color: 'var(--series-3)', body: 'A shape drawn by the generator from its geometric definition, with no person involved. It is augmented too before training.' },
];
const ABOUT = {
  A0: 'The control. It shows what the real drawings achieve with no help.',
  A1: 'Tests whether random changes to the real drawings help.',
  B: 'Tests whether adding computer-generated shapes helps beyond augmentation.',
  A2: 'Combines all three kinds of image. This is the model the pre-registered test was about.',
  P: 'Learns basic shapes from generated images first, then adapts to real drawings.',
};
const ARM_COLOR = { A0: 'var(--series-1)', A1: 'var(--series-2)', B: 'var(--series-3)', A2: 'var(--series-4)', P: 'var(--series-5)' };

function batchBar(values, caption) {
  const total = Object.values(values).reduce((a, b) => a + b, 0);
  const parts = KINDS.filter((k) => values[k.key]).map((k) => el('span', { style: `flex:${values[k.key]};background:${k.color}`, 'data-tip': `${k.label}: ${values[k.key]} of ${total} images in each batch` },
    `${Math.round(100 * values[k.key] / total)}%`));
  return el('div', {}, caption ? el('small', { class: 'note', text: caption }) : null, el('div', { class: 'batch-bar' }, parts));
}

function modelCard(r, maxEpochs) {
  const usual = { clean: r.clean, augmented: r.augmented, synthetic: r.synthetic };
  return el('div', { class: 'model-card' },
    el('h3', { 'data-tip': ARM_TIPS[r.arm] }, el('span', { class: 'arm-swatch', style: `background:${ARM_COLOR[r.arm]}` }), `${ARM_NAMES[r.arm]} (${r.arm})`),
    el('p', { text: ABOUT[r.arm] }),
    r.pretrain_epochs
      ? [batchBar({ synthetic: r.pretrain_synthetic }, `Epochs 1 to ${r.pretrain_epochs}`), batchBar(usual, `Epochs ${r.pretrain_epochs + 1} to ${maxEpochs}`)]
      : batchBar(usual));
}

export function modelsExplainer({ recipes, maxEpochs, classes, augmentDefaults, synthDefaults }) {
  let label = 2; let round = 0;
  const shapeName = el('strong', {});
  const tiles = Object.fromEntries(KINDS.map((k) => [k.key, el('div', { class: 'kind-image' })]));
  const status = el('div', {});
  async function load() {
    shapeName.textContent = classes[label];
    status.replaceChildren();
    try {
      const [real, synth] = await Promise.all([
        post('/api/augment', { label, index: round, seed: 7 + round, n: 1, values: augmentDefaults }),
        post('/api/synth', { label, seed: 3 + round, n: 1, values: synthDefaults }),
      ]);
      tiles.clean.replaceChildren(pixImg(real.original, { alt: `Real ${classes[label]}`, size: 112 }));
      tiles.augmented.replaceChildren(pixImg(real.variants[0], { alt: `Augmented ${classes[label]}`, size: 112 }));
      tiles.synthetic.replaceChildren(pixImg(synth.items[0].image, { alt: `Computer-generated ${classes[label]}`, size: 112 }));
    } catch (error) { status.replaceChildren(errorBox(error)); }
  }
  load();
  return el('div', {},
    el('h3', { style: 'margin-top:0', text: 'The three kinds of training image' }),
    el('div', { class: 'toolbar' }, el('span', {}, 'Showing: ', shapeName),
      el('button', { type: 'button', class: 'ghost', text: 'Next shape', onclick: () => { label = (label + 1) % classes.length; load(); } }),
      el('button', { type: 'button', class: 'ghost', text: 'Another example', onclick: () => { round += 1; load(); } })),
    el('div', { class: 'kinds' }, KINDS.map((k) => el('div', { class: 'kind', style: `border-top-color:${k.color}` }, tiles[k.key], el('h4', { text: k.label }), el('p', { text: k.body })))),
    status,
    el('h3', { text: 'The five models' }),
    el('p', { class: 'note', text: 'All five are the same network. The only real difference is what each one trained on. The bars show the make-up of each training batch, using the colours above.' }),
    el('div', { class: 'model-grid' }, recipes.map((r) => modelCard(r, maxEpochs))));
}
