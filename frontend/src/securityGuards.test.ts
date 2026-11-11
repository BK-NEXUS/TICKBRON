import { describe, it, expect } from 'vitest'
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'

/** The source files of the site (not the tests): a new line that matches one of these must be justified or rewritten. */
const SRC = __dirname
const FORBIDDEN: Record<string, RegExp> = {
  'HTML written from a string': /dangerouslySetInnerHTML|\.innerHTML\s*=|\.outerHTML\s*=|document\.write\(/,
  'eval or a function built from text': /(?<![\w.])eval\(|new Function\(/,
  'a token, password or session kept in the browser storage': /(local|session)Storage\.setItem\([^)]*(token|password|session|csrf)/i,
}

export function problemsIn(text: string): string[] {
  const lines = text.split('\n')
  const found: string[] = []
  lines.forEach((line, index) => {
    const code = line.replace(/\/\/.*$/, '')
    for (const [kind, pattern] of Object.entries(FORBIDDEN)) {
      if (pattern.test(code)) found.push(`${kind} (line ${index + 1})`)
    }
  })
  // An external link opened in a new tab must not hand the new page a handle to this one
  for (const match of text.matchAll(/<a\b[^>]*target="_blank"[^>]*>/g)) {
    if (!/rel="[^"]*noopener/.test(match[0])) found.push('a new-tab link without rel="noopener"')
  }
  return found
}

function sourceFiles(folder: string): string[] {
  return readdirSync(folder).flatMap(name => {
    const path = join(folder, name)
    if (statSync(path).isDirectory()) return name === 'test' ? [] : sourceFiles(path)
    return /\.(ts|tsx)$/.test(name) && !/\.test\.(ts|tsx)$/.test(name) ? [path] : []
  })
}

describe('security guards of the site source', () => {
  it('recognises each kind of problem', () => {
    expect(problemsIn('<div dangerouslySetInnerHTML={{ __html: text }} />')).toHaveLength(1)
    expect(problemsIn('node.innerHTML = text')).toHaveLength(1)
    expect(problemsIn('const x = eval(text)')).toHaveLength(1)
    expect(problemsIn("localStorage.setItem('authToken', token)")).toHaveLength(1)
    expect(problemsIn('<a href="https://x.test" target="_blank">x</a>')).toHaveLength(1)
  })

  it('lets safe code and comments through', () => {
    expect(problemsIn('<a href="https://x.test" target="_blank" rel="noopener noreferrer">x</a>')).toEqual([])
    expect(problemsIn("localStorage.setItem('tickbron.language', language)")).toEqual([])
    expect(problemsIn('// never use eval( here')).toEqual([])
  })

  it('finds none of them in the source files', () => {
    const offences = sourceFiles(SRC).flatMap(path =>
      problemsIn(readFileSync(path, 'utf8')).map(problem => `${path.slice(SRC.length + 1)}: ${problem}`))
    expect(offences).toEqual([])
  })
})
