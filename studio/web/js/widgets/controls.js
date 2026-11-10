// Form controls shared by the interactive pages.
import { el } from '../ui.js';

export function classPicker(names, onChange, initial = 0) {
  let value = initial;
  const buttons = names.map((name, i) => el('button', {
    type: 'button', 'aria-pressed': i === initial ? 'true' : 'false', text: name,
    onclick: () => { set(i); onChange(i); },
  }));
  function set(next) {
    value = next;
    buttons.forEach((b, i) => b.setAttribute('aria-pressed', i === next ? 'true' : 'false'));
  }
  return { root: el('div', { class: 'pick', role: 'group', 'aria-label': 'Shape class' }, buttons), value: () => value, set };
}

export function sliderRow({ label, min, max, step, value, format = (v) => v, note, onInput }) {
  const input = el('input', { type: 'range', min, max, step, value, 'aria-label': label });
  const output = el('output', { text: format(Number(value)) });
  const hint = note ? el('small', { text: note }) : null;
  const root = el('label', { class: 'slider' }, el('span', { text: label }), output, input, hint);
  input.addEventListener('input', () => { output.textContent = format(Number(input.value)); onInput?.(); });
  return {
    root,
    input,
    get: () => Number(input.value),
    set: (v) => { input.value = v; output.textContent = format(Number(v)); },
    enable: (on, reason) => {
      input.disabled = !on; root.classList.toggle('off', !on);
      if (hint) hint.textContent = on ? note : reason;
    },
  };
}

// Walks every enabled slider in small random steps, keeping the same random draw,
// so the images change only because the settings did. Touching a slider stops it.
export function animateButton({ sliders, onStep, refresh, interval = 700 }) {
  const direction = Object.fromEntries(Object.keys(sliders).map((key) => [key, Math.random() < 0.5 ? -1 : 1]));
  let timer = null;
  const stop = () => { clearInterval(timer); timer = null; button.textContent = 'Animate'; button.setAttribute('aria-pressed', 'false'); };
  const tick = () => {
    if (document.hidden) return;
    for (const [key, row] of Object.entries(sliders)) {
      const { input } = row;
      if (input.disabled) continue;
      const min = Number(input.min); const max = Number(input.max); const step = Number(input.step);
      if (Math.random() < 0.2) direction[key] *= -1;
      let next = row.get() + direction[key] * Math.max(step, (max - min) * 0.03) * (0.5 + Math.random());
      if (next < min || next > max) { direction[key] *= -1; next = Math.min(max, Math.max(min, next)); }
      row.set(Number((min + Math.round((next - min) / step) * step).toFixed(6)));
      onStep?.(key);
    }
    refresh();
  };
  const start = () => { button.textContent = 'Stop'; button.setAttribute('aria-pressed', 'true'); tick(); timer = setInterval(tick, interval); };
  const button = el('button', { type: 'button', class: 'ghost', text: 'Animate', 'aria-pressed': 'false', onclick: () => (timer ? stop() : start()) });
  Object.values(sliders).forEach((row) => row.input.addEventListener('input', () => { if (timer) stop(); }));
  return { button, stop };
}

export function select(options, value, onChange, label) {
  const node = el('select', { 'aria-label': label, onchange: () => onChange(node.value) },
    options.map((o) => el('option', { value: o.value ?? o, selected: (o.value ?? o) === value, text: o.label ?? o })));
  return node;
}
