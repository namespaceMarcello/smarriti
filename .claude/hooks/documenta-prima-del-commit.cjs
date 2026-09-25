#!/usr/bin/env node
const { execFileSync } = require('node:child_process')
let dati = ''
process.stdin.on('data', (c) => (dati += c))
process.stdin.on('end', () => {
  let cmd = ''
  try { cmd = JSON.parse(dati || '{}').tool_input?.command || '' } catch { process.exit(0) }
  if (!/\bgit\b[\s\S]*\bcommit\b/.test(cmd)) process.exit(0)
  let staged = []
  try {
    staged = execFileSync('git', ['diff', '--cached', '--name-only'], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] })
      .split('\n').map((r) => r.trim()).filter(Boolean)
  } catch { process.exit(0) }
  if (!staged.length) process.exit(0)
  // ADATTA: le cartelle di codice di questo repo (aggiorna quando nasce il codice)
  const tocca = staged.some((f) => /^(src|sim|app)\//.test(f))
  if (!tocca || staged.includes('docs/archivio/FATTO.md')) process.exit(0)
  console.error(
    'Questo commit tocca il codice ma non documenta niente.\n' +
    'Aggiungi in coda a docs/archivio/FATTO.md una voce di 2-5 righe:\n' +
    '  ### <data> — <titolo>\n  cosa e\' stato implementato, e come si prova.\n' +
    'Aggiorna docs/STATO.md SOLO se e\' cambiata una decisione, un debito o un\n' +
    'prossimo passo (cancella la voce fatta, non aggiungerne una accanto).\n' +
    'Poi metti in stage e rifai il commit.\n' +
    'File nel commit: ' + staged.join(', ')
  )
  process.exit(2)
})
