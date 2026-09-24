import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import ts from 'typescript'

// vite build strips types without checking them; a type error only fails the build if tsc runs first
describe('build script', () => {
  it('type-checks before bundling', () => {
    const pkg = JSON.parse(readFileSync(resolve(__dirname, '../package.json'), 'utf-8'))

    expect(pkg.scripts.build).toMatch(/^tsc && vite build$/)
  })

  it('type-checks App.tsx and every page it lazy-loads', () => {
    // tsconfig.json has comments, so it is read with TypeScript's own parser
    const tsconfig = ts.readConfigFile(resolve(__dirname, '../tsconfig.json'), ts.sys.readFile).config

    expect(tsconfig.include).toContain('src')
    expect(tsconfig.exclude).not.toContain('src/App.tsx')
  })
})
