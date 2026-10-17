import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { PhotoLightbox } from './PhotoLightbox'
import { I18nProvider } from '../i18n/I18nContext'
import type { PropertyPhoto } from '../adapters/propertyAdapter'

const photo = (id: number, extra: Partial<PropertyPhoto> = {}): PropertyPhoto => ({
  id, photo: `https://media.test/${id}.jpg`, photo_type: 'exterior', is_primary: id === 1, display_order: id, ...extra,
})
const photos = [photo(1), photo(2, { caption: 'The courtyard' }), photo(3, { alt_text: 'Pool at night' })]

function renderLightbox(startIndex = 0, onClose = vi.fn(), list = photos) {
  localStorage.setItem('tickbron.language', 'en')
  render(<I18nProvider><PhotoLightbox photos={list} startIndex={startIndex} name="Hotel Alpha" onClose={onClose} /></I18nProvider>)
  return { onClose }
}

describe('PhotoLightbox', () => {
  beforeEach(() => localStorage.clear())

  it('opens as a modal dialog on the chosen photo, with a counter', () => {
    renderLightbox(1)
    const dialog = screen.getByRole('dialog', { name: 'Photos of Hotel Alpha' })
    expect(dialog).toHaveAttribute('aria-modal', 'true')
    expect(screen.getByRole('img')).toHaveAttribute('src', 'https://media.test/2.jpg')
    expect(screen.getByText('2 of 3')).toBeInTheDocument()
  })

  it('shows the caption, and uses the photo\'s alt text, else a generated one', () => {
    renderLightbox(1)
    expect(screen.getByText('The courtyard')).toBeInTheDocument()
    expect(screen.getByRole('img')).toHaveAttribute('alt', 'The courtyard')
    fireEvent.click(screen.getByRole('button', { name: 'Next image' }))
    expect(screen.getByRole('img')).toHaveAttribute('alt', 'Pool at night')
    fireEvent.click(screen.getByRole('button', { name: 'Next image' }))
    expect(screen.getByRole('img')).toHaveAttribute('alt', 'Hotel Alpha, photo 1')
  })

  it('moves between photos with the buttons and wraps around at both ends', () => {
    renderLightbox(0)
    fireEvent.click(screen.getByRole('button', { name: 'Previous image' }))
    expect(screen.getByText('3 of 3')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Next image' }))
    expect(screen.getByText('1 of 3')).toBeInTheDocument()
  })

  it('moves with the arrow keys', () => {
    renderLightbox(0)
    fireEvent.keyDown(document, { key: 'ArrowRight' })
    expect(screen.getByText('2 of 3')).toBeInTheDocument()
    fireEvent.keyDown(document, { key: 'ArrowLeft' })
    fireEvent.keyDown(document, { key: 'ArrowLeft' })
    expect(screen.getByText('3 of 3')).toBeInTheDocument()
  })

  it('closes with Escape, the close button, or a click beside the photo', () => {
    const first = renderLightbox(0)
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(first.onClose).toHaveBeenCalledTimes(1)
    fireEvent.click(screen.getByRole('button', { name: 'Close photos' }))
    expect(first.onClose).toHaveBeenCalledTimes(2)
    fireEvent.click(screen.getByTestId('lightbox-backdrop'))
    expect(first.onClose).toHaveBeenCalledTimes(3)
  })

  it('a click on the photo itself does not close it', () => {
    const { onClose } = renderLightbox(0)
    fireEvent.click(screen.getByRole('img'))
    expect(onClose).not.toHaveBeenCalled()
  })

  it('a single photo has no arrows and no counter', () => {
    renderLightbox(0, vi.fn(), [photo(1)])
    expect(screen.queryByRole('button', { name: 'Next image' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Previous image' })).toBeNull()
    expect(screen.queryByText('1 of 1')).toBeNull()
  })
})
