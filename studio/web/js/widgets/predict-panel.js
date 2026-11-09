// Draw a shape and see each exported model's answer. All scoring is on the server.
// Every result slot is on screen from the start and only its values change, so
// the layout never moves while drawing or clearing.
import { post } from '../api.js';
import { createPad } from '../draw/pad.js';
import { debounce, el, errorBox, latestOnly, note } from '../ui.js';

const ARM_COLOR = { A0: 'var(--series-1)', A1: 'var(--series-2)', B: 'var(--series-3)' };
const ARM_LABEL = { A0: 'A0 · real only', A1: 'A1 · + augmentation', B: 'B · + synthetic' };
const TOP_K = 3;
const EMPTY = 'Draw a shape to see the prediction.';
const BLANK = 'data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==';

function probRow() {
  const name = el('span', { text: '–' });
  const bar = el('b', { style: 'width:0' });
  const value = el('span', { text: '–' });
  return { root: el('div', { class: 'prob' }, name, el('div', { class: 'prob-track' }, bar), value), name, bar, value };
}

function resultSlot(arm) {
  const answer = el('strong', { text: '–' });
  const rows = Array.from({ length: TOP_K }, probRow);
  const latency = el('p', { class: 'note', style: 'margin:6px 0 0', text: '– ms' });
  const root = el('div', { class: 'result' }, el('h3', { text: ARM_LABEL[arm] }), answer, rows.map((r) => r.root), latency);
  return {
    root,
    show(result) {
      answer.textContent = result.not_sure ? 'not sure' : result.label;
      latency.textContent = `${result.latency_ms.toFixed(1)} ms`;
      rows.forEach((row, i) => {
        const top = result.top[i];
        row.name.textContent = top.label;
        row.bar.style.width = `${(top.p * 100).toFixed(1)}%`;
        row.bar.style.background = ARM_COLOR[arm];
        row.value.textContent = `${(top.p * 100).toFixed(0)}%`;
      });
    },
    clear() {
      answer.textContent = '–'; latency.textContent = '– ms';
      rows.forEach((row) => { row.name.textContent = '–'; row.value.textContent = '–'; row.bar.style.width = '0'; });
    },
  };
}

export function predictPanel({ arms, labels, compact = false }) {
  const slots = Object.fromEntries(arms.map((arm) => [arm, resultSlot(arm)]));
  const seenSize = compact ? 96 : 128;
  const seen = el('img', { class: 'pix', src: BLANK, alt: '', width: seenSize, height: seenSize, 'data-tip': 'Your drawing after the same standardization as the training images.' });
  const chips = Object.fromEntries(labels.map((name) => {
    const dots = arms.length > 1 ? arms.map((arm) => [arm, el('i', {})]) : [];
    return [name, { node: el('span', { class: 'label-chip' }, dots.map(([, dot]) => dot), name), dots }];
  }));
  function markChips(results = []) {
    for (const [name, chip] of Object.entries(chips)) {
      const picked = results.filter((r) => !r.not_sure && r.label === name).map((r) => r.arm);
      chip.node.classList.toggle('on', picked.length > 0);
      chip.dots.forEach(([arm, dot]) => { dot.style.background = picked.includes(arm) ? ARM_COLOR[arm] : 'transparent'; });
    }
  }
  const message = el('div', { class: 'panel-msg' }, note(EMPTY));
  const send = latestOnly((image) => post('/api/infer', { image, arms }));
  let last = null;

  function reset(content) {
    last = null;
    Object.values(slots).forEach((slot) => slot.clear());
    seen.src = BLANK; seen.alt = '';
    markChips();
    message.replaceChildren(content);
  }

  async function run() {
    if (!pad.strokeCount()) { reset(note(EMPTY)); return; }
    try {
      const out = await send(pad.png());
      if (out === undefined) return;
      if (out.status !== 'ok') {
        reset(out.status === 'no_model' ? errorBox(new Error(out.message)) : note(out.message));
        return;
      }
      last = out;
      out.results.forEach((result) => slots[result.arm].show(result));
      markChips(out.results);
      seen.src = `data:image/png;base64,${out.seen}`; seen.alt = 'Preprocessed drawing';
      message.replaceChildren(out.missing.length
        ? note(`Not exported yet: ${out.missing.join(', ')}. Run: python -m studio.tools.export_arms`) : '');
    } catch (error) { reset(errorBox(error)); }
  }

  const pad = createPad({ onChange: debounce(run, 60) });

  function feedback() {
    if (!last) return;
    const payload = { saved_at: new Date().toISOString(), note: 'Informal feedback for a future CRISP-DM iteration; not test data.',
      strokes: pad.strokes(), results: last.results.map(({ arm, label, top }) => ({ arm, label, top })) };
    const url = URL.createObjectURL(new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' }));
    el('a', { href: url, download: `shapesense-feedback-${Date.now()}.json` }).click();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
  }

  const tools = compact ? null : el('button', { type: 'button', class: 'ghost', onclick: feedback, text: 'Wrong prediction? Save it' });
  return el('div', {},
    el('div', { class: compact ? 'predict-compact' : 'grid side', style: compact ? null : 'margin:0' },
      el('div', { class: 'pad-wrap' }, pad.canvas, pad.controls, tools),
      el('div', {},
        el('div', { class: 'results' }, Object.values(slots).map((slot) => slot.root)),
        el('h3', { text: 'What the model saw (64×64)' }), seen, message)),
    el('div', { class: 'label-row', role: 'list', 'aria-label': 'All classes the models know' },
      Object.values(chips).map((chip) => chip.node)));
}
