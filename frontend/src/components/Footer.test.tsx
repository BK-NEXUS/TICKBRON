import { describe, it, expect } from 'vitest'
import { fireEvent, render, screen, within } from '@testing-library/react'
import { BrowserRouter } from 'react-router'
import { Footer } from './Footer'

describe('Footer', () => {
  it('renders the TICKBRON branding', () => {
    render(
      <BrowserRouter>
        <Footer />
      </BrowserRouter>
    )
    expect(screen.getByText('TICKBRON')).toBeInTheDocument()
  })

  it('renders the client logo image', () => {
    const { container } = render(
      <BrowserRouter>
        <Footer />
      </BrowserRouter>
    )
    const logo = container.querySelector('.footer img.brand-logo--footer')
    expect(logo).toHaveAttribute('src', '/brand/tickbron-mark.webp')
    expect(logo).toHaveAttribute('alt', '')
  })

  it('renders footer sections', () => {
    render(
      <BrowserRouter>
        <Footer />
      </BrowserRouter>
    )
    expect(screen.getByText('Explore')).toBeInTheDocument()
    expect(screen.getByText('Support')).toBeInTheDocument()
    expect(screen.getByText('Legal')).toBeInTheDocument()
  })

  it('renders copyright notice', () => {
    render(
      <BrowserRouter>
        <Footer />
      </BrowserRouter>
    )
    expect(screen.getByText(new RegExp(`${new Date().getFullYear()} TICKBRON`))).toBeInTheDocument()
  })
})

describe('Footer social links', () => {
  const show = () => render(<BrowserRouter><Footer /></BrowserRouter>)

  it('links to the TICKBRON Instagram account in a new tab', () => {
    show()
    const link = screen.getByRole('link', { name: 'TICKBRON on Instagram' })
    expect(link).toHaveAttribute('href', 'https://www.instagram.com/tickbron/')
    expect(link).toHaveAttribute('target', '_blank')
    expect(link).toHaveAttribute('rel', expect.stringContaining('noopener'))
  })

  it('keeps the developer contacts closed until the button is pressed', () => {
    show()
    const button = screen.getByRole('button', { name: 'Contact the developer' })
    expect(button).toHaveAttribute('aria-expanded', 'false')
    expect(screen.queryByRole('link', { name: 'Telegram' })).not.toBeInTheDocument()
  })

  it('opens the developer contacts with Telegram and Instagram links', () => {
    show()
    fireEvent.click(screen.getByRole('button', { name: 'Contact the developer' }))
    expect(screen.getByRole('button', { name: 'Contact the developer' })).toHaveAttribute('aria-expanded', 'true')
    const telegram = screen.getByRole('link', { name: 'Telegram' })
    expect(telegram).toHaveAttribute('href', 'https://t.me/Kpakona')
    expect(telegram).toHaveAttribute('target', '_blank')
    expect(telegram).toHaveAttribute('rel', expect.stringContaining('noopener'))
    expect(screen.getByRole('link', { name: 'Instagram' })).toHaveAttribute('href', 'https://www.instagram.com/ese.muratovk/')
  })

  it('puts the TICKBRON Instagram logo at the right end of the footer and the developer among the Legal links', () => {
    show()
    const legal = screen.getByText('Legal').closest('.footer-section') as HTMLElement
    const social = screen.getByRole('link', { name: 'TICKBRON on Instagram' }).closest('.footer-section') as HTMLElement
    expect(social).toHaveClass('footer-section--social')
    expect(social.previousElementSibling).toBe(legal)
    expect(within(legal).getByRole('button', { name: 'Contact the developer' })).toBeInTheDocument()
  })

  it('draws the Instagram logo in its own colours', () => {
    show()
    const logo = screen.getByRole('link', { name: 'TICKBRON on Instagram' }).querySelector('svg radialGradient')
    expect(logo).not.toBeNull()
  })

  it('gives the logo gradient a plain id that the fill refers to, so every browser paints it', () => {
    show()
    const svg = screen.getByRole('link', { name: 'TICKBRON on Instagram' }).querySelector('svg') as SVGElement
    const id = svg.querySelector('radialGradient')?.getAttribute('id') ?? ''
    expect(id).toMatch(/^[A-Za-z][A-Za-z0-9_-]*$/)
    expect(svg.querySelector('rect')?.getAttribute('fill')).toBe(`url(#${id})`)
  })

  it('closes the developer contacts with Escape and when clicking elsewhere', () => {
    show()
    const open = () => fireEvent.click(screen.getByRole('button', { name: 'Contact the developer' }))
    open()
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(screen.queryByRole('link', { name: 'Telegram' })).not.toBeInTheDocument()
    open()
    fireEvent.mouseDown(document.body)
    expect(screen.queryByRole('link', { name: 'Telegram' })).not.toBeInTheDocument()
  })
})
