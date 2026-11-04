import { render, screen, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from '../App'
import { profile } from '../data/profile'
import { I18nProvider } from '../i18n/I18nProvider'
import { dictionaries } from '../i18n/dictionaries'
import { Certificates } from './Certificates'

beforeEach(() => {
  localStorage.clear()
  vi.stubGlobal(
    'matchMedia',
    vi.fn((query: string) => ({
      matches: query.includes('reduced-motion'),
      addEventListener: () => {},
      removeEventListener: () => {},
    })),
  )
})
afterEach(() => vi.unstubAllGlobals())

describe('App', () => {
  it('shows the full name in a single h1', () => {
    render(<App />)
    const h1 = screen.getAllByRole('heading', { level: 1 })
    expect(h1).toHaveLength(1)
    expect(h1[0]).toHaveTextContent(`${profile.firstName} ${profile.lastName}`)
  })

  it('lists every certificate with its score', () => {
    render(<App />)
    const list = screen.getByRole('list', { name: dictionaries.uz['certs.title'] })
    const items = within(list).getAllByRole('listitem')
    expect(items).toHaveLength(profile.certificates.length)
    profile.certificates.forEach((c, i) => {
      expect(items[i]).toHaveTextContent(c.name)
      expect(items[i]).toHaveTextContent(c.score)
    })
  })

  it('links to the personal website in a new tab safely', () => {
    render(<App />)
    const link = screen.getByRole('link', { name: new RegExp(dictionaries.uz['website.cta']) })
    expect(link).toHaveAttribute('href', profile.website.url)
    expect(link).toHaveAttribute('target', '_blank')
    expect(link).toHaveAttribute('rel', 'noopener noreferrer')
  })

  it('keeps a contact link and a theme toggle reachable on every screen', () => {
    render(<App />)
    expect(screen.getByRole('link', { name: dictionaries.uz['contact.title'] })).toHaveAttribute('href', '#contact')
    expect(screen.getByRole('button', { name: dictionaries.uz['theme.toLight'] })).toBeInTheDocument()
  })

  it('lets keyboard users skip to the content and names the navigation', () => {
    render(<App />)
    expect(screen.getByRole('link', { name: dictionaries.uz['a11y.skip'] })).toHaveAttribute('href', '#main')
    expect(screen.getByRole('main')).toHaveAttribute('id', 'main')
    expect(screen.getByRole('navigation', { name: dictionaries.uz['nav.label'] })).toBeInTheDocument()
  })

  it('shows every social link', () => {
    render(<App />)
    const contact = screen.getByRole('region', { name: dictionaries.uz['contact.title'] })
    for (const s of profile.socials) {
      expect(within(contact).getByRole('link', { name: new RegExp(s.label) })).toHaveAttribute('href', s.href)
    }
  })
})

describe('Certificates', () => {
  it('shows the empty state when there are no certificates', () => {
    render(<I18nProvider><Certificates certificates={[]} /></I18nProvider>)
    expect(screen.getByText(dictionaries.uz['certs.empty'])).toBeInTheDocument()
  })

  it('renders a very long certificate name inside the wrapping name element', () => {
    const name = 'Very long certificate name '.repeat(8)
    render(
      <I18nProvider>
        <Certificates certificates={[{ id: 'x', name, score: '9', year: 2024, issuer: 'Issuer' }]} />
      </I18nProvider>,
    )
    expect(screen.getByText(name.trim())).toHaveClass('cert-name')
  })
})
