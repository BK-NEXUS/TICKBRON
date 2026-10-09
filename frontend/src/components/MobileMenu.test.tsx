import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, within } from '@testing-library/react'
import { MobileMenu } from './MobileMenu'
import { I18nProvider } from '../i18n/I18nContext'

describe('MobileMenu', () => {
  it('does not render when closed', () => {
    render(<MobileMenu isOpen={false} onClose={vi.fn()} />)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('renders when open', () => {
    render(<MobileMenu isOpen={true} onClose={vi.fn()} />)
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByText('Menu')).toBeInTheDocument()
  })

  it('renders navigation links', () => {
    render(<MobileMenu isOpen={true} onClose={vi.fn()} />)
    expect(screen.getByText('Home')).toBeInTheDocument()
    expect(screen.getByText('Properties')).toBeInTheDocument()
    expect(screen.getByText('About')).toBeInTheDocument()
    expect(screen.getByText('Help')).toBeInTheDocument()
  })

  it('Login and Sign Up lead to the login and register pages', () => {
    render(<MobileMenu isOpen={true} onClose={vi.fn()} />)
    expect(screen.getByRole('link', { name: 'Login' })).toHaveAttribute('href', '/login')
    expect(screen.getByRole('link', { name: 'Sign Up' })).toHaveAttribute('href', '/register')
  })

  it('does not offer Login and Sign Up to a logged-in user', () => {
    render(<MobileMenu isOpen={true} onClose={vi.fn()} isAuthenticated />)
    expect(screen.queryByText('Login')).not.toBeInTheDocument()
    expect(screen.queryByText('Sign Up')).not.toBeInTheDocument()
  })

  it('every navigation link points at a page that exists', () => {
    render(<MobileMenu isOpen={true} onClose={vi.fn()} />)
    const hrefs = screen.getAllByRole('link').map(link => link.getAttribute('href'))
    expect(hrefs).toEqual(expect.arrayContaining(['/', '/search', '/about', '/help']))
    expect(hrefs).not.toContain('/properties')
  })

  it('renders action buttons', () => {
    render(<MobileMenu isOpen={true} onClose={vi.fn()} />)
    expect(screen.getByText('Login')).toBeInTheDocument()
    expect(screen.getByText('Sign Up')).toBeInTheDocument()
  })

  it('calls onClose when close button is clicked', () => {
    const handleClose = vi.fn()
    render(<MobileMenu isOpen={true} onClose={handleClose} />)
    
    const closeButton = screen.getByLabelText('Close menu')
    fireEvent.click(closeButton)
    
    expect(handleClose).toHaveBeenCalledTimes(1)
  })

  it('calls onClose when nav link is clicked', () => {
    const handleClose = vi.fn()
    render(<MobileMenu isOpen={true} onClose={handleClose} />)
    
    const homeLink = screen.getByText('Home')
    fireEvent.click(homeLink)
    
    expect(handleClose).toHaveBeenCalledTimes(1)
  })

  it('applies custom className', () => {
    render(
      <MobileMenu isOpen={true} onClose={vi.fn()} className="custom-class" />
    )
    const menu = screen.getByRole('dialog')
    expect(menu).toHaveClass('custom-class')
  })

  it('closes on Escape and keeps focus inside the open menu', () => {
    const onClose = vi.fn()
    render(<MobileMenu isOpen={true} onClose={onClose} />)
    expect(screen.getByRole('dialog')).toContainElement(document.activeElement as HTMLElement)
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  describe('language and currency on phones', () => {
    beforeEach(() => localStorage.clear())
    afterEach(() => localStorage.clear())

    const renderMenu = () =>
      render(<I18nProvider><MobileMenu isOpen={true} onClose={vi.fn()} /></I18nProvider>)

    it('offers the three languages and the two currencies', () => {
      renderMenu()
      const language = screen.getByRole('group', { name: 'Language' })
      expect(within(language).getAllByRole('button').map(b => b.textContent)).toEqual(['UZ', 'RU', 'EN'])
      const currency = screen.getByRole('group', { name: 'Currency' })
      expect(within(currency).getAllByRole('button').map(b => b.textContent)).toEqual(['UZS', 'USD'])
    })

    it('marks the active language and currency', () => {
      renderMenu()
      expect(within(screen.getByRole('group', { name: 'Currency' })).getByRole('button', { name: 'UZS' }))
        .toHaveAttribute('aria-pressed', 'true')
    })

    it('switches the menu text and the page language', () => {
      renderMenu()
      fireEvent.click(screen.getByRole('button', { name: 'Русский' }))
      expect(screen.getByRole('link', { name: 'Главная' })).toBeInTheDocument()
      expect(screen.getByRole('group', { name: 'Язык' })).toBeInTheDocument()
      expect(document.documentElement.lang).toBe('ru')
    })

    it('has the theme button next to them', () => {
      renderMenu()
      expect(screen.getByRole('button', { name: /Switch to (dark|light) theme/ })).toBeInTheDocument()
    })

    it('keeps the menu open when a language or currency is chosen', () => {
      const onClose = vi.fn()
      render(<I18nProvider><MobileMenu isOpen={true} onClose={onClose} /></I18nProvider>)
      fireEvent.click(screen.getByRole('button', { name: 'USD' }))
      expect(onClose).not.toHaveBeenCalled()
    })
  })
})
