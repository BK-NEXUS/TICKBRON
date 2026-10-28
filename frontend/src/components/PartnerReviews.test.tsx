import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { PartnerReviews } from './PartnerReviews'
import { partnerAdapter, type OwnerReview } from '../adapters/partnerAdapter'
import { I18nProvider } from '../i18n/I18nContext'

vi.mock('../adapters/partnerAdapter')

const row = (over: Partial<OwnerReview>): OwnerReview => ({
  id: 1, property: 5, property_name: 'Registan Hotel', reviewer: 'Aziz K.', stay_month: '2026-10', overall_rating: 4,
  title: 'Quiet', comment: 'Clean rooms', created_at: '2026-10-20T10:00:00Z', owner_reply: '', replied_at: null, ...over,
})

const properties = [{ id: 5, name: 'Registan Hotel' }, { id: 6, name: 'Chorsu Inn' }]

function show() {
  return render(<I18nProvider><PartnerReviews properties={properties} /></I18nProvider>)
}

describe('PartnerReviews', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.setItem('tickbron.language', 'en')
    vi.mocked(partnerAdapter.getReviews).mockResolvedValue({ data: { count: 1, hasMore: false, results: [row({})] }, error: null })
    vi.mocked(partnerAdapter.replyToReview).mockResolvedValue({ data: row({ owner_reply: 'Thank you!', replied_at: '2026-10-21T10:00:00Z' }), error: null })
    vi.mocked(partnerAdapter.deleteReviewReply).mockResolvedValue({ data: null, error: null })
  })

  it('lists the reviews of the owner hotels with what the guest wrote, without an address', async () => {
    show()
    expect(await screen.findByText('Clean rooms')).toBeInTheDocument()
    expect(screen.getByText(/Aziz K\./)).toBeInTheDocument()
    expect(screen.getAllByText('Registan Hotel').length).toBeGreaterThan(0)
    expect(partnerAdapter.getReviews).toHaveBeenCalledWith({ propertyId: undefined, page: 1 })
  })

  it('shows the reviews of one hotel when it is picked', async () => {
    show()
    await screen.findByText('Clean rooms')
    fireEvent.change(screen.getByLabelText('Hotel'), { target: { value: '6' } })
    await waitFor(() => expect(partnerAdapter.getReviews).toHaveBeenLastCalledWith({ propertyId: 6, page: 1 }))
  })

  it('sends the answer and shows it under the review', async () => {
    show()
    fireEvent.change(await screen.findByLabelText('Your answer'), { target: { value: ' Thank you! ' } })
    fireEvent.click(screen.getByRole('button', { name: 'Send answer' }))
    await waitFor(() => expect(partnerAdapter.replyToReview).toHaveBeenCalledWith(1, 'Thank you!'))
    expect(await screen.findByRole('button', { name: 'Save answer' })).toBeInTheDocument()  // it is an answered review now
    expect(screen.getByLabelText('Your answer')).toHaveValue('Thank you!')
  })

  it('does not send an empty answer', async () => {
    show()
    await screen.findByLabelText('Your answer')
    fireEvent.click(screen.getByRole('button', { name: 'Send answer' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Write the answer first.')
    expect(partnerAdapter.replyToReview).not.toHaveBeenCalled()
  })

  it('shows the answer that exists and lets the owner remove it', async () => {
    vi.mocked(partnerAdapter.getReviews).mockResolvedValue({
      data: { count: 1, hasMore: false, results: [row({ owner_reply: 'Welcome back', replied_at: '2026-10-21T10:00:00Z' })] }, error: null })
    show()
    expect(await screen.findByLabelText('Your answer')).toHaveValue('Welcome back')
    fireEvent.click(screen.getByRole('button', { name: 'Remove answer' }))
    await waitFor(() => expect(partnerAdapter.deleteReviewReply).toHaveBeenCalledWith(1))
    await waitFor(() => expect(screen.getByLabelText('Your answer')).toHaveValue(''))
    expect(screen.queryByRole('button', { name: 'Remove answer' })).not.toBeInTheDocument()
  })

  it('shows the problem and keeps the text when the answer is refused', async () => {
    vi.mocked(partnerAdapter.replyToReview).mockResolvedValue({ data: null, error: 'Not found.' })
    show()
    fireEvent.change(await screen.findByLabelText('Your answer'), { target: { value: 'Thanks' } })
    fireEvent.click(screen.getByRole('button', { name: 'Send answer' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Not found.')
    expect(screen.getByLabelText('Your answer')).toHaveValue('Thanks')
  })

  it('says there are no reviews yet, and loads more pages', async () => {
    vi.mocked(partnerAdapter.getReviews).mockResolvedValueOnce({ data: { count: 0, hasMore: false, results: [] }, error: null })
    const view = show()
    expect(await screen.findByText('No reviews of your hotels yet.')).toBeInTheDocument()
    view.unmount()

    vi.mocked(partnerAdapter.getReviews)
      .mockResolvedValueOnce({ data: { count: 2, hasMore: true, results: [row({})] }, error: null })
      .mockResolvedValueOnce({ data: { count: 2, hasMore: false, results: [row({ id: 2, comment: 'Second one' })] }, error: null })
    show()
    fireEvent.click(await screen.findByRole('button', { name: 'Show more' }))
    expect(await screen.findByText('Second one')).toBeInTheDocument()
  })
})
