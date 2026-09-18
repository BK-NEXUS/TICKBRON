import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { FavoritesPage } from './FavoritesPage'

describe('FavoritesPage', () => {
  it('renders empty state with correct content', () => {
    render(
      <MemoryRouter>
        <FavoritesPage />
      </MemoryRouter>
    )

    expect(screen.getByText('❤️')).toBeInTheDocument()
    expect(screen.getByText('No favorites yet')).toBeInTheDocument()
    expect(screen.getByText('Save your favorite properties to view them here.')).toBeInTheDocument()
    expect(screen.getByText('Explore Properties')).toBeInTheDocument()
  })

  it('has proper page structure', () => {
    const { container } = render(
      <MemoryRouter>
        <FavoritesPage />
      </MemoryRouter>
    )

    expect(container.querySelector('.favorites-page')).toBeInTheDocument()
    expect(container.querySelector('.container')).toBeInTheDocument()
  })

  it('links to search page via CTA', () => {
    render(
      <MemoryRouter>
        <FavoritesPage />
      </MemoryRouter>
    )

    const ctaLink = screen.getByText('Explore Properties')
    expect(ctaLink).toHaveAttribute('href', '/search')
  })
})
