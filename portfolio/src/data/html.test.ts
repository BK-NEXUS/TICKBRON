import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'

const html = readFileSync('index.html', 'utf8')

describe('index.html metadata', () => {
  it('has a description and a favicon', () => {
    expect(html).toMatch(/<meta name="description" content="[^"]{40,}"/)
    expect(html).toMatch(/<link rel="icon" href="\/favicon\.svg"/)
  })

  it('has Open Graph tags for link previews', () => {
    for (const tag of ['og:title', 'og:description', 'og:type']) {
      expect(html).toContain(`property="${tag}"`)
    }
  })

  it('sets a theme color for each color scheme', () => {
    expect(html).toContain('name="theme-color" content="#04060a"')
    expect(html).toContain('name="theme-color" content="#ffffff"')
  })
})
