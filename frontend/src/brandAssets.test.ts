import { describe, it, expect } from 'vitest'
import { existsSync, readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'

const BRAND_DIR = join(__dirname, '..', 'public', 'brand')
const LOGOS = ['tickbron-logo.webp', 'tickbron-logo-dark.webp', 'tickbron-mark.webp', 'tickbron-mark-dark.webp']

/** Width, height and the alpha flag of a WebP file (lossy "VP8 " with ALPH or "VP8X" with the alpha bit). */
function webpInfo(file: string) {
  const bytes = readFileSync(join(BRAND_DIR, file))
  expect(bytes.subarray(0, 4).toString('ascii')).toBe('RIFF')
  expect(bytes.subarray(8, 12).toString('ascii')).toBe('WEBP')
  expect(bytes.subarray(12, 16).toString('ascii'), `${file} must carry an alpha channel (VP8X)`).toBe('VP8X')
  return { alpha: (bytes[20] & 0x10) !== 0, width: 1 + bytes.readUIntLE(24, 3), height: 1 + bytes.readUIntLE(27, 3) }
}

describe('brand files', () => {
  it.each(LOGOS)('%s is a transparent WebP of a sensible size', (file) => {
    const { alpha, width } = webpInfo(file)

    expect(alpha).toBe(true)
    expect(width).toBeGreaterThanOrEqual(400)
    expect(statSync(join(BRAND_DIR, file)).size).toBeLessThan(250_000)
  })

  it('has a wide symbol-only file and a lockup that also holds the name', () => {
    const lockup = webpInfo('tickbron-logo.webp')
    const mark = webpInfo('tickbron-mark.webp')

    expect(mark.width / mark.height).toBeGreaterThan(1.4)
    expect(lockup.height / lockup.width).toBeGreaterThan(mark.height / mark.width)
  })

  it('no longer ships the paper-background JPG to browsers', () => {
    expect(existsSync(join(BRAND_DIR, 'tickbron-logo.jpg'))).toBe(false)
  })

  it('keeps the icons the page head points to', () => {
    const html = readFileSync(join(__dirname, '..', 'index.html'), 'utf8')

    for (const file of ['favicon.ico', 'favicon-32.png', 'apple-touch-icon.png']) {
      expect(html).toContain(`/brand/${file}`)
      expect(existsSync(join(BRAND_DIR, file))).toBe(true)
    }
  })
})
