import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const css = readFileSync(resolve(__dirname, 'index.css'), 'utf-8')

describe('brand logo styles', () => {
  it('hides the light-ink twin until a dark theme asks for it', () => {
    expect(css).toMatch(/\.brand-logo--dark \{\s*display: none;/)
  })

  it('swaps the artwork in both dark contexts: the system setting and the manual toggle', () => {
    const system = css.match(/@media \(prefers-color-scheme: dark\) \{\s*:root:not\(\[data-theme='light'\]\) \.brand-logo:not\(\.brand-logo--dark\) \{\s*display: none;[\s\S]*?:root:not\(\[data-theme='light'\]\) \.brand-logo--dark \{\s*display: block;/)
    const manual = css.match(/:root\[data-theme='dark'\] \.brand-logo:not\(\.brand-logo--dark\) \{\s*display: none;[\s\S]*?:root\[data-theme='dark'\] \.brand-logo--dark \{\s*display: block;/)

    expect(system).not.toBeNull()
    expect(manual).not.toBeNull()
  })

  it('sizes the header symbol by height, since it is wider than tall', () => {
    expect(css).toMatch(/\.brand-logo--header \{[^}]*height: 36px;[^}]*width: auto;/)
  })
})
