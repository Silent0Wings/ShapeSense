// Every page starts here: navigation, its data bundle, then its own render.
import { get, page } from '../api.js';
import { mountNav } from '../nav.js';
import { errorBox } from '../ui.js';
import { pageFindings } from '../widgets/findings.js';

export async function boot(name, render) {
  mountNav();
  const main = document.querySelector('main');
  try {
    const [data, meta] = await Promise.all([page(name), get('/api/meta')]);
    await render(main, data, meta);
    const findings = pageFindings(name, meta.iterations);
    if (findings) main.append(findings);
  } catch (error) {
    main.replaceChildren(errorBox(error));
  }
}

export const ARM_SERIES = [
  { key: 'A0', label: 'Real only (A0)', color: 'var(--series-1)' },
  { key: 'A1', label: 'Real + augmented (A1)', color: 'var(--series-2)' },
  { key: 'B', label: 'Real + synthetic (B)', color: 'var(--series-3)' },
  { key: 'A2', label: 'Full mix (A2)', color: 'var(--series-4)' },
  { key: 'P', label: 'Synthetic pretraining (P)', color: 'var(--series-5)' },
];
