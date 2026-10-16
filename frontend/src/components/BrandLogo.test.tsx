import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrandLogo } from './BrandLogo'

describe('BrandLogo', () => {
  it('uses the full lockup on the sign-in pages and names it for screen readers', () => {
    render(<BrandLogo variant="auth" />)

    const logo = screen.getByRole('img', { name: 'TICKBRON — Online Booking' })
    expect(logo).toHaveAttribute('src', '/brand/tickbron-logo.webp')
    expect(logo).toHaveClass('brand-logo', 'brand-logo--auth')
  })

  it.each(['header', 'footer'] as const)('uses the symbol alone in the %s, where the lockup would be too small to read', (variant) => {
    const { container } = render(<BrandLogo variant={variant} decorative />)

    expect(container.querySelector('img.brand-logo:not(.brand-logo--dark)')).toHaveAttribute('src', '/brand/tickbron-mark.webp')
  })

  it('has a light-ink twin for the dark theme that screen readers skip', () => {
    const { container } = render(<BrandLogo variant="auth" />)

    const twin = container.querySelector('img.brand-logo--dark')
    expect(twin).toHaveAttribute('src', '/brand/tickbron-logo-dark.webp')
    expect(twin).toHaveAttribute('alt', '')
    expect(twin).toHaveAttribute('aria-hidden', 'true')
    expect(screen.getAllByRole('img')).toHaveLength(1)
  })

  it('leaves out the name when the visible site name sits next to the logo', () => {
    const { container } = render(<BrandLogo variant="header" decorative />)

    for (const img of container.querySelectorAll('img')) expect(img).toHaveAttribute('alt', '')
  })
})
