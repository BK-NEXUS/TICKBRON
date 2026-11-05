import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { SoftImage } from './SoftImage'

describe('SoftImage', () => {
  it('passes every attribute to the picture and starts not shown, so it can fade in', () => {
    render(<SoftImage src="/media/a.jpg" alt="Lobby" loading="lazy" className="property-card-photo" />)
    const image = screen.getByRole('img', { name: 'Lobby' })
    expect(image).toHaveAttribute('src', '/media/a.jpg')
    expect(image).toHaveAttribute('loading', 'lazy')
    expect(image).toHaveClass('soft-image', 'property-card-photo')
    expect(image).not.toHaveClass('is-loaded')
  })

  it('is shown once the file has loaded and still calls the caller\'s onLoad', () => {
    let called = 0
    render(<SoftImage src="/media/a.jpg" alt="Lobby" onLoad={() => { called += 1 }} />)
    const image = screen.getByRole('img', { name: 'Lobby' })
    fireEvent.load(image)
    expect(image).toHaveClass('is-loaded')
    expect(called).toBe(1)
  })

  it('is shown when the file fails too, so the alt text is never hidden behind an invisible picture', () => {
    let called = 0
    render(<SoftImage src="/media/gone.jpg" alt="Lobby" onError={() => { called += 1 }} />)
    const image = screen.getByRole('img', { name: 'Lobby' })
    fireEvent.error(image)
    expect(image).toHaveClass('is-loaded')
    expect(called).toBe(1)
  })

  it('does not fade a picture the browser already has (cached): it is shown at once', () => {
    const original = Object.getOwnPropertyDescriptor(HTMLImageElement.prototype, 'complete')
    Object.defineProperty(HTMLImageElement.prototype, 'complete', { configurable: true, get: () => true })
    try {
      render(<SoftImage src="/media/cached.jpg" alt="Cached" />)
      expect(screen.getByRole('img', { name: 'Cached' })).toHaveClass('is-loaded')
    } finally {
      if (original) Object.defineProperty(HTMLImageElement.prototype, 'complete', original)
      else delete (HTMLImageElement.prototype as unknown as Record<string, unknown>).complete
    }
  })
})
