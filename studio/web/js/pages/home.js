import { crispCycle } from '../widgets/crisp-cycle.js';
import { failureLog, iterationLog } from '../widgets/findings.js';
import { predictPanel } from '../widgets/predict-panel.js';
import { badge, card, el, note, pageHead } from '../ui.js';
import { boot } from './boot.js';

boot('home', (main, data, meta) => {
  main.append(pageHead({
    eyebrow: 'Shape classification project',
    title: 'From business question to a live model',
    lede: 'Ten shape classes, four public datasets and one question: does synthetic training data help a small CNN? Follow the CRISP-DM steps below, see what each trip round the cycle found, or draw a shape and see the models answer.',
  }));
  main.append(card('The CRISP-DM cycle', crispCycle({ phases: data.phases, verdict: data.verdict }),
    note('Select a step to open it. Dashed arrows are the trips back round the loop: iteration 1 went from Modeling to Data Preparation, and iteration 2 from Evaluation to Data Preparation.')));
  main.append(iterationLog(meta.iterations));
  main.append(failureLog(meta.failures, meta.phases));
  main.append(el('div', { class: 'grid two' },
    data.arms.length
      ? card('Try it now', predictPanel({ arms: [meta.candidate], compact: true, labels: meta.classes }))
      : card('Try it now', note('No exported model yet. Run: python run_pipeline.py --stages 6')),
    card('Pipeline stages', el('div', { class: 'lights' }, data.lights.map((l) => el('a', { class: 'light', href: l.page },
      `${l.stage} · ${l.title}`, l.status === 'passed' ? badge('pass', 'Passed') : badge('fail', l.status)))))));
});
