import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

const ROOT = join(__dirname, '..')

function sourceFiles(dir: string): string[] {
  return readdirSync(dir).flatMap(name => {
    const path = join(dir, name)
    if (statSync(path).isDirectory()) return sourceFiles(path)
    return /\.(ts|tsx)$/.test(name) && !/\.test\./.test(name) ? [path] : []
  })
}

const variablesRead = new Set(
  sourceFiles(join(ROOT, 'src')).flatMap(file => readFileSync(file, 'utf8').match(/import\.meta\.env\.(VITE_[A-Z0-9_]+)/g) ?? [])
    .map(use => use.replace('import.meta.env.', '')),
)
const variablesListed = new Set(
  [...readFileSync(join(ROOT, '.env.example'), 'utf8').matchAll(/^#?\s*([A-Z][A-Z0-9_]*)=/gm)].map(match => match[1]),
)

describe('frontend/.env.example', () => {
  it('lists every VITE_ variable the code reads', () => {
    expect([...variablesRead].filter(name => !variablesListed.has(name))).toEqual([])
  })

  it('lists nothing the code does not read', () => {
    expect([...variablesListed].filter(name => !variablesRead.has(name))).toEqual([])
  })
})
