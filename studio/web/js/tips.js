// Tooltips everywhere: tags elements from the glossary, shows on hover, focus or tap.
import { tipFor } from './glossary.js';

const KEYED = [
  ['#nav nav a', (e) => e.textContent], ['button', (e) => e.textContent], ['th', (e) => e.textContent],
  ['h2', (e) => e.textContent], ['h3', (e) => e.textContent], ['.stat', (e) => e.querySelector('.stat-label').textContent],
  ['.slider', (e) => e.querySelector('span').textContent], ['.label-chip', (e) => e.textContent], ['.legend span', (e) => e.textContent],
  ['a.node', (e) => e.getAttribute('aria-label').split(':')[0]], ['.badge', (e) => e.textContent.slice(1)],
];

function tag() {
  for (const [selector, read] of KEYED) {
    for (const node of document.querySelectorAll(`${selector}:not([data-tip])`)) {
      const tip = tipFor(read(node));
      if (tip) node.setAttribute('data-tip', tip);
    }
  }
}

export function mountTips() {
  const bubble = document.createElement('div');
  bubble.className = 'tip'; bubble.setAttribute('role', 'tooltip'); bubble.hidden = true;
  document.body.append(bubble);
  let current = null;

  function show(target) {
    current = target;
    bubble.textContent = target.getAttribute('data-tip');
    bubble.hidden = false;
    const box = target.getBoundingClientRect(); const tip = bubble.getBoundingClientRect();
    const left = Math.max(8, Math.min(box.left + box.width / 2 - tip.width / 2, innerWidth - tip.width - 8));
    const top = box.top - tip.height - 8 >= 4 ? box.top - tip.height - 8 : box.bottom + 8;
    bubble.style.left = `${left}px`; bubble.style.top = `${top}px`;
  }
  function hide() { current = null; bubble.hidden = true; }
  const find = (node) => (node instanceof Element ? node.closest('[data-tip]') : null);

  document.addEventListener('pointerover', (e) => { const t = find(e.target); if (t && t !== current) show(t); else if (!t) hide(); });
  document.addEventListener('pointerdown', (e) => { const t = find(e.target); if (t) show(t); else hide(); });
  document.addEventListener('focusin', (e) => { const t = find(e.target); if (t && e.target.matches(':focus-visible')) show(t); });
  document.addEventListener('focusout', hide);
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') hide(); });
  window.addEventListener('scroll', hide, { passive: true, capture: true });

  let queued = false;
  new MutationObserver(() => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => { queued = false; tag(); });
  }).observe(document.body, { childList: true, subtree: true });
  tag();
}
