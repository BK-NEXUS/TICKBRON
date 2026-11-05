import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { RoomPhotoQueue } from './RoomPhotoQueue'
import { I18nProvider } from '../i18n/I18nContext'
import { readImageSize } from '../utils/imageSize'

vi.mock('../utils/imageSize', () => ({ readImageSize: vi.fn() }))
const sizeOf = vi.mocked(readImageSize)
const file = (name: string) => new File(['x'], name, { type: 'image/jpeg' })

function open(files: File[] = []) {
  localStorage.setItem('tickbron.language', 'en')
  const onChange = vi.fn()
  render(<I18nProvider><RoomPhotoQueue files={files} onChange={onChange} max={20} /></I18nProvider>)
  return { onChange }
}

describe('RoomPhotoQueue', () => {
  beforeEach(() => {
    localStorage.clear()
    sizeOf.mockReset()
  })

  it('writes the size to use for a room photo, in pixels', () => {
    open()
    const hint = screen.getByTestId('image-requirements')
    expect(hint).toHaveTextContent('1600 × 1067 px (3:2)')
    expect(hint).toHaveTextContent('1200 × 800 px')
  })

  it('queues a photo of a good size', async () => {
    sizeOf.mockResolvedValue({ width: 1600, height: 1067 })
    const { onChange } = open()
    const good = file('good.jpg')
    fireEvent.change(screen.getByLabelText('Add photos'), { target: { files: [good] } })
    await waitFor(() => expect(onChange).toHaveBeenCalledWith([good]))
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('does not queue a photo that is too small, and says so with the size to use', async () => {
    sizeOf.mockResolvedValue({ width: 900, height: 600 })
    const { onChange } = open()
    fireEvent.change(screen.getByLabelText('Add photos'), { target: { files: [file('small.jpg')] } })
    expect(await screen.findByRole('alert', {}, { timeout: 4000 })).toHaveTextContent('small.jpg: The picture is too small (900 × 600 px). Use at least 1200 × 800 px')
    expect(onChange).not.toHaveBeenCalled()
  })

  it('does not queue a gif', async () => {
    const { onChange } = open()
    fireEvent.change(screen.getByLabelText('Add photos'), { target: { files: [new File(['x'], 'a.gif', { type: 'image/gif' })] } })
    expect(await screen.findByRole('alert', {}, { timeout: 4000 })).toHaveTextContent('a.gif: Use a JPG, PNG or WebP picture.')
    expect(onChange).not.toHaveBeenCalled()
  })
})
