import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MobileMenu } from './MobileMenu'

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
})
