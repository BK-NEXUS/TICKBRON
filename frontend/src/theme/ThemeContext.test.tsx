import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ThemeProvider, useTheme } from './ThemeContext'
import { ThemeToggle } from '../components/ThemeToggle'

const mockSystemDark = (dark: boolean) =>
  vi.spyOn(window, 'matchMedia').mockImplementation(
    (query: string) => ({ matches: dark && query.includes('dark'), media: query, addEventListener() {}, removeEventListener() {} }) as unknown as MediaQueryList,
  )

function Probe() {
  const { theme, effectiveTheme } = useTheme()
  return <span data-testid="state">{theme}/{effectiveTheme}</span>
}

describe('ThemeProvider', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.removeAttribute('data-theme')
  })
  afterEach(() => vi.restoreAllMocks())

  it('follows the system setting until the user chooses, without setting data-theme', () => {
    mockSystemDark(true)
    render(<ThemeProvider><Probe /></ThemeProvider>)
    expect(screen.getByTestId('state')).toHaveTextContent('system/dark')
    expect(document.documentElement).not.toHaveAttribute('data-theme')
  })

  it('applies a stored choice to <html>', () => {
    mockSystemDark(true)
    localStorage.setItem('tickbron.theme', 'light')
    render(<ThemeProvider><Probe /></ThemeProvider>)
    expect(screen.getByTestId('state')).toHaveTextContent('light/light')
    expect(document.documentElement).toHaveAttribute('data-theme', 'light')
  })

  it('ignores a stored value that is not a theme', () => {
    mockSystemDark(false)
    localStorage.setItem('tickbron.theme', 'purple')
    render(<ThemeProvider><Probe /></ThemeProvider>)
    expect(screen.getByTestId('state')).toHaveTextContent('system/light')
  })

  it('works without localStorage', () => {
    mockSystemDark(false)
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => { throw new Error('blocked') })
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('blocked') })
    render(<ThemeProvider><ThemeToggle /></ThemeProvider>)
    fireEvent.click(screen.getByRole('button'))
    expect(document.documentElement).toHaveAttribute('data-theme', 'dark')
  })
})

describe('ThemeToggle', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.removeAttribute('data-theme')
  })
  afterEach(() => vi.restoreAllMocks())

  it('switches to the opposite of what is shown, remembers it, and names the action', () => {
    mockSystemDark(false)
    const { unmount } = render(<ThemeProvider><ThemeToggle /></ThemeProvider>)
    const button = screen.getByRole('button', { name: 'Switch to dark theme' })
    expect(button).toHaveAttribute('aria-pressed', 'false')

    fireEvent.click(button)
    expect(document.documentElement).toHaveAttribute('data-theme', 'dark')
    expect(screen.getByRole('button', { name: 'Switch to light theme' })).toHaveAttribute('aria-pressed', 'true')
    expect(localStorage.getItem('tickbron.theme')).toBe('dark')

    unmount()
    render(<ThemeProvider><ThemeToggle /></ThemeProvider>)
    expect(screen.getByRole('button', { name: 'Switch to light theme' })).toBeInTheDocument()
  })

  it('toggles from the system dark setting to light', () => {
    mockSystemDark(true)
    render(<ThemeProvider><ThemeToggle /></ThemeProvider>)
    fireEvent.click(screen.getByRole('button', { name: 'Switch to light theme' }))
    expect(document.documentElement).toHaveAttribute('data-theme', 'light')
  })

  it('is an SVG icon button, not an emoji', () => {
    mockSystemDark(false)
    render(<ThemeProvider><ThemeToggle /></ThemeProvider>)
    expect(screen.getByRole('button').querySelector('svg')).not.toBeNull()
  })
})
