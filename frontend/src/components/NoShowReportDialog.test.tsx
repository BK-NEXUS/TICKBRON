import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { NoShowReportDialog } from './NoShowReportDialog'
import { I18nProvider } from '../i18n/I18nContext'
import { noShowAdapter } from '../adapters/noShowAdapter'

vi.mock('../adapters/noShowAdapter', () => ({
  noShowAdapter: { reportNoShow: vi.fn() },
}))

const adapter = vi.mocked(noShowAdapter)
const booking = { id: 12, property_name: 'Silk Road Plaza', confirmation_code: 'ABC123', check_in: '2026-10-05', check_out: '2026-10-07' }
const COMMENT = 'The guest never arrived and did not answer calls.'

function renderDialog(overrides: { onReported?: () => void; onClose?: () => void } = {}) {
  const onReported = overrides.onReported ?? vi.fn()
  const onClose = overrides.onClose ?? vi.fn()
  render(
    <I18nProvider>
      <NoShowReportDialog booking={booking} onReported={onReported} onClose={onClose} />
    </I18nProvider>,
  )
  return { onReported, onClose }
}

const box = () => screen.getByLabelText('What happened? (required)') as HTMLTextAreaElement
const submit = () => screen.getByRole('button', { name: 'Send report' })

describe('NoShowReportDialog', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('is a labelled dialog that names the booking', () => {
    renderDialog()
    const dialog = screen.getByRole('dialog', { name: 'Guest did not arrive' })
    expect(dialog).toHaveTextContent('Silk Road Plaza')
    expect(dialog).toHaveTextContent('ABC123')
  })

  it('cannot be sent without a comment of at least 10 characters', () => {
    renderDialog()
    expect(submit()).toBeDisabled()
    fireEvent.change(box(), { target: { value: 'too short' } })
    expect(submit()).toBeDisabled()
    fireEvent.change(box(), { target: { value: '          x          ' } })
    expect(submit()).toBeDisabled()
    fireEvent.change(box(), { target: { value: COMMENT } })
    expect(submit()).toBeEnabled()
  })

  it('limits the comment to 500 characters and shows a counter', () => {
    renderDialog()
    expect(box()).toHaveAttribute('maxlength', '500')
    fireEvent.change(box(), { target: { value: COMMENT } })
    expect(screen.getByText(`${COMMENT.length} / 500`)).toBeInTheDocument()
  })

  it('sends the trimmed comment and tells the screen it worked', async () => {
    adapter.reportNoShow.mockResolvedValue({ data: { id: 5 } as never, error: null, code: null, fieldErrors: null })
    const { onReported } = renderDialog()
    fireEvent.change(box(), { target: { value: `  ${COMMENT}  ` } })
    fireEvent.click(submit())
    await waitFor(() => expect(adapter.reportNoShow).toHaveBeenCalledWith(12, COMMENT))
    await waitFor(() => expect(onReported).toHaveBeenCalledTimes(1))
  })

  it('does not send twice while the request runs', async () => {
    let finish: (value: Awaited<ReturnType<typeof noShowAdapter.reportNoShow>>) => void = () => {}
    adapter.reportNoShow.mockReturnValue(new Promise(resolve => { finish = resolve }))
    renderDialog()
    fireEvent.change(box(), { target: { value: COMMENT } })
    fireEvent.click(submit())
    await waitFor(() => expect(screen.getByRole('button', { name: 'Sending...' })).toBeDisabled())
    fireEvent.click(screen.getByRole('button', { name: 'Sending...' }))
    expect(adapter.reportNoShow).toHaveBeenCalledTimes(1)
    finish({ data: { id: 5 } as never, error: null, code: null, fieldErrors: null })
    await waitFor(() => expect(screen.getByRole('button', { name: 'Send report' })).toBeInTheDocument())
  })

  it('shows a translated message for a business error and stays open', async () => {
    adapter.reportNoShow.mockResolvedValue({ data: null, error: 'x', code: 'window_closed', fieldErrors: null })
    const { onReported } = renderDialog()
    fireEvent.change(box(), { target: { value: COMMENT } })
    fireEvent.click(submit())
    expect(await screen.findByRole('alert')).toHaveTextContent('The time to report this booking has passed.')
    expect(onReported).not.toHaveBeenCalled()
    expect(screen.getByRole('dialog')).toBeInTheDocument()
  })

  it('shows the comment message when the server rejects the text', async () => {
    adapter.reportNoShow.mockResolvedValue({ data: null, error: 'x', code: null, fieldErrors: { comment: ['bad'] } })
    renderDialog()
    fireEvent.change(box(), { target: { value: COMMENT } })
    fireEvent.click(submit())
    expect(await screen.findByRole('alert')).toHaveTextContent('The comment must be 10 to 500 characters of plain text.')
  })

  it('Cancel closes without calling the backend', () => {
    const { onClose } = renderDialog()
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(onClose).toHaveBeenCalled()
    expect(adapter.reportNoShow).not.toHaveBeenCalled()
  })
})
