import { crispProgress } from '../widgets/crisp-cycle.js';
import { failureLog, iterationLog } from '../widgets/findings.js';
import { predictPanel } from '../widgets/predict-panel.js';
import { get } from '../api.js';
import { finding, otherArmsNote, verdictPicture } from '../plain.js';
import { badge, card, el, note, pageHead, pixImg } from '../ui.js';
import { boot } from './boot.js';

async function shapeRow(classes) {
  const samples = await Promise.all(classes.map((_, label) => get(`/api/samples?label=${label}&split=train&n=1`)));
  return el('div', { class: 'tiles' }, samples.map((s, i) => el('div', { class: 'tile' }, pixImg(s.items[0].image, { alt: classes[i], size: 72 }), classes[i])));
}

boot('home', async (main, data, meta) => {
  main.append(pageHead({
    eyebrow: 'ShapeSense',
    title: 'Draw a shape, and a small AI model names it',
    lede: 'ShapeSense trains a small neural network to recognise ten shapes, and tests which kinds of training data make it better.',
  }));
  main.append(card('The ten shapes', await shapeRow(meta.classes), el('p', {}, el('a', { class: 'cta', href: 'live.html', text: 'Try drawing a shape' }))));
  if (data.verdict) main.append(card('The main finding', el('p', { class: 'finding', text: finding(data.verdict) }), verdictPicture(data.verdict, data.criterion.macro_f1_min_gain_points),
    note('The dot is the measured difference in macro-F1 points, the line is its uncertainty range, and the dashed line is the gain set in advance as the target. Real only trains on real images alone. Full mix adds augmented and computer-generated shapes.'),
    data.verdict.others?.length ? note(otherArmsNote) : null));
  main.append(card('The CRISP-DM cycle', crispProgress({ phases: data.phases, iterations: meta.iterations, results: data.results }),
    note('Move the slider to walk through each trip round the cycle, and select a step to read what was found there. Dashed arrows are the trips back: the brightest one started the iteration shown.')));
  main.append(iterationLog(meta.iterations));
  main.append(failureLog(meta.failures, meta.phases));
  main.append(el('div', { class: 'grid two' },
    data.arms.length
      ? card('Try it now', predictPanel({ arms: [meta.candidate], compact: true, labels: meta.classes }))
      : card('Try it now', note('No exported model yet. Run: python run_pipeline.py --stages 6')),
    card('Pipeline stages', el('div', { class: 'lights' }, data.lights.map((l) => el('a', { class: 'light', href: l.page },
      `${l.stage} · ${l.title}`, l.status === 'passed' ? badge('pass', 'Passed') : badge('fail', l.status)))))));
});
