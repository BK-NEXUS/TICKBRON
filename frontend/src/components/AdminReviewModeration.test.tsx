import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { AdminReviewModeration } from './AdminReviewModeration'
import { adminAdapter, type AdminReview } from '../adapters/adminAdapter'
import { I18nProvider } from '../i18n/I18nContext'

vi.mock('../adapters/adminAdapter')

const row = (over: Partial<AdminReview>): AdminReview => ({
  id: 1, property: 5, property_name: 'Registan Hotel', reviewer: 'Aziz K.', reviewer_email: 'aziz@example.com',
  stay_month: '2026-10', overall_rating: 4, title: 'Quiet', comment: 'Clean rooms', status: 'pending',
  created_at: '2026-10-20T10:00:00Z', reviewed_at: null, ...over,
})

function show() {
  return render(<I18nProvider><AdminReviewModeration /></I18nProvider>)
}

describe('AdminReviewModeration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.setItem('tickbron.language', 'en')
    vi.mocked(adminAdapter.getReviews).mockResolvedValue({ data: { count: 1, hasMore: false, results: [row({})] }, error: null })
    vi.mocked(adminAdapter.decideReview).mockResolvedValue({ data: row({ status: 'approved' }), error: null })
  })

  it('opens on the reviews waiting for a decision, with the hotel, the reviewer and the address', async () => {
    show()
    expect(await screen.findByText('Registan Hotel')).toBeInTheDocument()
    expect(screen.getByText(/Aziz K\./)).toBeInTheDocument()
    expect(screen.getByText(/aziz@example\.com/)).toBeInTheDocument()
    expect(screen.getByText('Clean rooms')).toBeInTheDocument()
    expect(adminAdapter.getReviews).toHaveBeenCalledWith('pending', 1)
  })

  it('shows the other lists on their tab', async () => {
    show()
    await screen.findByText('Registan Hotel')
    fireEvent.click(screen.getByRole('tab', { name: 'Approved' }))
    await waitFor(() => expect(adminAdapter.getReviews).toHaveBeenLastCalledWith('approved', 1))
    fireEvent.click(screen.getByRole('tab', { name: 'Rejected' }))
    await waitFor(() => expect(adminAdapter.getReviews).toHaveBeenLastCalledWith('rejected', 1))
  })

  it('approves a waiting review and takes it off the list', async () => {
    show()
    fireEvent.click(await screen.findByRole('button', { name: 'Approve' }))
    await waitFor(() => expect(adminAdapter.decideReview).toHaveBeenCalledWith(1, 'approve'))
    await waitFor(() => expect(screen.queryByText('Registan Hotel')).not.toBeInTheDocument())
    expect(screen.getByText('No reviews here.')).toBeInTheDocument()
  })

  it('rejects a waiting review', async () => {
    show()
    fireEvent.click(await screen.findByRole('button', { name: 'Reject' }))
    await waitFor(() => expect(adminAdapter.decideReview).toHaveBeenCalledWith(1, 'reject'))
  })

  it('an approved review can only be rejected, a rejected one only approved', async () => {
    vi.mocked(adminAdapter.getReviews).mockResolvedValue({ data: { count: 1, hasMore: false, results: [row({ status: 'approved' })] }, error: null })
    show()
    fireEvent.click(await screen.findByRole('tab', { name: 'Approved' }))
    await screen.findByText('Registan Hotel')
    expect(screen.queryByRole('button', { name: 'Approve' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Reject' })).toBeInTheDocument()
  })

  it('keeps the review and shows the problem when the decision is refused', async () => {
    vi.mocked(adminAdapter.decideReview).mockResolvedValue({ data: null, error: 'Not found.' })
    show()
    fireEvent.click(await screen.findByRole('button', { name: 'Approve' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Not found.')
    expect(screen.getByText('Registan Hotel')).toBeInTheDocument()
  })

  it('loads the next page on "Show more"', async () => {
    vi.mocked(adminAdapter.getReviews)
      .mockResolvedValueOnce({ data: { count: 2, hasMore: true, results: [row({})] }, error: null })
      .mockResolvedValueOnce({ data: { count: 2, hasMore: false, results: [row({ id: 2, property_name: 'Chorsu Inn' })] }, error: null })
    show()
    fireEvent.click(await screen.findByRole('button', { name: 'Show more' }))
    expect(await screen.findByText('Chorsu Inn')).toBeInTheDocument()
    expect(adminAdapter.getReviews).toHaveBeenLastCalledWith('pending', 2)
  })

  it('shows the error when the list cannot be loaded', async () => {
    vi.mocked(adminAdapter.getReviews).mockResolvedValue({ data: null, error: 'Server down' })
    show()
    expect(await screen.findByRole('alert')).toHaveTextContent('Server down')
  })
})
