import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { NotFoundPage } from './NotFoundPage'

describe('NotFoundPage', () => {
  it('renders 404 message', () => {
    render(
      <BrowserRouter>
        <NotFoundPage />
      </BrowserRouter>
    )
    expect(screen.getByText('404')).toBeInTheDocument()
    expect(screen.getByText('Page Not Found')).toBeInTheDocument()
  })

  it('renders helpful message', () => {
    render(
      <BrowserRouter>
        <NotFoundPage />
      </BrowserRouter>
    )
    expect(screen.getByText(/The page you're looking for/)).toBeInTheDocument()
  })

  it('renders home link', () => {
    render(
      <BrowserRouter>
        <NotFoundPage />
      </BrowserRouter>
    )
    const homeLink = screen.getByText('Go Home')
    expect(homeLink).toBeInTheDocument()
    expect(homeLink.closest('a')).toHaveAttribute('href', '/')
  })
})
