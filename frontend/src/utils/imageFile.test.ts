import { describe, it, expect, vi, beforeEach } from 'vitest'
import { imageFileError, imageProblem, MAX_IMAGE_BYTES } from './imageFile'
import { readImageSize } from './imageSize'

vi.mock('./imageSize', () => ({ readImageSize: vi.fn() }))
const sizeOf = vi.mocked(readImageSize)

const file = (name: string, type: string, size = 10) => new File([new Uint8Array(size)], name, { type })

describe('imageFileError', () => {
  it('accepts jpg, jpeg, png and webp up to 10 MB', () => {
    for (const [name, type] of [['a.jpg', 'image/jpeg'], ['a.jpeg', 'image/jpeg'], ['a.PNG', 'image/png'], ['a.webp', 'image/webp']]) {
      expect(imageFileError(file(name, type))).toBeNull()
    }
    expect(imageFileError(file('big.png', 'image/png', MAX_IMAGE_BYTES))).toBeNull()
  })

  it('names the problem: wrong type or too large', () => {
    expect(imageFileError(file('a.bmp', 'image/bmp'))).toBe('geoAdmin.errImageType')
    expect(imageFileError(file('a.gif', 'image/gif'))).toBe('geoAdmin.errImageType')
    expect(imageFileError(file('a.png', 'application/pdf'))).toBe('geoAdmin.errImageType')
    expect(imageFileError(file('big.png', 'image/png', MAX_IMAGE_BYTES + 1))).toBe('geoAdmin.errImageSize')
  })
})

describe('imageProblem', () => {
  beforeEach(() => sizeOf.mockReset())

  it('is null for a picture of a good size', async () => {
    sizeOf.mockResolvedValue({ width: 1600, height: 1067 })
    expect(await imageProblem(file('a.jpg', 'image/jpeg'), 'hotel')).toBeNull()
  })

  it('names the size problem of a picture that is too small or the wrong shape', async () => {
    sizeOf.mockResolvedValue({ width: 800, height: 500 })
    expect((await imageProblem(file('a.jpg', 'image/jpeg'), 'hotel'))?.key).toBe('image.errTooSmall')
    sizeOf.mockResolvedValue({ width: 1200, height: 1800 })
    expect((await imageProblem(file('a.jpg', 'image/jpeg'), 'hotel'))?.key).toBe('image.errShape')
  })

  it('reports the type or the file size first, without reading the picture', async () => {
    expect(await imageProblem(file('a.gif', 'image/gif'), 'hotel')).toEqual({ key: 'geoAdmin.errImageType' })
    expect(await imageProblem(file('big.png', 'image/png', MAX_IMAGE_BYTES + 1), 'hotel')).toEqual({ key: 'geoAdmin.errImageSize' })
    expect(sizeOf).not.toHaveBeenCalled()
  })

  it('lets the server decide when the browser cannot read the picture', async () => {
    sizeOf.mockResolvedValue(null)
    expect(await imageProblem(file('a.jpg', 'image/jpeg'), 'hotel')).toBeNull()
  })
})
