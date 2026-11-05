import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

// Git on Windows checks files out with CRLF; the patterns below look for "\n}\n"
const css = (file: string) => readFileSync(resolve(__dirname, file), 'utf-8').replace(/\r\n/g, '\n')
const index = css('index.css')
const refresh = css('refresh.css')
const all = `${index}\n${refresh}`

/** The text of every `@media <query> { ... }` block whose query contains `needle` (blocks end with a "}" in column 0) */
function mediaBlocks(source: string, needle: string): string[] {
  return [...source.matchAll(/@media ([^{]*)\{([\s\S]*?)\n\}\n/g)].filter(match => match[1].includes(needle)).map(match => match[2])
}

describe('motion respects the visitor\'s setting', () => {
  it('the skeleton shimmer only runs when motion is allowed', () => {
    const outside = all.replace(/@media \(prefers-reduced-motion: no-preference\) \{[\s\S]*?\n\}\n/g, '')
    expect(outside).not.toMatch(/\.skeleton::after \{[^}]*animation:/)
    expect(mediaBlocks(all, 'prefers-reduced-motion: no-preference').join('\n')).toMatch(/\.skeleton::after \{[^}]*animation:/)
  })

  it('a picture fades in only when motion is allowed and is plainly shown otherwise', () => {
    const outside = all.replace(/@media \(prefers-reduced-motion: no-preference\) \{[\s\S]*?\n\}\n/g, '')
    expect(outside).not.toMatch(/\.soft-image[^{]*\{[^}]*opacity: 0/)
    const motion = mediaBlocks(all, 'prefers-reduced-motion: no-preference').join('\n')
    expect(motion).toMatch(/\.soft-image:not\(\.is-loaded\) \{[^}]*opacity: 0/)
    expect(motion).toMatch(/\.soft-image \{[^}]*transition: opacity/)
  })
})

describe('the failure screen', () => {
  it('keeps the red for the icon and writes the title and the message in the normal text colours', () => {
    expect(refresh).toMatch(/\.empty-state\.error-state \.empty-state-title \{[^}]*color: var\(--color-text-primary\)/)
    expect(refresh).toMatch(/\.empty-state\.error-state \.empty-state-message \{[^}]*color: var\(--color-text-secondary\)/)
    expect(refresh).toMatch(/\.empty-state-icon--error \{[^}]*color: var\(--color-error\)/)
  })
})

describe('the hotel page on a phone', () => {
  it('keeps the price and the book button in view at the bottom, above the bottom menu', () => {
    const phone = mediaBlocks(all, 'max-width').join('\n')
    expect(phone).toMatch(/\.property-detail-sidebar \{[^}]*position: sticky;[^}]*bottom: calc\(var\(--mobile-nav-height\)/)
  })

  it('lays the page out as one column there, because a grid item sticks only inside its own cell', () => {
    const phone = mediaBlocks(all, 'max-width: 767px').join(' ')
    expect(phone).toMatch(/\.property-detail-content \{[^}]*display: flex;[^}]*flex-direction: column/)
  })

  it('defines the height of the bottom menu once, for the bar to sit above', () => {
    expect(all).toMatch(/--mobile-nav-height: \d+px/)
  })
})
