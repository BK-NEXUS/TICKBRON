import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { I18nProvider, useI18n } from './I18nContext'

function Probe() {
  const { language, currency, t, formatMoney, setLanguage, setCurrency } = useI18n()
  return (
    <div>
      <span data-testid="lang">{language}</span>
      <span data-testid="cur">{currency}</span>
      <span data-testid="home">{t('nav.home')}</span>
      <span data-testid="money">{formatMoney(1250000, currency)}</span>
      <button onClick={() => setLanguage('ru')}>ru</button>
      <button onClick={() => setCurrency('USD')}>usd</button>
    </div>
  )
}

const setNavigatorLanguage = (value: string) =>
  vi.spyOn(window.navigator, 'language', 'get').mockReturnValue(value)

describe('I18nProvider', () => {
  beforeEach(() => localStorage.clear())
  afterEach(() => vi.restoreAllMocks())

  it('defaults to Uzbek and UZS when the browser language is not supported', () => {
    setNavigatorLanguage('de-DE')
    render(<I18nProvider><Probe /></I18nProvider>)
    expect(screen.getByTestId('lang')).toHaveTextContent('uz')
    expect(screen.getByTestId('cur')).toHaveTextContent('UZS')
  })

  it('follows a supported browser language', () => {
    setNavigatorLanguage('ru-RU')
    render(<I18nProvider><Probe /></I18nProvider>)
    expect(screen.getByTestId('lang')).toHaveTextContent('ru')
    expect(screen.getByTestId('home')).toHaveTextContent('Главная')
  })

  it('switches language and currency, remembers them and sets html lang', () => {
    setNavigatorLanguage('en-US')
    const { unmount } = render(<I18nProvider><Probe /></I18nProvider>)
    expect(screen.getByTestId('home')).toHaveTextContent('Home')

    fireEvent.click(screen.getByText('ru'))
    fireEvent.click(screen.getByText('usd'))
    expect(screen.getByTestId('home')).toHaveTextContent('Главная')
    expect(screen.getByTestId('money')).toHaveTextContent('$1,250,000.00')
    expect(document.documentElement.lang).toBe('ru')

    unmount()
    render(<I18nProvider><Probe /></I18nProvider>)
    expect(screen.getByTestId('lang')).toHaveTextContent('ru')
    expect(screen.getByTestId('cur')).toHaveTextContent('USD')
  })

  it('ignores a stored value that is not a supported option', () => {
    localStorage.setItem('tickbron.language', 'fr')
    localStorage.setItem('tickbron.currency', 'EUR')
    setNavigatorLanguage('en-US')
    render(<I18nProvider><Probe /></I18nProvider>)
    expect(screen.getByTestId('lang')).toHaveTextContent('en')
    expect(screen.getByTestId('cur')).toHaveTextContent('UZS')
  })

  it('still works when localStorage throws', () => {
    setNavigatorLanguage('en-US')
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => { throw new Error('blocked') })
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('blocked') })
    render(<I18nProvider><Probe /></I18nProvider>)
    fireEvent.click(screen.getByText('ru'))
    expect(screen.getByTestId('lang')).toHaveTextContent('ru')
  })
})

describe('useI18n without a provider', () => {
  it('falls back to English text so isolated components render', () => {
    render(<Probe />)
    expect(screen.getByTestId('home')).toHaveTextContent('Home')
  })
})

describe('t', () => {
  it('fills {placeholders} and returns the key for an unknown key', () => {
    function T() {
      const { t } = useI18n()
      return <span data-testid="t">{t('nope.missing' as never)}|{t('header.openMenu')}|{t('language.label', { name: 'Русский' })}</span>
    }
    render(<T />)
    expect(screen.getByTestId('t')).toHaveTextContent('nope.missing|Open menu|Language: Русский')
  })
})
