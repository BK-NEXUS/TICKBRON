import { describe, it, expect } from 'vitest'
import { imageFileError, MAX_IMAGE_BYTES } from './imageFile'

const file = (name: string, type: string, size = 10) => new File([new Uint8Array(size)], name, { type })

describe('imageFileError', () => {
  it('accepts jpg, jpeg, png, webp and gif up to 10 MB', () => {
    for (const [name, type] of [['a.jpg', 'image/jpeg'], ['a.jpeg', 'image/jpeg'], ['a.PNG', 'image/png'], ['a.webp', 'image/webp'], ['a.gif', 'image/gif']]) {
      expect(imageFileError(file(name, type))).toBeNull()
    }
    expect(imageFileError(file('big.png', 'image/png', MAX_IMAGE_BYTES))).toBeNull()
  })

  it('names the problem: wrong type or too large', () => {
    expect(imageFileError(file('a.bmp', 'image/bmp'))).toBe('geoAdmin.errImageType')
    expect(imageFileError(file('a.png', 'application/pdf'))).toBe('geoAdmin.errImageType')
    expect(imageFileError(file('big.png', 'image/png', MAX_IMAGE_BYTES + 1))).toBe('geoAdmin.errImageSize')
  })
})
