import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { StarIcon } from './StarIcon'

describe('StarIcon', () => {
  it('is a decorative SVG that follows the text colour', () => {
    const { container } = render(<StarIcon />)
    const svg = container.querySelector('svg.star-icon')
    expect(svg).toHaveAttribute('aria-hidden', 'true')
    expect(svg).toHaveAttribute('fill', 'currentColor')
  })
})
