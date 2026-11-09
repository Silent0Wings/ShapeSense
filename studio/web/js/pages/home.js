import { crispCycle } from '../widgets/crisp-cycle.js';
import { predictPanel } from '../widgets/predict-panel.js';
import { badge, card, el, note, pageHead } from '../ui.js';
import { boot } from './boot.js';

boot('home', (main, data) => {
  main.append(pageHead({
    eyebrow: 'Shape classification project',
    title: 'From business question to a live model',
    lede: 'Ten shape classes, four public datasets and one question: does synthetic training data help a small CNN? Follow the CRISP-DM steps below, or draw a shape and see the models answer.',
  }));
  main.append(card('The CRISP-DM cycle', crispCycle({ phases: data.phases, verdict: data.verdict }),
    note('Select a step to open it. The dashed Modeling arrow is iteration 1: a modeling finding sent the project back to Data Preparation.')));
  main.append(el('div', { class: 'grid two' },
    data.arms.length
      ? card('Try it now', predictPanel({ arms: ['A0'], compact: true }))
      : card('Try it now', note('No exported model yet. Run: python run_pipeline.py --stages 6')),
    card('Pipeline stages', el('div', { class: 'lights' }, data.lights.map((l) => el('a', { class: 'light', href: l.page },
      `${l.stage} · ${l.title}`, l.status === 'passed' ? badge('pass', 'Passed') : badge('fail', l.status)))))));
});
