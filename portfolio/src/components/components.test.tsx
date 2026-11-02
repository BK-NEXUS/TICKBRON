import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { I18nProvider } from '../i18n/I18nProvider'
import { Counter } from './Counter'
import { LanguageSwitch } from './LanguageSwitch'
import { SocialButton } from './SocialButton'
import { TiltCard } from './TiltCard'

function stubMotion(reduced: boolean) {
  vi.stubGlobal(
    'matchMedia',
    vi.fn((query: string) => ({
      matches: query.includes('reduced-motion') ? reduced : false,
      addEventListener: () => {},
      removeEventListener: () => {},
    })),
  )
}

afterEach(() => {
  vi.unstubAllGlobals()
  localStorage.clear()
})

describe('Counter', () => {
  it('shows the final value immediately with reduced motion', () => {
    stubMotion(true)
    render(<Counter value={350} />)
    expect(screen.getByText('350')).toBeInTheDocument()
  })
})

describe('LanguageSwitch', () => {
  it('switches language and marks the active button', async () => {
    stubMotion(false)
    render(<I18nProvider><LanguageSwitch /></I18nProvider>)
    expect(screen.getByRole('button', { name: 'UZ' })).toHaveAttribute('aria-pressed', 'true')
    await userEvent.click(screen.getByRole('button', { name: 'EN' }))
    expect(screen.getByRole('button', { name: 'EN' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: 'UZ' })).toHaveAttribute('aria-pressed', 'false')
  })
})

describe('SocialButton', () => {
  it('opens https links safely in a new tab', () => {
    stubMotion(false)
    render(<I18nProvider><SocialButton link={{ id: 'telegram', label: 'Telegram', href: 'https://t.me/example' }} /></I18nProvider>)
    const a = screen.getByRole('link', { name: /Telegram/ })
    expect(a).toHaveAttribute('href', 'https://t.me/example')
    expect(a).toHaveAttribute('target', '_blank')
    expect(a).toHaveAttribute('rel', 'noopener noreferrer')
  })

  it('does not open mailto links in a new tab', () => {
    stubMotion(false)
    render(<I18nProvider><SocialButton link={{ id: 'email', label: 'Email', href: 'mailto:a@b.co' }} /></I18nProvider>)
    const a = screen.getByRole('link', { name: /Email/ })
    expect(a).not.toHaveAttribute('target')
  })
})

describe('TiltCard', () => {
  it('renders children and does not tilt with reduced motion', async () => {
    stubMotion(true)
    render(<TiltCard><p>card</p></TiltCard>)
    const card = screen.getByText('card').parentElement as HTMLElement
    await userEvent.hover(card)
    expect(card.style.transform).toBe('')
  })
})
