import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { ProfilePage } from './ProfilePage'

describe('ProfilePage', () => {
  it('renders with correct content', () => {
    render(
      <MemoryRouter>
        <ProfilePage />
      </MemoryRouter>
    )

    expect(screen.getByText('My Profile')).toBeInTheDocument()
    expect(screen.getByText('Profile management coming soon.')).toBeInTheDocument()
  })

  it('has proper page structure', () => {
    const { container } = render(
      <MemoryRouter>
        <ProfilePage />
      </MemoryRouter>
    )

    expect(container.querySelector('.profile-page')).toBeInTheDocument()
    expect(container.querySelector('.container')).toBeInTheDocument()
    expect(container.querySelector('.profile-page-content')).toBeInTheDocument()
  })

  it('applies correct CSS classes', () => {
    const { container } = render(
      <MemoryRouter>
        <ProfilePage />
      </MemoryRouter>
    )

    const title = screen.getByText('My Profile')
    expect(title).toHaveClass('profile-page-title')

    const message = screen.getByText('Profile management coming soon.')
    expect(message).toHaveClass('profile-page-message')
  })
})
