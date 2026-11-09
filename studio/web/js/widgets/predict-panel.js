// Draw a shape and see each exported model's answer. All scoring is on the server.
import { post } from '../api.js';
import { createPad } from '../draw/pad.js';
import { debounce, el, errorBox, latestOnly, note, pixImg } from '../ui.js';

const ARM_COLOR = { A0: 'var(--series-1)', A1: 'var(--series-2)', B: 'var(--series-3)' };
const ARM_LABEL = { A0: 'A0 · real only', A1: 'A1 · + augmentation', B: 'B · + synthetic' };

function resultCard(result) {
  return el('div', { class: 'result' }, el('h3', { text: ARM_LABEL[result.arm] }),
    el('strong', { text: result.not_sure ? 'not sure' : result.label }),
    result.top.map((t) => el('div', { class: 'prob' }, el('span', { text: t.label }),
      el('div', { class: 'prob-track' }, el('b', { style: `width:${(t.p * 100).toFixed(1)}%;background:${ARM_COLOR[result.arm]}` })),
      el('span', { text: `${(t.p * 100).toFixed(0)}%` }))),
    el('p', { class: 'note', style: 'margin:6px 0 0', text: `${result.latency_ms.toFixed(1)} ms` }));
}

export function predictPanel({ arms, compact = false }) {
  const results = el('div', { class: 'results' }, note('Draw a shape to see the prediction.'));
  const seen = el('div', {});
  const send = latestOnly((image) => post('/api/infer', { image, arms }));
  let last = null;

  async function run() {
    if (!pad.strokeCount()) {
      last = null; seen.replaceChildren();
      results.replaceChildren(note('Draw a shape to see the prediction.'));
      return;
    }
    try {
      const out = await send(pad.png());
      if (out === undefined) return;
      last = out;
      if (out.status !== 'ok') {
        seen.replaceChildren();
        results.replaceChildren(out.status === 'no_model' ? errorBox(new Error(out.message)) : note(out.message));
        return;
      }
      seen.replaceChildren(el('h3', { text: 'What the model saw (64×64)' }), pixImg(out.seen, { alt: 'Preprocessed drawing', size: compact ? 96 : 128 }));
      results.replaceChildren(...out.results.map(resultCard),
        ...(out.missing.length ? [note(`Not exported yet: ${out.missing.join(', ')}. Run: python -m studio.tools.export_arms`)] : []));
    } catch (error) { results.replaceChildren(errorBox(error)); }
  }

  const pad = createPad({ onChange: debounce(run, 60) });

  function feedback() {
    if (!last || last.status !== 'ok') return;
    const payload = { saved_at: new Date().toISOString(), note: 'Informal feedback for a future CRISP-DM iteration; not test data.',
      strokes: pad.strokes(), results: last.results.map(({ arm, label, top }) => ({ arm, label, top })) };
    const url = URL.createObjectURL(new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' }));
    el('a', { href: url, download: `shapesense-feedback-${Date.now()}.json` }).click();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
  }

  const tools = compact ? null : el('button', { type: 'button', class: 'ghost', onclick: feedback, text: 'Wrong prediction? Save it' });
  return el('div', { class: compact ? 'grid' : 'grid side', style: 'margin:0' },
    el('div', { class: 'pad-wrap' }, pad.canvas, pad.controls, tools),
    el('div', {}, results, seen));
}
