import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { AdminNoShowReports } from './AdminNoShowReports'
import { I18nProvider } from '../i18n/I18nContext'
import { noShowAdapter, type StaffNoShowReport } from '../adapters/noShowAdapter'

vi.mock('../adapters/noShowAdapter', () => ({
  noShowAdapter: { listReports: vi.fn(), approveReport: vi.fn(), rejectReport: vi.fn(), reverseReport: vi.fn() },
}))

const adapter = vi.mocked(noShowAdapter)
const COMMENT = 'Checked with the hotel and the guest.'

function report(id: number, extra: Partial<StaffNoShowReport> = {}): StaffNoShowReport {
  return {
    id, booking_id: id * 10, booking_reference: `REF${id}`, property_id: 3, property_name: 'Silk Road Plaza',
    check_in: '2026-10-05', check_out: '2026-10-07', comment: `Owner comment ${id}`, status: 'pending',
    decision_comment: '', decided_at: null, created_at: '2026-10-08T10:00:00Z', decided_by_id: null, created_by_id: 7,
    hotel_flagged: false,
    refund_preview: { amount: '450000.00', currency: 'UZS', percent: 50, already_refunded: '0.00', paid: '900000.00' },
    refunds: [], ...extra,
  }
}

function page(results: StaffNoShowReport[], count = results.length) {
  return { data: { count, next: null, previous: null, results }, error: null, code: null, fieldErrors: null }
}

function renderScreen() {
  render(
    <I18nProvider>
      <AdminNoShowReports />
    </I18nProvider>,
  )
}

const done = { data: report(1, { status: 'approved' }), error: null, code: null, fieldErrors: null }

describe('AdminNoShowReports', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    adapter.listReports.mockResolvedValue(page([report(1)]))
  })

  describe('queue', () => {
    it('opens on the reports waiting for a decision', async () => {
      renderScreen()
      await screen.findByText('REF1')
      expect(adapter.listReports).toHaveBeenCalledWith(expect.objectContaining({ status: 'pending', page: 1 }))
      expect(screen.getByLabelText('Status')).toHaveValue('pending')
    })

    it('shows the booking reference, hotel, stay, owner comment and the exact refund', async () => {
      renderScreen()
      const item = (await screen.findByText('REF1')).closest('li') as HTMLElement
      expect(within(item).getByText('Silk Road Plaza')).toBeInTheDocument()
      expect(within(item).getByText('Owner comment 1')).toBeInTheDocument()
      expect(within(item).getByText('Waiting for a decision')).toBeInTheDocument()
      expect(item).toHaveTextContent('50%')
      expect(item).toHaveTextContent('450')
      expect(item).toHaveTextContent('900')
    })

    it('says when part of the money was already refunded', async () => {
      adapter.listReports.mockResolvedValue(page([report(1, {
        refund_preview: { amount: '300000.00', currency: 'UZS', percent: 50, already_refunded: '150000.00', paid: '900000.00' },
      })]))
      renderScreen()
      const item = (await screen.findByText('REF1')).closest('li') as HTMLElement
      expect(within(item).getByText(/Already refunded/)).toHaveTextContent('150')
    })

    it('marks a hotel that reports unusually often', async () => {
      adapter.listReports.mockResolvedValue(page([report(1, { hotel_flagged: true }), report(2)]))
      renderScreen()
      const items = await screen.findAllByRole('listitem')
      expect(within(items[0]).getByText('Reports often')).toBeInTheDocument()
      expect(within(items[1]).queryByText('Reports often')).toBeNull()
    })

    it('does not show a refund line for a report without a preview', async () => {
      adapter.listReports.mockResolvedValue(page([report(2, { status: 'rejected', refund_preview: null, decision_comment: 'Guest arrived late' })]))
      renderScreen()
      const item = (await screen.findByText('REF2')).closest('li') as HTMLElement
      expect(item).not.toHaveTextContent('If approved')
      expect(within(item).getByText('Guest arrived late')).toBeInTheDocument()
    })

    it('lists the refunds of an approved report with their state', async () => {
      adapter.listReports.mockResolvedValue(page([report(3, {
        status: 'approved', refund_preview: null, decision_comment: 'ok ok ok ok',
        refunds: [{ id: 1, amount: '450000.00', currency: 'UZS', status: 'needs_manual' }],
      })]))
      renderScreen()
      const item = (await screen.findByText('REF3')).closest('li') as HTMLElement
      expect(item).toHaveTextContent('450')
      expect(within(item).getByText(/Pay by hand/)).toBeInTheDocument()
    })

    it('shows loading, then an empty message', async () => {
      adapter.listReports.mockResolvedValue(page([]))
      renderScreen()
      expect(screen.getByText('Loading reports...')).toBeInTheDocument()
      expect(await screen.findByText('No reports here.')).toBeInTheDocument()
    })

    it('shows an error with a retry', async () => {
      adapter.listReports.mockResolvedValueOnce({ data: null, error: 'boom', code: null, fieldErrors: null })
      renderScreen()
      expect(await screen.findByRole('alert')).toHaveTextContent('Could not load the reports.')
      adapter.listReports.mockResolvedValue(page([report(1)]))
      fireEvent.click(screen.getByRole('button', { name: 'Try Again' }))
      expect(await screen.findByText('REF1')).toBeInTheDocument()
    })

    it('filters by status and by date, back to page 1', async () => {
      renderScreen()
      await screen.findByText('REF1')
      fireEvent.change(screen.getByLabelText('Status'), { target: { value: 'approved' } })
      await waitFor(() => expect(adapter.listReports).toHaveBeenLastCalledWith(expect.objectContaining({ status: 'approved', page: 1 })))
      fireEvent.change(screen.getByLabelText('Sent from'), { target: { value: '2026-10-01' } })
      await waitFor(() => expect(adapter.listReports).toHaveBeenLastCalledWith(expect.objectContaining({ from: '2026-10-01' })))
      fireEvent.change(screen.getByLabelText('Sent to'), { target: { value: '2026-10-09' } })
      await waitFor(() => expect(adapter.listReports).toHaveBeenLastCalledWith(expect.objectContaining({ to: '2026-10-09' })))
      await screen.findByText('REF1')
    })

    it('shows all statuses when All is chosen', async () => {
      renderScreen()
      await screen.findByText('REF1')
      fireEvent.change(screen.getByLabelText('Status'), { target: { value: '' } })
      await waitFor(() => expect(adapter.listReports).toHaveBeenLastCalledWith(expect.objectContaining({ status: '' })))
      await screen.findByText('REF1')
    })

    it('goes to the next page', async () => {
      adapter.listReports.mockResolvedValue({ data: { count: 45, next: 'x', previous: null, results: [report(1)] }, error: null, code: null, fieldErrors: null })
      renderScreen()
      await screen.findByText('REF1')
      fireEvent.click(screen.getByRole('button', { name: 'Next page' }))
      await waitFor(() => expect(adapter.listReports).toHaveBeenLastCalledWith(expect.objectContaining({ page: 2 })))
      await screen.findByText('REF1')
    })
  })

  describe('decisions', () => {
    it('offers approve and reject on a waiting report, and correct on a decided one', async () => {
      adapter.listReports.mockResolvedValue(page([
        report(1),
        report(2, { status: 'approved', refund_preview: null }),
        report(3, { status: 'rejected', refund_preview: null }),
        report(4, { status: 'withdrawn', refund_preview: null }),
      ]))
      renderScreen()
      const items = await screen.findAllByRole('listitem')
      expect(within(items[0]).getByRole('button', { name: 'Approve' })).toBeInTheDocument()
      expect(within(items[0]).getByRole('button', { name: 'Reject' })).toBeInTheDocument()
      expect(within(items[0]).queryByRole('button', { name: 'Correct decision' })).toBeNull()
      expect(within(items[1]).getByRole('button', { name: 'Correct decision' })).toBeInTheDocument()
      expect(within(items[2]).getByRole('button', { name: 'Correct decision' })).toBeInTheDocument()
      expect(within(items[3]).queryAllByRole('button')).toHaveLength(0)
    })

    it('approving needs a comment, shows the refund, then sends it and reloads', async () => {
      adapter.approveReport.mockResolvedValue(done)
      renderScreen()
      fireEvent.click(await screen.findByRole('button', { name: 'Approve' }))
      const dialog = await screen.findByRole('dialog', { name: 'Approve report' })
      expect(dialog).toHaveTextContent('450')
      const send = within(dialog).getByRole('button', { name: 'Approve and refund' })
      expect(send).toBeDisabled()
      fireEvent.change(within(dialog).getByLabelText('Decision comment (required)'), { target: { value: 'short' } })
      expect(send).toBeDisabled()
      fireEvent.change(within(dialog).getByLabelText('Decision comment (required)'), { target: { value: `  ${COMMENT}  ` } })
      expect(send).toBeEnabled()
      adapter.listReports.mockResolvedValue(page([]))
      fireEvent.click(send)
      await waitFor(() => expect(adapter.approveReport).toHaveBeenCalledWith(1, COMMENT))
      await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
      await waitFor(() => expect(adapter.listReports).toHaveBeenCalledTimes(2))
    })

    it('warns that approving refunds nothing when the booking carries no refund promise (0%)', async () => {
      adapter.listReports.mockResolvedValue(page([report(1, {
        refund_preview: { amount: '0.00', currency: 'UZS', percent: 0, already_refunded: '0.00', paid: '900000.00' },
      })]))
      renderScreen()
      fireEvent.click(await screen.findByRole('button', { name: 'Approve' }))
      const dialog = await screen.findByRole('dialog', { name: 'Approve report' })
      expect(within(dialog).getByText(/refunds nothing/)).toBeInTheDocument()
    })

    it('does not show that warning for a normal 50% booking', async () => {
      renderScreen()
      fireEvent.click(await screen.findByRole('button', { name: 'Approve' }))
      const dialog = await screen.findByRole('dialog', { name: 'Approve report' })
      expect(within(dialog).queryByText(/refunds nothing/)).toBeNull()
    })

    it('rejecting sends the comment to reject', async () => {
      adapter.rejectReport.mockResolvedValue(done)
      renderScreen()
      fireEvent.click(await screen.findByRole('button', { name: 'Reject' }))
      const dialog = await screen.findByRole('dialog', { name: 'Reject report' })
      fireEvent.change(within(dialog).getByLabelText('Decision comment (required)'), { target: { value: COMMENT } })
      fireEvent.click(within(dialog).getByRole('button', { name: 'Reject report' }))
      await waitFor(() => expect(adapter.rejectReport).toHaveBeenCalledWith(1, COMMENT))
      await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
    })

    it('correcting a decision sends the comment to reverse', async () => {
      adapter.listReports.mockResolvedValue(page([report(2, { status: 'approved', refund_preview: null })]))
      adapter.reverseReport.mockResolvedValue(done)
      renderScreen()
      fireEvent.click(await screen.findByRole('button', { name: 'Correct decision' }))
      const dialog = await screen.findByRole('dialog', { name: 'Correct decision' })
      fireEvent.change(within(dialog).getByLabelText('Decision comment (required)'), { target: { value: COMMENT } })
      fireEvent.click(within(dialog).getByRole('button', { name: 'Correct decision' }))
      await waitFor(() => expect(adapter.reverseReport).toHaveBeenCalledWith(2, COMMENT))
    })

    it('shows the translated backend error inside the dialog and stays open', async () => {
      adapter.approveReport.mockResolvedValue({ data: null, error: 'x', code: 'inventory_unavailable', fieldErrors: null })
      renderScreen()
      fireEvent.click(await screen.findByRole('button', { name: 'Approve' }))
      const dialog = await screen.findByRole('dialog')
      fireEvent.change(within(dialog).getByLabelText('Decision comment (required)'), { target: { value: COMMENT } })
      fireEvent.click(within(dialog).getByRole('button', { name: 'Approve and refund' }))
      expect(await within(dialog).findByRole('alert')).toHaveTextContent('The rooms are no longer free, so the booking cannot be restored.')
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })

    it('does not send twice while the request runs', async () => {
      let finish: (value: typeof done) => void = () => {}
      adapter.approveReport.mockReturnValue(new Promise(resolve => { finish = resolve }))
      renderScreen()
      fireEvent.click(await screen.findByRole('button', { name: 'Approve' }))
      const dialog = await screen.findByRole('dialog')
      fireEvent.change(within(dialog).getByLabelText('Decision comment (required)'), { target: { value: COMMENT } })
      fireEvent.click(within(dialog).getByRole('button', { name: 'Approve and refund' }))
      await waitFor(() => expect(within(dialog).getByRole('button', { name: 'Sending...' })).toBeDisabled())
      expect(adapter.approveReport).toHaveBeenCalledTimes(1)
      adapter.listReports.mockResolvedValue(page([]))
      finish(done)
      await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
    })

    it('Cancel closes the dialog without calling the backend', async () => {
      renderScreen()
      fireEvent.click(await screen.findByRole('button', { name: 'Reject' }))
      fireEvent.click(within(await screen.findByRole('dialog')).getByRole('button', { name: 'Cancel' }))
      expect(screen.queryByRole('dialog')).toBeNull()
      expect(adapter.rejectReport).not.toHaveBeenCalled()
    })
  })
})
