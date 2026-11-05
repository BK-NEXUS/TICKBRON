import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ImageRequirements } from './ImageRequirements'
import { I18nProvider } from '../i18n/I18nContext'

function show(kind: 'hotel' | 'room' | 'ad' | 'place', language = 'en') {
  localStorage.setItem('tickbron.language', language)
  render(<I18nProvider><ImageRequirements kind={kind} /></I18nProvider>)
  return screen.getByTestId('image-requirements')
}

describe('ImageRequirements', () => {
  beforeEach(() => localStorage.clear())

  it.each([
    ['hotel', ['1600 × 1067 px (3:2)', '1200 × 800 px', '4:3', '16:9']],
    ['room', ['1600 × 1067 px (3:2)', '1200 × 800 px', '4:3', '16:9']],
    ['ad', ['1920 × 720 px (8:3)', '1600 × 600 px', '16:9', '16:5']],
    ['place', ['1200 × 900 px (4:3)', '800 × 600 px', '6:5', '9:5']],
  ] as const)('writes the pixel sizes of a %s picture', (kind, parts) => {
    const text = show(kind).textContent ?? ''
    for (const part of parts) expect(text).toContain(part)
    expect(text).toContain('JPG, PNG or WebP, up to 10 MB')
  })

  it.each(['uz', 'ru'])('says it in %s with the same numbers', language => {
    const text = show('ad', language).textContent ?? ''
    expect(text).toContain('1920 × 720 px')
    expect(text).toContain('1600 × 600 px')
    expect(text).not.toContain('Best size')
  })
})
