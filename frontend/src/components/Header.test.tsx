import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { Header } from './Header'
import { AuthProvider } from '../contexts/AuthContext'

// Mock the auth adapter
vi.mock('../adapters/authAdapter', () => ({
  authAdapter: {
    getCurrentUser: vi.fn().mockResolvedValue({ success: false }),
  },
}))

describe('Header', () => {
  const renderWithAuthProvider = (component: React.ReactElement) => {
    return render(
      <AuthProvider>
        <BrowserRouter>
          {component}
        </BrowserRouter>
      </AuthProvider>
    )
  }

  it('renders the logo', () => {
    renderWithAuthProvider(<Header />)
    expect(screen.getByText('TICKBRON')).toBeInTheDocument()
  })

  it('renders navigation links', () => {
    renderWithAuthProvider(<Header />)
    expect(screen.getByText('Home')).toBeInTheDocument()
    expect(screen.getByText('Properties')).toBeInTheDocument()
    expect(screen.getByText('About')).toBeInTheDocument()
    expect(screen.getByText('Help')).toBeInTheDocument()
  })

  it('renders action buttons when not authenticated', () => {
    renderWithAuthProvider(<Header />)
    expect(screen.getByText('Login')).toBeInTheDocument()
    expect(screen.getByText('Sign Up')).toBeInTheDocument()
  })

  it('renders language selector', () => {
    renderWithAuthProvider(<Header />)
    expect(screen.getByText('EN')).toBeInTheDocument()
  })

  it('renders currency selector', () => {
    renderWithAuthProvider(<Header />)
    expect(screen.getByText('USD')).toBeInTheDocument()
  })

  it('renders mobile menu toggle', () => {
    renderWithAuthProvider(<Header />)
    const toggle = screen.getByLabelText('Open menu')
    expect(toggle).toBeInTheDocument()
  })
})
