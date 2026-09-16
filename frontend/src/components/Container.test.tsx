import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Container } from './Container'

describe('Container', () => {
  it('renders children', () => {
    render(
      <Container>
        <div>Test content</div>
      </Container>
    )
    expect(screen.getByText('Test content')).toBeInTheDocument()
  })

  it('applies default desktop size class', () => {
    const { container } = render(<Container>Content</Container>)
    expect(container.firstChild).toHaveClass('container-desktop')
  })

  it('applies mobile size class', () => {
    const { container } = render(<Container size="mobile">Content</Container>)
    expect(container.firstChild).toHaveClass('container-mobile')
  })

  it('applies tablet size class', () => {
    const { container } = render(<Container size="tablet">Content</Container>)
    expect(container.firstChild).toHaveClass('container-tablet')
  })

  it('applies large-desktop size class', () => {
    const { container } = render(<Container size="large-desktop">Content</Container>)
    expect(container.firstChild).toHaveClass('container-large-desktop')
  })

  it('applies full size class', () => {
    const { container } = render(<Container size="full">Content</Container>)
    expect(container.firstChild).toHaveClass('container-full')
  })

  it('applies custom className', () => {
    const { container } = render(
      <Container className="custom-class">Content</Container>
    )
    expect(container.firstChild).toHaveClass('custom-class')
  })

  it('applies both size and custom classes', () => {
    const { container } = render(
      <Container size="mobile" className="custom-class">Content</Container>
    )
    expect(container.firstChild).toHaveClass('container-mobile')
    expect(container.firstChild).toHaveClass('custom-class')
  })
})
