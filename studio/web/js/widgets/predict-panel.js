// Draw a shape and see each exported model's answer. All scoring is on the server.
// Every result slot is on screen from the start and only its values change, so
// the layout never moves while drawing or clearing.
import { ARM_NAMES, ARM_TIPS } from '../plain.js';
import { post } from '../api.js';
import { createPad } from '../draw/pad.js';
import { s, text } from '../svg/core.js';
import { debounce, el, errorBox, latestOnly, note } from '../ui.js';

const ARM_COLOR = { A0: 'var(--series-1)', A1: 'var(--series-2)', B: 'var(--series-3)', A2: 'var(--series-4)', P: 'var(--series-5)', vote: 'var(--accent)' };
const ARM_LABEL = { ...Object.fromEntries(Object.entries(ARM_NAMES).map(([key, name]) => [key, `${name} (${key})`])), vote: 'All models vote' };
const TOP_K = 3;
const EMPTY = 'Draw a shape to see the prediction.';
const BLANK = 'data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==';

function probRow() {
  const name = el('span', { text: '–' });
  const bar = el('b', { style: 'width:0' });
  const value = el('span', { text: '–' });
  return { root: el('div', { class: 'prob' }, name, el('div', { class: 'prob-track' }, bar), value), name, bar, value };
}

function resultSlot(arm, colorOf) {
  const answer = el('strong', { text: '–' });
  const rows = Array.from({ length: TOP_K }, probRow);
  const latency = el('p', { class: 'note', style: 'margin:6px 0 0', text: '– ms' });
  const root = el('div', { class: arm === 'vote' ? 'result vote' : 'result' }, el('h3', { 'data-tip': ARM_TIPS[arm] }, el('span', { class: 'arm-swatch', style: `background:${ARM_COLOR[arm]}` }), ARM_LABEL[arm]), answer, rows.map((r) => r.root), latency);
  return {
    root,
    show(result, tally = '') {
      answer.textContent = result.not_sure ? 'not sure' : result.label;
      answer.style.color = result.not_sure ? '' : colorOf(result.label);
      root.style.borderColor = arm === 'vote' && !result.not_sure ? colorOf(result.label) : '';
      latency.textContent = `${tally}${result.latency_ms.toFixed(1)} ms`;
      rows.forEach((row, i) => {
        const top = result.top[i];
        row.name.textContent = top.label;
        row.bar.style.width = `${(top.p * 100).toFixed(1)}%`;
        row.bar.style.background = colorOf(top.label);
        row.value.textContent = `${(top.p * 100).toFixed(0)}%`;
      });
    },
    clear() {
      answer.textContent = '–'; answer.style.color = ''; root.style.borderColor = ''; latency.textContent = '– ms';
      rows.forEach((row) => { row.name.textContent = '–'; row.value.textContent = '–'; row.bar.style.width = '0'; });
    },
  };
}

// Every model around the vote, with a line from each coloured by the label it predicts.
function voteNetwork(slots, arms, colorOf) {
  const upper = Math.ceil(arms.length / 2);
  arms.forEach((arm, i) => {
    const top = i < upper; const inRow = top ? upper : arms.length - upper;
    slots[arm].root.style.gridArea = `${top ? 1 : 3} / ${4 - inRow + 2 * (top ? i : i - upper)} / span 1 / span 2`;
  });
  slots.vote.root.style.gridArea = '2 / 3 / span 1 / span 2';
  const lines = s('svg', { class: 'vote-lines', 'aria-hidden': 'true' });
  const root = el('div', { class: 'vote-net' }, lines, Object.values(slots).map((slot) => slot.root));
  let shown = [];
  function draw(results = shown) {
    shown = results;
    const box = root.getBoundingClientRect();
    lines.setAttribute('viewBox', `0 0 ${box.width} ${box.height}`);
    const vote = slots.vote.root.getBoundingClientRect();
    const counts = { up: 0, down: 0 };
    const total = { up: Math.min(upper, shown.length), down: Math.max(0, shown.length - upper) };
    lines.replaceChildren(...shown.flatMap((result) => {
      const card = slots[result.arm].root.getBoundingClientRect();
      const above = card.bottom <= vote.top + 1; const side = above ? 'up' : 'down';
      counts[side] += 1;
      const x1 = card.left + card.width / 2 - box.left; const y1 = (above ? card.bottom : card.top) - box.top;
      const x2 = vote.left + (vote.width * counts[side]) / (total[side] + 1) - box.left; const y2 = (above ? vote.top : vote.bottom) - box.top;
      const my = (y1 + y2) / 2;
      const line = s('path', { d: `M${x1},${y1} C${x1},${my} ${x2},${my} ${x2},${y2}`, fill: 'none', 'stroke-width': 2.6,
        stroke: result.not_sure ? 'var(--text-muted)' : colorOf(result.label), 'stroke-dasharray': result.not_sure ? '5 5' : null });
      return [line, text((x1 + x2) / 2, my + 4, result.not_sure ? 'not sure' : result.label, { 'text-anchor': 'middle', class: 'vote-line-label' })];
    }));
  }
  new ResizeObserver(() => draw()).observe(root);
  return { root, draw };
}

export function predictPanel({ arms, labels, compact = false }) {
  const colorOf = (name) => `var(--label-${labels.indexOf(name)})`;
  const slots = Object.fromEntries((arms.length > 1 ? ['vote', ...arms] : arms).map((arm) => [arm, resultSlot(arm, colorOf)]));
  const network = arms.length > 1 ? voteNetwork(slots, arms, colorOf) : null;
  const seenSize = compact ? 96 : 128;
  const seen = el('img', { class: 'pix', src: BLANK, alt: '', width: seenSize, height: seenSize, 'data-tip': 'Your drawing after the same standardization as the training images.' });
  const chips = Object.fromEntries(labels.map((name) => {
    const dots = arms.length > 1 ? arms.map((arm) => [arm, el('i', { hidden: true })]) : [];
    return [name, { node: el('span', { class: 'label-chip' }, el('span', { class: 'label-swatch', style: `background:${colorOf(name)}` }), dots.map(([, dot]) => dot), name), dots }];
  }));
  function markChips(results = []) {
    for (const [name, chip] of Object.entries(chips)) {
      const picked = results.filter((r) => !r.not_sure && r.label === name).map((r) => r.arm);
      chip.node.classList.toggle('on', picked.length > 0);
      chip.dots.forEach(([arm, dot]) => { dot.hidden = !picked.includes(arm); dot.style.background = picked.includes(arm) ? ARM_COLOR[arm] : 'transparent'; });
    }
  }
  const message = el('div', { class: 'panel-msg' }, note(EMPTY));
  const send = latestOnly((image) => post('/api/infer', { image, arms }));
  let last = null;

  function reset(content) {
    last = null;
    Object.values(slots).forEach((slot) => slot.clear());
    network?.draw([]);
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
      out.results.filter((result) => slots[result.arm]).forEach((result) => slots[result.arm].show(result));
      if (out.vote && slots.vote) {
        const agree = out.results.filter((result) => !result.not_sure && result.label === out.vote.label).length;
        slots.vote.show(out.vote, `${agree} of ${out.results.length} models picked this · `);
      }
      network?.draw(out.results);
      markChips(out.results);
      seen.src = `data:image/png;base64,${out.seen}`; seen.alt = 'Preprocessed drawing';
      message.replaceChildren(out.missing.length
        ? note(`Not exported yet: ${out.missing.join(', ')}. Run: python -m studio.tools.export_arms`) : '');
    } catch (error) { reset(errorBox(error)); }
  }

  const pad = createPad({ onChange: debounce(run, 60) });

  async function feedback() {
    if (!last) { message.replaceChildren(note('Draw a shape first, then save it.')); return; }
    try {
      const out = await post('/api/feedback', { image: pad.png(), strokes: pad.strokes(),
        results: last.results.map(({ arm, label, top }) => ({ arm, label, top })) });
      message.replaceChildren(note(`Saved to ${out.saved}`));
    } catch (error) { message.replaceChildren(errorBox(error)); }
  }

  const tools = compact ? null : el('button', { type: 'button', class: 'ghost', onclick: feedback, text: 'Wrong prediction? Save it', 'data-tip': 'Saves this drawing and every answer to studio/feedback in this repository.' });
  return el('div', {},
    el('div', { class: compact ? 'predict-compact' : 'grid side', style: compact ? null : 'margin:0' },
      el('div', { class: 'pad-wrap' }, pad.canvas, pad.controls, tools,
        el('h3', { style: 'margin:8px 0 0', text: 'What the model saw (64×64)' }), seen),
      el('div', {},
        network ? network.root : el('div', { class: 'results' }, Object.values(slots).map((slot) => slot.root)),
        arms.length > 1 ? note('Each line takes the colour of the label that model predicts, and the labels below show the colours. The vote averages every model\'s probabilities with equal weight, so a very sure model can outweigh a count of models. It has no measured score of its own.') : null,
        message)),
    el('div', { class: 'label-row', role: 'list', 'aria-label': 'All classes the models know' },
      Object.values(chips).map((chip) => chip.node)));
}
