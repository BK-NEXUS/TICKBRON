/**
 * Draws the favicon files from public/brand/favicon.svg with the browser that Playwright already
 * uses for the E2E tests: favicon-32.png, apple-touch-icon.png (180px) and favicon.ico (16, 32, 48px).
 *
 * Run from frontend/ after tools/make_logo_svg.py:  node tools/render_icons.mjs
 * (set CHROMIUM_PATH to use a browser that is not Playwright's own)
 */
import { chromium } from 'playwright-core'
import { readFileSync, writeFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const BRAND_DIR = join(dirname(fileURLToPath(import.meta.url)), '..', 'public', 'brand')
const svg = readFileSync(join(BRAND_DIR, 'favicon.svg'), 'utf8')

/** An .ico file that holds PNG images (supported by every current browser). */
function ico(images) {
  const header = Buffer.alloc(6)
  header.writeUInt16LE(1, 2)
  header.writeUInt16LE(images.length, 4)
  let offset = 6 + images.length * 16
  const entries = images.map(({ size, png }) => {
    const entry = Buffer.alloc(16)
    entry.writeUInt8(size, 0)
    entry.writeUInt8(size, 1)
    entry.writeUInt16LE(1, 4)
    entry.writeUInt16LE(32, 6)
    entry.writeUInt32LE(png.length, 8)
    entry.writeUInt32LE(offset, 12)
    offset += png.length
    return entry
  })
  return Buffer.concat([header, ...entries, ...images.map(({ png }) => png)])
}

const browser = await chromium.launch(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {})
const page = await browser.newPage()
async function render(size, source = svg) {
  await page.setViewportSize({ width: size, height: size })
  await page.setContent(`<body style="margin:0;background:transparent">${source.replace('<svg ', `<svg width="${size}" height="${size}" `)}</body>`)
  return page.screenshot({ omitBackground: true, clip: { x: 0, y: 0, width: size, height: size } })
}

writeFileSync(join(BRAND_DIR, 'favicon-32.png'), await render(32))
// iOS fills transparent corners with black and rounds the icon itself, so the touch icon is a plain square
writeFileSync(join(BRAND_DIR, 'apple-touch-icon.png'), await render(180, svg.replace('rx="18"', 'rx="0"')))
writeFileSync(join(BRAND_DIR, 'favicon.ico'), ico(await Promise.all([16, 32, 48].map(async (size) => ({ size, png: await render(size) })))))
await browser.close()
console.log('favicon-32.png, apple-touch-icon.png, favicon.ico written')
