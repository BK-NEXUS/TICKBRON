import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { HeroScene } from './HeroScene'

describe('HeroScene', () => {
  it('is decoration only: hidden from assistive technology and without text', () => {
    const { container } = render(<HeroScene />)

    const scene = container.querySelector('.hero-scene')
    expect(scene).toHaveAttribute('aria-hidden', 'true')
    expect(scene?.textContent).toBe('')
    expect(container.querySelectorAll('.hero-arch')).toHaveLength(3)
  })
})
