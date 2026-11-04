import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ThemeToggle } from '../components/ThemeToggle'
import { I18nProvider } from '../i18n/I18nProvider'
import { useTheme } from './context'
import { ThemeProvider } from './ThemeProvider'

function stubMedia({ light = false, reduced = false } = {}) {
  vi.stubGlobal(
    'matchMedia',
    vi.fn((query: string) => ({
      matches: query.includes('color-scheme: light') ? light : query.includes('reduced-motion') ? reduced : false,
      addEventListener: () => {},
      removeEventListener: () => {},
    })),
  )
}

function Probe() {
  const { theme } = useTheme()
  return <span data-testid="theme">{theme}</span>
}

function renderApp() {
  return render(
    <I18nProvider>
      <ThemeProvider>
        <Probe />
        <ThemeToggle />
      </ThemeProvider>
    </I18nProvider>,
  )
}

beforeEach(() => {
  localStorage.clear()
  delete document.documentElement.dataset.theme
})
afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
  Reflect.deleteProperty(document, 'startViewTransition')
})

describe('ThemeProvider', () => {
  it('defaults to dark', () => {
    stubMedia()
    renderApp()
    expect(screen.getByTestId('theme')).toHaveTextContent('dark')
    expect(document.documentElement.dataset.theme).toBe('dark')
  })

  it('follows a light system preference when nothing is stored', () => {
    stubMedia({ light: true })
    renderApp()
    expect(screen.getByTestId('theme')).toHaveTextContent('light')
  })

  it('prefers the stored choice and ignores unknown stored values', () => {
    stubMedia()
    localStorage.setItem('theme', 'light')
    const first = renderApp()
    expect(screen.getByTestId('theme')).toHaveTextContent('light')
    first.unmount()
    localStorage.setItem('theme', 'purple')
    renderApp()
    expect(screen.getByTestId('theme')).toHaveTextContent('dark')
  })

  it('toggles, updates the document and persists the choice', async () => {
    stubMedia()
    renderApp()
    await userEvent.click(screen.getByRole('button'))
    expect(screen.getByTestId('theme')).toHaveTextContent('light')
    expect(document.documentElement.dataset.theme).toBe('light')
    expect(localStorage.getItem('theme')).toBe('light')
  })

  it('still toggles when localStorage throws', async () => {
    stubMedia()
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('blocked')
    })
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('blocked')
    })
    renderApp()
    await userEvent.click(screen.getByRole('button'))
    expect(screen.getByTestId('theme')).toHaveTextContent('light')
  })

  it('animates the change with a view transition when motion is allowed', async () => {
    stubMedia()
    const start = vi.fn((update: () => void) => {
      update()
      return { ready: Promise.resolve() }
    })
    Object.defineProperty(document, 'startViewTransition', { value: start, configurable: true })
    renderApp()
    await userEvent.click(screen.getByRole('button'))
    await act(async () => {})
    expect(start).toHaveBeenCalledTimes(1)
    expect(screen.getByTestId('theme')).toHaveTextContent('light')
  })

  it('skips the view transition with reduced motion', async () => {
    stubMedia({ reduced: true })
    const start = vi.fn()
    Object.defineProperty(document, 'startViewTransition', { value: start, configurable: true })
    renderApp()
    await userEvent.click(screen.getByRole('button'))
    expect(start).not.toHaveBeenCalled()
    expect(screen.getByTestId('theme')).toHaveTextContent('light')
  })
})

describe('ThemeToggle', () => {
  it('labels the action for the theme it switches to', async () => {
    stubMedia()
    renderApp()
    const button = screen.getByRole('button', { name: /kunduzgi/i })
    await userEvent.click(button)
    expect(screen.getByRole('button', { name: /tungi/i })).toBeInTheDocument()
  })
})
