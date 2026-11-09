import { card, el, fmt, note, pageHead } from '../ui.js';
import { predictPanel } from '../widgets/predict-panel.js';
import { boot } from './boot.js';

boot('live', (main, d, meta) => {
  main.append(pageHead({ eyebrow: 'CRISP-DM deployment', title: 'Draw and predict',
    lede: 'Draw any of the ten shapes. Your drawing goes through the shipped standardize.py, then each exported ONNX model scores it.',
    chips: ['mouse, touch or stylus', 'runs on this machine'] }));
  if (!d.arms.length) { main.append(card('Not ready', note('No exported model yet. Run: python run_pipeline.py --stages 6'))); return; }
  main.append(card('Canvas', predictPanel({ arms: d.arms, labels: meta.classes })));
  main.append(card('How to read this',
    el('p', { text: `Live models: ${d.arms.map((a) => `${a} (${d.provenance[a]?.run ?? 'unknown run'}, validation ${fmt(d.provenance[a]?.val_macro_f1, 1)})`).join('; ')}.` }),
    note('Below 50% confidence the answer is shown as "not sure". Sketched diamonds are outside the training data, because the diamond class comes only from rendered images. Drawings here are informal evidence and never affect the verdict. Saved drawings go to studio/feedback in this repository.')));
});
