import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const css = readFileSync(resolve(__dirname, 'index.css'), 'utf-8')
const rule = (selector: string) => css.match(new RegExp(`\n${selector.replace(/[.[\]()]/g, '\$&')} \{([^}]*)\}`))?.[1] ?? ''

describe('button styles', () => {
  it('are pills and the primary button casts a brand-coloured shadow', () => {
    expect(rule('.btn')).toContain('border-radius: var(--radius-pill)')
    expect(rule('.btn-primary')).toContain('box-shadow: var(--shadow-brand)')
    expect(rule('.btn-primary')).toContain('color: var(--color-on-primary)')
  })

  it('keep a visible 2px focus ring with an offset', () => {
    expect(rule('.btn:focus-visible')).toMatch(/outline: 2px solid var\(--color-focus\)/)
    expect(rule('.btn:focus-visible')).toContain('outline-offset: 2px')
  })

  it('give every size a 44px target on touch screens', () => {
    expect(css).toMatch(/@media \(pointer: coarse\) \{\s*\.btn:not\(\.btn-link\) \{\s*--btn-height: 44px;/)
  })

  it('stop moving with prefers-reduced-motion', () => {
    expect(css).toMatch(/@media \(prefers-reduced-motion: reduce\) \{\s*\.btn \{\s*transition: none;/)
  })

  it('give the danger variant its own red, not the brand colour', () => {
    expect(rule('.btn-danger')).toContain('background-color: var(--color-error)')
    expect(rule('.btn-danger')).toContain('box-shadow: var(--shadow-danger)')
  })
})
