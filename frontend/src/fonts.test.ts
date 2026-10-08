import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

// E2E BUG 10: the CSP (style-src/font-src 'self') blocked the Google Fonts stylesheet,
// so PT Sans / PT Serif never loaded. The fonts are bundled with the app instead.
const read = (path: string) => readFileSync(resolve(__dirname, path), 'utf-8')

describe('brand fonts', () => {
  it('are not loaded from Google Fonts', () => {
    expect(read('styles/index.css')).not.toContain('fonts.googleapis.com')
    expect(read('../index.html')).not.toContain('fonts.googleapis.com')
  })

  it('are bundled from @fontsource (served from the same origin)', () => {
    const main = read('main.tsx')
    for (const font of ['@fontsource/pt-sans/400.css', '@fontsource/pt-sans/700.css',
      '@fontsource/pt-serif/400.css', '@fontsource/pt-serif/700.css']) {
      expect(main).toContain(`import '${font}'`)
    }
    const pkg = JSON.parse(read('../package.json'))
    expect(pkg.dependencies).toHaveProperty('@fontsource/pt-sans')
    expect(pkg.dependencies).toHaveProperty('@fontsource/pt-serif')
  })

  it('keep the font-family tokens pointing at PT Sans / PT Serif', () => {
    const css = read('styles/tokens.css')
    expect(css).toMatch(/--font-family-heading: 'PT Serif'/)
    expect(css).toMatch(/--font-family-body: 'PT Sans'/)
  })
})
