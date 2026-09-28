/**
 * Crawl: as a guest (not logged in), a hotel owner and a super-admin, open every page the
 * app links to, follow every internal link and click every button, at desktop and mobile
 * width. Fails on:
 *  - a link or button that lands on the 404 page
 *  - a dead button: clicking it changes nothing (no navigation, no DOM change, no request)
 *  - a console error / uncaught page error
 * Buttons that would change data (log out, pay, delete, cancel, approve, ...) are not clicked.
 * Needs the real local stack with seed_demo data (see playwright.config.ts).
 */
import { Page } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'
import { test, expect, loginWithPassword, DEMO, API, DESKTOP, MOBILE, SCREENSHOT_DIR } from './support'

type Role = 'guest' | 'owner' | 'admin'

interface Finding {
  role: Role
  viewport: string
  page: string
  kind: '404' | 'dead-button' | 'console' | 'pageerror'
  detail: string
}

// Clicking these changes data or ends the session; they are covered by the user flows
const UNSAFE = /log ?out|sign ?out|delete|remove|cancel|pay|approve|suspend|reject|confirm|create account|create owner account|save|submit|book now|proceed to booking|add note|update|send code|verify|retry/i

// Console noise that is not an app error (browser / dev server)
const IGNORED_CONSOLE = [/Download the React DevTools/i, /\[vite\]/i]

function isInternal(href: string) {
  return href.startsWith('/') && !href.startsWith('//') && !href.startsWith('/api/') && !href.startsWith('/media/')
}

/** Strip ids so /property/1 and /property/2 count as one page */
function pageKey(path: string) {
  return path.split('?')[0].replace(/\/\d+(?=\/|$)/g, '/:id')
}

async function isNotFound(page: Page) {
  return (await page.getByRole('heading', { name: 'Page Not Found' }).count()) > 0
}

async function settle(page: Page) {
  await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => undefined)
}

async function startPages(page: Page, role: Role): Promise<string[]> {
  const search = await (await page.request.get(`${API}/api/v1/properties/search/?destination=Tashkent`)).json()
  const propertyId = search.results?.[0]?.id
  const common = ['/', '/search?destination=Tashkent', propertyId ? `/property/${propertyId}` : '/']
  if (role === 'guest') return [...common, '/login', '/register']
  if (role === 'owner') return [...common, '/bookings', '/favorites', '/profile', '/partner']
  return [...common, '/bookings', '/favorites', '/profile', '/admin', '/admin/support', '/partner']
}

async function crawl(page: Page, role: Role, viewport: typeof DESKTOP, viewportName: string): Promise<Finding[]> {
  const findings: Finding[] = []
  let current = ''
  const record = (kind: Finding['kind'], detail: string) => {
    // Console errors count once however many pages show them; the rest once per page
    const keyOf = (k: string, p: string, d: string) => (k === 'console' || k === 'pageerror' ? `${k}|${d}` : `${k}|${pageKey(p)}|${d}`)
    const key = keyOf(kind, current, detail)
    if (!findings.some(f => keyOf(f.kind, f.page, f.detail) === key)) {
      findings.push({ role, viewport: viewportName, page: current, kind, detail })
    }
  }
  page.on('console', msg => {
    if (msg.type() === 'error' && !IGNORED_CONSOLE.some(re => re.test(msg.text()))) record('console', msg.text().slice(0, 200))
  })
  page.on('pageerror', err => record('pageerror', err.message.slice(0, 200)))

  await page.setViewportSize(viewport)
  const queue = await startPages(page, role)
  const seen = new Set<string>()
  const clickedButtons = new Set<string>()

  while (queue.length > 0) {
    const url = queue.shift()!
    if (seen.has(pageKey(url))) continue
    seen.add(pageKey(url))
    current = url

    await page.goto(url)
    await settle(page)
    if (await isNotFound(page)) {
      record('404', `page ${url}`)
      continue
    }

    // Links: every internal href goes on the queue
    const hrefs = await page.locator('a[href]').evaluateAll(links =>
      links.map(link => link.getAttribute('href') ?? ''))
    for (const href of hrefs) {
      if (isInternal(href) && !seen.has(pageKey(href))) queue.push(href)
    }

    // Buttons: click each one on a fresh load of the page
    const buttonCount = await page.locator('button:visible').count()
    for (let i = 0; i < buttonCount; i++) {
      await page.goto(url)
      await settle(page)
      const target = page.locator('button:visible').nth(i)
      if (!(await target.count())) continue
      const label = ((await target.getAttribute('aria-label')) || (await target.innerText()) || '').trim()
      const buttonKey = `${pageKey(url)}|${label}`
      if (!label || UNSAFE.test(label) || clickedButtons.has(buttonKey)) continue
      clickedButtons.add(buttonKey)
      if (!(await target.isEnabled().catch(() => false))) continue
      // Already-selected toggles/tabs, and submit buttons the browser's form validation stops, are not dead
      const inert = await target.evaluate((b: HTMLButtonElement) =>
        b.getAttribute('aria-pressed') === 'true' || b.getAttribute('aria-selected') === 'true' ||
        b.getAttribute('aria-current') !== null ||
        (b.type === 'submit' && !!b.form && !b.form.noValidate && !b.form.checkValidity()))

      const snapshot = () => page.evaluate(() => ({
        scroll: window.scrollY,
        focus: document.activeElement ? document.activeElement.outerHTML.slice(0, 200) : '',
      }))
      const before = { url: page.url(), html: await page.locator('body').innerHTML(), ...(await snapshot()) }
      let requests = 0
      const onRequest = () => { requests += 1 }
      page.on('request', onRequest)
      await target.click({ timeout: 5_000 }).catch(() => undefined)
      await page.waitForTimeout(400)
      await settle(page)
      page.off('request', onRequest)

      if (page.url() !== before.url) {
        const path = new URL(page.url()).pathname + new URL(page.url()).search
        if (await isNotFound(page)) record('404', `button "${label}" -> ${path}`)
        else if (!seen.has(pageKey(path))) queue.push(path)
      } else {
        const after = await snapshot()
        const html = await page.locator('body').innerHTML()
        const moved = after.scroll !== before.scroll || (after.focus !== before.focus && !after.focus.startsWith('<button'))
        if (!inert && requests === 0 && html === before.html && !moved) {
          record('dead-button', `button "${label}"`)
        }
        // Links that only show after the click (mobile menu, user dropdown) go on the queue too
        if (html !== before.html) {
          const opened = await page.locator('a[href]').evaluateAll(links => links.map(link => link.getAttribute('href') ?? ''))
          for (const href of opened) {
            if (isInternal(href) && !seen.has(pageKey(href))) queue.push(href)
          }
        }
      }
    }
  }
  return findings
}

for (const role of ['guest', 'owner', 'admin'] as Role[]) {
  test(`crawl as ${role}: no 404s, dead buttons or console errors`, async ({ page }) => {
    test.setTimeout(900_000)
    if (role === 'owner') await loginWithPassword(page, DEMO.owner.email, DEMO.owner.password)
    if (role === 'admin') await loginWithPassword(page, DEMO.admin.email, DEMO.admin.password)

    const findings = [
      ...(await crawl(page, role, DESKTOP, 'desktop')),
      ...(await crawl(page, role, MOBILE, 'mobile')),
    ]
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true })
    fs.writeFileSync(path.join(SCREENSHOT_DIR, `crawl-${role}.json`), JSON.stringify(findings, null, 2))
    console.log(`crawl ${role}: ${findings.length} findings\n` +
      findings.map(f => `  [${f.viewport}] ${f.kind} on ${f.page}: ${f.detail}`).join('\n'))
    expect(findings, findings.map(f => `${f.kind} on ${f.page}: ${f.detail}`).join('\n')).toEqual([])
  })
}
