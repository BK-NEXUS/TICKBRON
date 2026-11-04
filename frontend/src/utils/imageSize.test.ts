import { describe, it, expect, vi, afterEach } from 'vitest'
import { readImageSize } from './imageSize'

const file = new File(['x'], 'a.jpg', { type: 'image/jpeg' })

describe('readImageSize', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('reads the size without a blob address, which the page policy may refuse for images', async () => {
    const close = vi.fn()
    vi.stubGlobal('createImageBitmap', vi.fn().mockResolvedValue({ width: 1600, height: 1067, close }))
    const createObjectURL = vi.fn()
    vi.stubGlobal('URL', Object.assign(URL, { createObjectURL }))

    expect(await readImageSize(file)).toEqual({ width: 1600, height: 1067 })
    expect(close).toHaveBeenCalled()
    expect(createObjectURL).not.toHaveBeenCalled()
  })

  it('is null when the browser cannot decode the picture', async () => {
    vi.stubGlobal('createImageBitmap', vi.fn().mockRejectedValue(new Error('broken')))
    expect(await readImageSize(file)).toBeNull()
  })

  it('falls back to an image element in a browser without createImageBitmap', async () => {
    vi.stubGlobal('createImageBitmap', undefined)
    vi.stubGlobal('URL', Object.assign(URL, { createObjectURL: vi.fn(() => 'blob:x'), revokeObjectURL: vi.fn() }))
    class FakeImage {
      naturalWidth = 1200
      naturalHeight = 800
      onload: (() => void) | null = null
      onerror: (() => void) | null = null
      set src(_value: string) { queueMicrotask(() => this.onload?.()) }
    }
    vi.stubGlobal('Image', FakeImage)

    expect(await readImageSize(file)).toEqual({ width: 1200, height: 800 })
  })
})
