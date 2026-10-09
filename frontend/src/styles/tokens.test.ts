import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const read = (file: string) => readFileSync(resolve(__dirname, file), 'utf-8')
const tokensCss = read('tokens.css')
const indexCss = read('index.css')

const declared = new Map<string, string>()
for (const [, name, value] of tokensCss.matchAll(/^\s*(--[\w-]+):\s*([^;]+);/gm)) {
  if (!declared.has(name)) declared.set(name, value.replace(/\/\*.*?\*\//g, '').trim())
}

function token(name: string): string {
  const value = declared.get(name)
  if (value === undefined) throw new Error(`Missing token ${name}`)
  const alias = value.match(/^var\((--[\w-]+)\)$/)
  return alias ? token(alias[1]) : value
}

function luminance(hex: string): number {
  const [r, g, b] = [1, 3, 5].map((i) => {
    const channel = parseInt(hex.slice(i, i + 2), 16) / 255
    return channel <= 0.03928 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4
  })
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}

function contrast(foreground: string, background: string): number {
  const [lighter, darker] = [luminance(token(foreground)), luminance(token(background))].sort((a, b) => b - a)
  return (lighter + 0.05) / (darker + 0.05)
}

describe('design tokens', () => {
  describe('text contrast (WCAG AA, >= 4.5)', () => {
    const textPairs: Array<[string, string]> = [
      ['--color-text-primary', '--color-background'],
      ['--color-text-primary', '--color-background-alt'],
      ['--color-text-secondary', '--color-background'],
      ['--color-text-secondary', '--color-background-alt'],
      ['--color-text-tertiary', '--color-background'],
      ['--color-text-tertiary', '--color-background-alt'],
      ['--color-on-primary', '--color-primary'],
      ['--color-on-primary', '--color-primary-hover'],
      ['--color-gold-dark', '--color-background'],
      ['--color-gold-dark', '--color-background-alt'],
      ['--color-error', '--color-background'],
      ['--color-success', '--color-background'],
      ['--color-warning', '--color-background'],
    ]
    it.each(textPairs)('%s on %s', (foreground, background) => {
      expect(contrast(foreground, background)).toBeGreaterThanOrEqual(4.5)
    })

    it('white text on the gold fill fails, which is why primary buttons use ink', () => {
      expect(contrast('--color-background', '--color-primary')).toBeLessThan(4.5)
    })
  })

  describe('non-text contrast (>= 3)', () => {
    const uiPairs: Array<[string, string]> = [
      ['--color-focus', '--color-background'],
      ['--color-focus', '--color-background-alt'],
      ['--color-border-control', '--color-background'],
      ['--color-border-control', '--color-background-alt'],
    ]
    it.each(uiPairs)('%s on %s', (foreground, background) => {
      expect(contrast(foreground, background)).toBeGreaterThanOrEqual(3)
    })
  })

  it('defines the radius, shadow, spacing and layout scales', () => {
    expect(['--radius-sm', '--radius-md', '--radius-lg', '--radius-xl', '--radius-pill'].map(token))
      .toEqual(['8px', '12px', '16px', '24px', '999px'])
    for (const name of ['--shadow-xs', '--shadow-sm', '--shadow-md', '--shadow-lg', '--shadow-xl', '--shadow-brand']) {
      expect(token(name)).toBeTruthy()
    }
    expect(['--spacing-xs', '--spacing-sm', '--spacing-12', '--spacing-md', '--spacing-lg', '--spacing-xl',
      '--spacing-2xl', '--spacing-3xl'].map(token)).toEqual(['4px', '8px', '12px', '16px', '24px', '32px', '48px', '64px'])
    expect(token('--container-max')).toBe('1280px')
    expect(token('--container-wide')).toBe('1440px')
  })

  it('grows the gutter with the viewport', () => {
    expect(token('--gutter')).toBe('16px')
    expect(tokensCss).toMatch(/@media \(min-width: 640px\)\s*\{\s*:root \{ --gutter: 24px; \}/)
    expect(tokensCss).toMatch(/@media \(min-width: 1024px\)\s*\{\s*:root \{ --gutter: 32px; \}/)
  })

  it('is imported before every other stylesheet', () => {
    expect(read('../main.tsx').startsWith("import './styles/tokens.css'")).toBe(true)
    expect(indexCss).not.toMatch(/^:root\s*\{/m)
  })

  it('keeps the safe-area insets on the header and the bottom navigation', () => {
    expect(indexCss).toMatch(/\.header \{[^}]*env\(safe-area-inset-top\)/)
    expect(indexCss).toMatch(/\.mobile-bottom-navigation \{[^}]*env\(safe-area-inset-bottom\)/)
    expect(read('../../index.html')).toContain('viewport-fit=cover')
  })
})

describe('container', () => {
  it('centres its content with max-width, auto inline margin and the responsive gutter', () => {
    const rule = indexCss.match(/\n\.container \{([^}]*)\}/)?.[1] ?? ''
    expect(rule).toContain('max-width: var(--container-max)')
    expect(rule).toContain('margin-inline: auto')
    expect(rule).toContain('padding-inline: var(--gutter)')
  })

  it('has a wider variant for admin tables', () => {
    expect(indexCss).toMatch(/\.container-large-desktop \{\s*max-width: var\(--container-wide\)/)
  })
})

describe('dark theme', () => {
  const mediaBlock = tokensCss.match(
    /@media \(prefers-color-scheme: dark\)\s*\{\s*:root:not\(\[data-theme='light'\]\)\s*\{([^}]*)\}\s*\}/,
  )?.[1]
  const attributeBlock = tokensCss.match(/:root\[data-theme='dark'\]\s*\{([^}]*)\}/)?.[1]
  const parse = (block: string) =>
    new Map([...block.matchAll(/^\s*(--[\w-]+):\s*([^;]+);/gm)].map(([, name, value]) => [name, value.trim()]))

  it('is defined for the system setting and for the explicit choice, with the same values', () => {
    expect(mediaBlock).toBeDefined()
    expect(attributeBlock).toBeDefined()
    expect([...parse(mediaBlock!)]).toEqual([...parse(attributeBlock!)])
  })

  it('declares color-scheme so native controls and scrollbars follow the theme', () => {
    expect(tokensCss).toMatch(/:root\s*\{[^}]*color-scheme: light/)
    expect(attributeBlock).toContain('color-scheme: dark')
  })

  const dark = () => parse(attributeBlock!)
  const resolve = (name: string): string => {
    const value = dark().get(name) ?? declared.get(name)
    if (!value) throw new Error(`Missing token ${name}`)
    const alias = value.match(/^var\((--[\w-]+)\)$/)
    return alias ? resolve(alias[1]) : value
  }
  const darkContrast = (foreground: string, background: string) => {
    const [lighter, darker] = [luminance(resolve(foreground)), luminance(resolve(background))].sort((a, b) => b - a)
    return (lighter + 0.05) / (darker + 0.05)
  }

  const textPairs: Array<[string, string]> = [
    ['--color-text-primary', '--color-background'],
    ['--color-text-primary', '--color-background-alt'],
    ['--color-text-primary', '--color-surface'],
    ['--color-text-strong', '--color-surface'],
    ['--color-text-secondary', '--color-background'],
    ['--color-text-secondary', '--color-surface'],
    ['--color-text-tertiary', '--color-background'],
    ['--color-text-tertiary', '--color-surface'],
    ['--color-pomegranate', '--color-background'],
    ['--color-pomegranate', '--color-surface'],
    ['--color-on-primary', '--color-primary'],
    ['--color-error', '--color-background'],
    ['--color-error', '--color-surface'],
    ['--color-success', '--color-background'],
    ['--color-success', '--color-surface'],
    ['--color-warning', '--color-background'],
    ['--color-warning', '--color-surface'],
  ]
  it.each(textPairs)('text %s on %s is at least 4.5:1', (foreground, background) => {
    expect(darkContrast(foreground, background)).toBeGreaterThanOrEqual(4.5)
  })

  const uiPairs: Array<[string, string]> = [
    ['--color-focus', '--color-background'],
    ['--color-focus', '--color-surface'],
    ['--color-border-control', '--color-background'],
    ['--color-border-control', '--color-surface'],
  ]
  it.each(uiPairs)('control %s on %s is at least 3:1', (foreground, background) => {
    expect(darkContrast(foreground, background)).toBeGreaterThanOrEqual(3)
  })

  it('has the new surface tokens in the light theme too', () => {
    for (const name of ['--color-surface', '--color-text-strong', '--color-saffron-solid']) {
      expect(token(name)).toBeTruthy()
    }
  })
})
