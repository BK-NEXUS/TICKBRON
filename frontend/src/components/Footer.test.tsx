import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
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
    expect(logo).toHaveAttribute('src', '/brand/tickbron-logo.jpg')
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
    expect(screen.getByText(/2024 TICKBRON/)).toBeInTheDocument()
  })
})
