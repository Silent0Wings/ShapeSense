import { note, pageHead, card, stat, stats } from '../ui.js';
import { failureLog } from '../widgets/findings.js';
import { failureGraph } from '../widgets/failure-graph.js';
import { boot } from './boot.js';

boot('failures', (main, _data, meta) => {
  const count = (state) => meta.failures.filter((f) => f.state === state).length;
  main.append(pageHead({ eyebrow: 'CRISP-DM record', title: 'Failure timeline',
    lede: 'Everything that went wrong, in the order it happened: from dropping the Quick, Draw! diamonds, through training and finding out why the results failed, to closing out. Open any failure to see where it sits in the CRISP-DM cycle.',
    chips: [`${meta.failures.length} failures recorded`, 'kept beside the closed iterations'] }));
  main.append(card('Where things stand', stats(stat('Overcome', count('Overcome')), stat('Partly', count('Partly')), stat('Still open', count('Still open')), stat('Verdict stands', count('Verdict stands'))),
    note('Smaller build issues are listed in plan_issues.md.')));
  main.append(card('The timeline as a graph', failureGraph(meta.failures, meta.phases),
    note('Left to right is the order things happened, not calendar time, because the record has no dates. The line follows the project from one failure to the next, and the number is the failure\'s ID. Move the slider or select a mark to read that point.')));
  main.append(failureLog(meta.failures, meta.phases));
});
