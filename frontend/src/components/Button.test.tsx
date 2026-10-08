import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { Button, ButtonLink, buttonClassName } from './Button'

describe('Button', () => {
  it.each(['primary', 'secondary', 'tonal', 'ghost', 'danger', 'link'] as const)('renders the %s variant', (variant) => {
    render(<Button variant={variant}>Save</Button>)
    expect(screen.getByRole('button', { name: 'Save' })).toHaveClass('btn', `btn-${variant}`)
  })

  it('is a primary medium button by default and never submits a form by accident', () => {
    render(<Button>Save</Button>)
    const button = screen.getByRole('button', { name: 'Save' })
    expect(button).toHaveClass('btn-primary')
    expect(button).not.toHaveClass('btn-sm')
    expect(button).not.toHaveClass('btn-lg')
    expect(button).toHaveAttribute('type', 'button')
  })

  it.each(['sm', 'lg'] as const)('renders the %s size', (size) => {
    render(<Button size={size}>Save</Button>)
    expect(screen.getByRole('button')).toHaveClass(`btn-${size}`)
  })

  it('can be full width', () => {
    render(<Button fullWidth>Save</Button>)
    expect(screen.getByRole('button')).toHaveClass('btn-full')
  })

  it('does not click when disabled', async () => {
    const onClick = vi.fn()
    render(<Button disabled onClick={onClick}>Save</Button>)
    await userEvent.click(screen.getByRole('button'))
    expect(onClick).not.toHaveBeenCalled()
  })

  it('is busy while loading, swallows clicks and cannot submit a form twice', async () => {
    const onClick = vi.fn()
    const onSubmit = vi.fn((event: React.FormEvent) => event.preventDefault())
    render(
      <form onSubmit={onSubmit}>
        <Button type="submit" loading onClick={onClick}>Save</Button>
      </form>
    )
    const button = screen.getByRole('button', { name: 'Save' })
    expect(button).toHaveAttribute('aria-busy', 'true')
    expect(button).toHaveAttribute('aria-disabled', 'true')
    await userEvent.click(button)
    expect(onClick).not.toHaveBeenCalled()
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('clicks and submits when idle', async () => {
    const onClick = vi.fn()
    render(<Button onClick={onClick}>Save</Button>)
    await userEvent.click(screen.getByRole('button'))
    expect(onClick).toHaveBeenCalledTimes(1)
    expect(screen.getByRole('button')).not.toHaveAttribute('aria-busy')
  })

  it('gives an icon-only button its accessible name', () => {
    render(<Button iconOnly icon={<svg aria-hidden="true" />} aria-label="Close dialog" />)
    const button = screen.getByRole('button', { name: 'Close dialog' })
    expect(button).toHaveClass('btn-icon')
  })

  it('requires an aria-label on an icon-only button', () => {
    // @ts-expect-error an icon-only button without aria-label must not compile
    render(<Button iconOnly icon={<svg />} />)
  })
})

describe('ButtonLink', () => {
  it('renders a link with the button classes', () => {
    render(
      <MemoryRouter>
        <ButtonLink to="/search" variant="secondary" size="lg">Search</ButtonLink>
      </MemoryRouter>
    )
    const link = screen.getByRole('link', { name: 'Search' })
    expect(link).toHaveAttribute('href', '/search')
    expect(link).toHaveClass('btn', 'btn-secondary', 'btn-lg')
  })
})

describe('buttonClassName', () => {
  it('builds the shared class string', () => {
    expect(buttonClassName({ variant: 'danger', size: 'sm', className: 'extra' })).toBe('btn btn-danger btn-sm extra')
  })
})
