import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ReviewsSection } from './ReviewsSection'
import { accountAdapter, type PublicReview } from '../adapters/accountAdapter'
import { useAuth } from '../contexts/AuthContext'
import { I18nProvider } from '../i18n/I18nContext'
import { settle } from '../test/utils'

vi.mock('../adapters/accountAdapter')
vi.mock('../contexts/AuthContext', () => ({ useAuth: vi.fn() }))

const guestReview = (over: Partial<PublicReview>): PublicReview => ({
  id: 1, reviewer: 'Aziz K.', stay_month: '2026-10', overall_rating: 5, title: 'Great', comment: 'Clean rooms',
  created_at: '2026-10-20T10:00:00Z', ...over,
})

function show() {
  return render(<I18nProvider><ReviewsSection propertyId={5} /></I18nProvider>)
}

describe('ReviewsSection guest reviews', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.setItem('tickbron.language', 'en')
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: false } as never)
    vi.mocked(accountAdapter.getPropertyScores).mockResolvedValue({
      data: { property_id: 5, total_reviews: 2, average_rating: 4.5, category_scores: {} }, error: null })
    vi.mocked(accountAdapter.getPublicReviews).mockResolvedValue({
      data: { count: 1, hasMore: false, results: [guestReview({})] }, error: null })
  })

  it('shows what other guests wrote, to a visitor who is not signed in', async () => {
    show()
    expect(await screen.findByRole('heading', { name: 'Guest reviews' })).toBeInTheDocument()
    expect(screen.getByText('Aziz K.')).toBeInTheDocument()
    expect(screen.getByText('Clean rooms')).toBeInTheDocument()
    expect(accountAdapter.getPublicReviews).toHaveBeenCalledWith(5, 1)
  })

  it('loads the next page on "Show more reviews" and puts it below', async () => {
    vi.mocked(accountAdapter.getPublicReviews)
      .mockResolvedValueOnce({ data: { count: 2, hasMore: true, results: [guestReview({})] }, error: null })
      .mockResolvedValueOnce({ data: { count: 2, hasMore: false, results: [guestReview({ id: 2, reviewer: 'Dilnoza R.', comment: 'Friendly staff' })] }, error: null })
    show()
    fireEvent.click(await screen.findByRole('button', { name: 'Show more reviews' }))
    expect(await screen.findByText('Friendly staff')).toBeInTheDocument()
    expect(screen.getByText('Clean rooms')).toBeInTheDocument()
    expect(accountAdapter.getPublicReviews).toHaveBeenLastCalledWith(5, 2)
    expect(screen.queryByRole('button', { name: 'Show more reviews' })).not.toBeInTheDocument()
  })

  it('says there are no reviews yet', async () => {
    vi.mocked(accountAdapter.getPublicReviews).mockResolvedValue({ data: { count: 0, hasMore: false, results: [] }, error: null })
    show()
    expect(await screen.findByText('No reviews yet.')).toBeInTheDocument()
  })

  it('keeps the page when the list cannot be loaded and says so', async () => {
    vi.mocked(accountAdapter.getPublicReviews).mockResolvedValue({ data: null, error: 'Server down' })
    show()
    expect(await screen.findByText('Could not load the reviews.')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Reviews' })).toBeInTheDocument()
  })

  it('tells a signed-in guest that their own review is waiting for approval', async () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: true } as never)
    vi.mocked(accountAdapter.getEligibleProperties).mockResolvedValue({ data: { eligible_properties: [] }, error: null } as never)
    vi.mocked(accountAdapter.getReviews).mockResolvedValue({
      data: [{ id: 9, user: 1, property: 5, overall_rating: 4, comment: 'Mine', status: 'pending', created_at: '2026-10-21T10:00:00Z', updated_at: '2026-10-21T10:00:00Z' }],
      error: null } as never)
    show()
    await settle()
    expect(await screen.findByText('Pending Approval')).toBeInTheDocument()
  })
})
