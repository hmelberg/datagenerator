import { readFileSync } from 'node:fs';

const html = readFileSync(new URL('../datagenerator.html', import.meta.url), 'utf8');
const blocks = [...html.matchAll(/<script data-node-testable>([\s\S]*?)<\/script>/g)].map(m => m[1]);
if (!blocks.length) { console.error('FEIL: fant ingen <script data-node-testable>-blokker'); process.exit(1); }

const window = {};
new Function('window', blocks.join('\n'))(window);
const DG = window.DG;

// Ekte RandExp lastes bare i nettleser; node bruker en stub som bare
// verifiserer at regex-generatoren er koblet riktig.
DG.regexLib = class { constructor(re) { this.re = re; } gen() { return 'X1'; } };

const res = DG.runTests();
for (const f of res.failures) console.error('FEIL: ' + f.name + ' — ' + f.message);
console.log(res.failed ? `${res.failed} av ${res.total} tester FEILET` : `OK: ${res.total} tester besto`);
process.exit(res.failed ? 1 : 0);
