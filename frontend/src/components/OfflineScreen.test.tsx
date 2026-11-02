import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { I18nProvider } from '../i18n/I18nContext'
import { OfflineScreen } from './OfflineScreen'

const show = () => render(<I18nProvider><OfflineScreen /></I18nProvider>)
const goOffline = () => act(() => { window.dispatchEvent(new Event('offline')) })

describe('OfflineScreen', () => {
  beforeEach(() => { localStorage.clear(); localStorage.setItem('tickbron.language', 'en') })
  afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals() })

  it('shows nothing while the connection works', () => {
    show()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('shows the message, the picture and a retry button as soon as the connection is gone', () => {
    const { container } = show()
    goOffline()
    const alert = screen.getByRole('alert')
    expect(alert).toHaveTextContent('No internet connection')
    expect(alert).toHaveTextContent('Check your Wi-Fi or mobile data')
    expect(container.querySelector('svg[aria-hidden="true"]')).not.toBeNull()
    expect(screen.getByRole('button', { name: 'Try again' })).toBeInTheDocument()
  })

  it('goes away by itself when the connection comes back', () => {
    show()
    goOffline()
    act(() => { window.dispatchEvent(new Event('online')) })
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('"Try again" closes the screen when the server answers', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(null)))
    show()
    goOffline()
    fireEvent.click(screen.getByRole('button', { name: 'Try again' }))
    await waitFor(() => expect(screen.queryByRole('alert')).not.toBeInTheDocument())
  })

  it('"Try again" says there is still no connection when the server does not answer', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
    show()
    goOffline()
    fireEvent.click(screen.getByRole('button', { name: 'Try again' }))
    expect(await screen.findByText('Still no connection.')).toBeInTheDocument()
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('speaks the language of the page', () => {
    localStorage.setItem('tickbron.language', 'uz')
    show()
    goOffline()
    expect(screen.getByRole('alert')).toHaveTextContent('Internet aloqasi yo\'q')
  })

  it('moves: the hotel breathes, the palms sway, the Z floats, the badge pulses, the windows twinkle, clouds drift', () => {
    const { container } = show()
    goOffline()
    for (const part of ['offline-breathe', 'offline-sway', 'offline-zzz', 'offline-pulse', 'offline-twinkle', 'offline-drift']) {
      expect(container.querySelector(`svg .${part}`), part).not.toBeNull()
    }
    expect(container.querySelectorAll('svg .offline-sway').length).toBeGreaterThanOrEqual(2)
    expect(container.querySelectorAll('svg .offline-zzz').length).toBeGreaterThanOrEqual(3)
  })

  it('every animation of the screen is switched on only for people who have not asked for less motion', () => {
    const css = readFileSync(resolve(process.cwd(), 'src/styles/index.css'), 'utf8')
    const block = css.slice(css.indexOf('/* Offline screen'))
    const guard = block.indexOf('@media (prefers-reduced-motion: no-preference)')
    expect(guard).toBeGreaterThan(-1)
    expect(block.indexOf('animation:')).toBeGreaterThan(guard)
    const firstKeyframes = block.indexOf('@keyframes')
    expect(firstKeyframes).toBeGreaterThan(guard)
  })
})
