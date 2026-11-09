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
    get: () => Number(input.value),
    set: (v) => { input.value = v; output.textContent = format(Number(v)); },
    enable: (on, reason) => {
      input.disabled = !on; root.classList.toggle('off', !on);
      if (hint) hint.textContent = on ? note : reason;
    },
  };
}

export function select(options, value, onChange, label) {
  const node = el('select', { 'aria-label': label, onchange: () => onChange(node.value) },
    options.map((o) => el('option', { value: o.value ?? o, selected: (o.value ?? o) === value, text: o.label ?? o })));
  return node;
}
