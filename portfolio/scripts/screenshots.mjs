import { createRequire } from 'node:module'
import { mkdirSync } from 'node:fs'

// Playwright is provided by the environment, not a project dependency.
const { chromium } = createRequire(import.meta.url)('playwright')

const URL = process.env.PREVIEW_URL ?? 'http://localhost:4173'
const OUT = process.env.OUT_DIR ?? 'screenshots'
const sizes = [
  { name: 'mobile-390', width: 390, height: 844 },
  { name: 'desktop-1440', width: 1440, height: 900 },
]

mkdirSync(OUT, { recursive: true })
const browser = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] })
let failed = false
for (const theme of ['dark', 'light'])
for (const size of sizes) {
  const page = await browser.newPage({ viewport: { width: size.width, height: size.height } })
  await page.addInitScript((t) => localStorage.setItem('theme', t), theme)
  await page.goto(URL, { waitUntil: 'networkidle' })
  await page.waitForTimeout(2500)
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)
  console.log(`${theme} ${size.name}: horizontal overflow = ${overflow}px, canvas = ${await page.locator('canvas').count()}`)
  if (overflow > 0) failed = true
  await page.screenshot({ path: `${OUT}/${theme}-${size.name}-top.png` })
  await page.screenshot({ path: `${OUT}/${theme}-${size.name}-full.png`, fullPage: true })
  await page.close()
}
await browser.close()
process.exit(failed ? 1 : 0)
