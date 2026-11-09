// The site navigation and theme switch, shared by every page.
import { mountTips } from './tips.js';
import { el } from './ui.js';

const LINKS = [
  { group: 'Overview', items: [['index.html', 'CRISP-DM cycle'], ['business.html', 'Business understanding'], ['iteration1.html', 'Iteration 1 results'], ['failures.html', 'Failure timeline'], ['changes.html', 'Changes by CRISP-DM step'], ['robustness.html', 'Robustness check']] },
  { group: 'Pipeline stages', items: [
    ['stage0.html', '0 · Infrastructure'], ['stage1.html', '1 · Data freeze'], ['stage2.html', '2 · Augmentation'],
    ['stage3.html', '3 · Synthetic generator'], ['stage4.html', '4 · Training'], ['stage5.html', '5 · Evaluation'],
    ['stage6.html', '6 · Report and export'] ] },
  { group: 'Try it', items: [['live.html', 'Draw and predict']] },
];

function storedTheme() { try { return localStorage.getItem('studio-theme'); } catch { return null; } }
function storeTheme(value) { try { localStorage.setItem('studio-theme', value); } catch { /* per-viewer only */ } }

function applyTheme(theme) {
  if (theme) document.documentElement.dataset.theme = theme;
  else delete document.documentElement.dataset.theme;
}

function themeButton() {
  const next = () => (document.documentElement.dataset.theme
    || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')) === 'dark' ? 'light' : 'dark';
  const button = el('button', { class: 'ghost', type: 'button', onclick: () => {
    const theme = next(); applyTheme(theme); storeTheme(theme); button.textContent = label();
  } });
  const label = () => (next() === 'dark' ? 'Dark theme' : 'Light theme');
  button.textContent = label();
  return button;
}

export function mountNav() {
  applyTheme(storedTheme());
  const file = location.pathname.split('/').pop() || 'index.html';
  const here = file === 'failure.html' ? 'failures.html' : file;
  const groups = LINKS.map(({ group, items }) => el('div', { class: 'nav-group' },
    el('p', { class: 'nav-title', text: group }),
    items.map(([href, text]) => el('a', { href, 'aria-current': href === here ? 'page' : null, text }))));
  document.querySelector('#nav').append(
    el('a', { class: 'brand', href: 'index.html' }, 'ShapeSense', el('span', { text: 'Studio' })),
    el('nav', { 'aria-label': 'Pages' }, groups), el('div', { class: 'nav-foot' }, themeButton()));
  mountTips();
}
