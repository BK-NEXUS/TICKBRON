import { describe, it, expect, vi, afterEach } from 'vitest'
import { existsSync, readFileSync } from 'node:fs'
import { join } from 'node:path'

const PUBLIC_DIR = join(__dirname, '..', 'public')
const read = (file: string) => readFileSync(join(PUBLIC_DIR, file), 'utf8')

/** Width and height from the header of a PNG file */
function pngSize(file: string) {
  const bytes = readFileSync(join(PUBLIC_DIR, file))
  expect(bytes.subarray(1, 4).toString('ascii'), `${file} must be a PNG`).toBe('PNG')
  return { width: bytes.readUInt32BE(16), height: bytes.readUInt32BE(20) }
}

interface ManifestIcon { src: string; sizes: string; type: string; purpose?: string }

describe('the web app manifest (what makes the site installable and the Android app possible)', () => {
  const manifest = JSON.parse(read('manifest.webmanifest')) as Record<string, unknown> & { icons: ManifestIcon[] }

  it('is linked from the page head', () => {
    const html = readFileSync(join(__dirname, '..', 'index.html'), 'utf8')
    expect(html).toMatch(/<link rel="manifest" href="\/manifest\.webmanifest"/)
  })

  it('names the app TICKBRON and opens it as an app on the whole site', () => {
    expect(manifest.name).toBe('TICKBRON')
    expect(manifest.short_name).toBe('TICKBRON')
    expect(manifest.start_url).toBe('/')
    expect(manifest.scope).toBe('/')
    expect(manifest.display).toBe('standalone')
  })

  it('uses the cream of the site for the bars and the splash screen', () => {
    expect(manifest.theme_color).toBe('#F2EDE7')
    expect(manifest.background_color).toBe('#F2EDE7')
  })

  it('has ordinary 192 and 512 icons and a maskable 512 icon, and each file really has that size', () => {
    const find = (sizes: string, purpose: string) => manifest.icons.find(icon => icon.sizes === sizes && (icon.purpose ?? 'any') === purpose)
    for (const icon of [find('192x192', 'any'), find('512x512', 'any'), find('512x512', 'maskable')]) {
      expect(icon).toBeDefined()
      expect(icon!.type).toBe('image/png')
      const { width, height } = pngSize(icon!.src.replace(/^\//, ''))
      expect(`${width}x${height}`).toBe(icon!.sizes)
    }
  })
})

describe('the Digital Asset Links file (lets the Android app open the site without an address bar)', () => {
  const links = JSON.parse(read('.well-known/assetlinks.json')) as Array<{ relation: string[]; target: { namespace: string; package_name: string; sha256_cert_fingerprints: string[] } }>

  it('says the app com.tickbron.app may handle all links of the site', () => {
    expect(links).toHaveLength(1)
    expect(links[0].relation).toEqual(['delegate_permission/common.handle_all_urls'])
    expect(links[0].target.namespace).toBe('android_app')
    expect(links[0].target.package_name).toBe('com.tickbron.app')
  })

  it('lists the signing key fingerprints in the form Android expects (32 hex pairs with colons)', () => {
    const fingerprints = links[0].target.sha256_cert_fingerprints
    expect(fingerprints.length).toBeGreaterThan(0)
    for (const fingerprint of fingerprints) expect(fingerprint).toMatch(/^([0-9A-F]{2}:){31}[0-9A-F]{2}$/)
  })
})

describe('the offline page', () => {
  const page = read('offline.html')

  it('names the site, offers a retry and speaks the three languages of the site', () => {
    expect(page).toContain('TICKBRON')
    expect(page).toMatch(/lang="uz"/)
    expect(page).toMatch(/lang="ru"/)
    expect(page).toMatch(/lang="en"/)
    expect(page).toMatch(/<a [^>]*href="\/"/)
  })

  it('needs no script (the site policy only allows files of its own)', () => {
    expect(page).not.toMatch(/<script/i)
  })
})

describe('the service worker', () => {
  type Listener = (event: Record<string, unknown>) => void
  const source = read('sw.js')

  function start(cacheNames: string[] = []) {
    const listeners: Record<string, Listener> = {}
    const store = new Map<string, string[]>(cacheNames.map(name => [name, []]))
    const caches = {
      open: vi.fn(async (name: string) => ({
        addAll: vi.fn(async (urls: string[]) => { store.set(name, urls) }),
      })),
      match: vi.fn(async (url: string) => `cached:${url}`),
      keys: vi.fn(async () => [...store.keys()]),
      delete: vi.fn(async (name: string) => store.delete(name)),
    }
    const self = { addEventListener: (type: string, listener: Listener) => { listeners[type] = listener }, skipWaiting: vi.fn(), clients: { claim: vi.fn() } }
    new Function('self', 'caches', source)(self, caches)
    return { listeners, caches, store, self }
  }

  /** Runs a listener and returns what it gave to waitUntil / respondWith (undefined when it was not used) */
  async function run(listener: Listener, request?: Record<string, unknown>) {
    let given: Promise<unknown> | undefined
    const event = { request, waitUntil: (promise: Promise<unknown>) => { given = promise }, respondWith: (promise: Promise<unknown>) => { given = promise } }
    listener(event)
    return { used: given !== undefined, value: await given }
  }

  afterEach(() => vi.unstubAllGlobals())

  it('keeps the offline page and the logo ready when it is installed', async () => {
    const { listeners, store } = start()
    await run(listeners.install)
    expect(store.get('tickbron-offline-v1')).toEqual(['/offline.html', '/brand/tickbron-mark.webp'])
    for (const url of store.get('tickbron-offline-v1')!) expect(existsSync(join(PUBLIC_DIR, url.replace(/^\//, ''))), url).toBe(true)
  })

  it('removes the caches of older versions when it takes over', async () => {
    const { listeners, caches } = start(['tickbron-offline-v1', 'tickbron-offline-v0'])
    await run(listeners.activate)
    expect(caches.delete).toHaveBeenCalledWith('tickbron-offline-v0')
    expect(caches.delete).not.toHaveBeenCalledWith('tickbron-offline-v1')
  })

  it('answers a page visit with the offline page when there is no connection', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('offline')))
    const { listeners } = start()
    const { used, value } = await run(listeners.fetch, { mode: 'navigate', url: 'https://tickbron.com/search' })
    expect(used).toBe(true)
    expect(value).toBe('cached:/offline.html')
  })

  it('hands a page visit with a connection to the network untouched', async () => {
    const response = { ok: true }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response))
    const { listeners } = start()
    const { value } = await run(listeners.fetch, { mode: 'navigate', url: 'https://tickbron.com/' })
    expect(value).toBe(response)
  })

  it('never touches anything but page visits: the API, sign-in and booking data are never stored or replayed', async () => {
    const { listeners, caches } = start()
    for (const url of ['https://tickbron.com/api/v1/auth/me/', 'https://tickbron.com/assets/index-abc.js', 'https://tickbron.com/media/a.jpg']) {
      const { used } = await run(listeners.fetch, { mode: 'cors', url })
      expect(used, url).toBe(false)
    }
    expect(caches.match).not.toHaveBeenCalled()
  })
})
