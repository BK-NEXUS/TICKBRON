import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { CreatePromotionDialog } from './PromotionDialogs'
import { promotionAdapter } from '../adapters/promotionAdapter'

vi.mock('../adapters/promotionAdapter', () => ({
  promotionAdapter: { createPromotion: vi.fn() },
}))

const hotel = { id: 3, name: 'Grand', status: 'active' }

describe('CreatePromotionDialog', () => {
  beforeEach(() => vi.clearAllMocks())

  it('reports a priority over the limit in the page language, not in the browser\'s, and sends nothing', () => {
    render(<CreatePromotionDialog hotel={hotel} onCreated={vi.fn()} onClose={vi.fn()} />)
    fireEvent.change(document.getElementById('promo-start') as HTMLInputElement, { target: { value: '2026-11-01' } })
    fireEvent.change(document.getElementById('promo-end') as HTMLInputElement, { target: { value: '2026-11-10' } })
    fireEvent.change(document.getElementById('promo-priority') as HTMLInputElement, { target: { value: '150' } })

    fireEvent.click(screen.getByRole('button', { name: 'Create promotion' }))

    expect(screen.getByRole('alert')).toHaveTextContent('Priority (0-100) cannot be more than 100.')
    expect(promotionAdapter.createPromotion).not.toHaveBeenCalled()
  })

  it('an end date before the start date is reported with the start date', () => {
    render(<CreatePromotionDialog hotel={hotel} onCreated={vi.fn()} onClose={vi.fn()} />)
    fireEvent.change(document.getElementById('promo-start') as HTMLInputElement, { target: { value: '2026-11-10' } })
    fireEvent.change(document.getElementById('promo-end') as HTMLInputElement, { target: { value: '2026-11-01' } })

    fireEvent.click(screen.getByRole('button', { name: 'Create promotion' }))

    expect(screen.getByRole('alert')).toHaveTextContent('End date cannot be less than 2026-11-10.')
  })
})
