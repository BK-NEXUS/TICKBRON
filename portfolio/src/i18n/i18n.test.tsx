import { act, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { dictionaries } from './dictionaries'
import { useI18n } from './context'
import { I18nProvider } from './I18nProvider'

function Probe() {
  const { lang, setLang, t } = useI18n()
  return (
    <div>
      <span data-testid="lang">{lang}</span>
      <span data-testid="role">{t('hero.role')}</span>
      <span data-testid="missing">{t('no.such.key')}</span>
      <button onClick={() => setLang('en')}>en</button>
    </div>
  )
}

beforeEach(() => localStorage.clear())
afterEach(() => vi.restoreAllMocks())

describe('dictionaries', () => {
  it('have identical key sets in uz, en and ru', () => {
    const keys = (l: 'uz' | 'en' | 'ru') => Object.keys(dictionaries[l]).sort()
    expect(keys('en')).toEqual(keys('uz'))
    expect(keys('ru')).toEqual(keys('uz'))
  })
})

describe('I18nProvider', () => {
  it('defaults to uz and translates', () => {
    render(<I18nProvider><Probe /></I18nProvider>)
    expect(screen.getByTestId('lang')).toHaveTextContent('uz')
    expect(screen.getByTestId('role')).toHaveTextContent(dictionaries.uz['hero.role'])
  })

  it('switches language and persists it', () => {
    render(<I18nProvider><Probe /></I18nProvider>)
    act(() => screen.getByText('en').click())
    expect(screen.getByTestId('role')).toHaveTextContent(dictionaries.en['hero.role'])
    expect(localStorage.getItem('lang')).toBe('en')
  })

  it('falls back to uz when the stored code is unknown', () => {
    localStorage.setItem('lang', 'xx')
    render(<I18nProvider><Probe /></I18nProvider>)
    expect(screen.getByTestId('lang')).toHaveTextContent('uz')
  })

  it('works when localStorage throws', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => { throw new Error('blocked') })
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('blocked') })
    render(<I18nProvider><Probe /></I18nProvider>)
    act(() => screen.getByText('en').click())
    expect(screen.getByTestId('lang')).toHaveTextContent('en')
  })

  it('keeps the document lang attribute in sync', () => {
    render(<I18nProvider><Probe /></I18nProvider>)
    expect(document.documentElement.lang).toBe('uz')
    act(() => screen.getByText('en').click())
    expect(document.documentElement.lang).toBe('en')
  })

  it('returns the key for unknown keys', () => {
    render(<I18nProvider><Probe /></I18nProvider>)
    expect(screen.getByTestId('missing')).toHaveTextContent('no.such.key')
  })
})
