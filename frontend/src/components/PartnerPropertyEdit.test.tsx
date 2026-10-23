import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { PartnerPropertyEdit } from './PartnerPropertyEdit'
import { partnerAdapter, type PartnerProperty } from '../adapters/partnerAdapter'

vi.mock('../adapters/partnerAdapter', () => ({ partnerAdapter: { updateProperty: vi.fn() } }))

const property = {
  id: 7, city: 'Tashkent', address_line1: '1 Amir Temur', address_line2: 'Block B', status: 'active',
  translations: { en: { name: 'Hotel Plaza', description: 'Quiet' }, ru: { name: 'Отель', description: '' } },
} as unknown as PartnerProperty

const setup = () => {
  const onSaved = vi.fn()
  render(<PartnerPropertyEdit property={property} onSaved={onSaved} />)
  return onSaved
}
const type = (label: string, value: string) => fireEvent.change(screen.getByLabelText(label), { target: { value } })

describe('PartnerPropertyEdit', () => {
  beforeEach(() => {
    vi.mocked(partnerAdapter.updateProperty).mockReset()
  })

  it('shows what is saved: names, descriptions and the address', () => {
    setup()
    expect(screen.getByLabelText('Hotel name (English)')).toHaveValue('Hotel Plaza')
    expect(screen.getByLabelText('Description (English)')).toHaveValue('Quiet')
    expect(screen.getByLabelText('Hotel name (Русский)')).toHaveValue('Отель')
    expect(screen.getByLabelText('Hotel name (Oʻzbekcha)')).toHaveValue('')
    expect(screen.getByLabelText('Address Line 1 *')).toHaveValue('1 Amir Temur')
    expect(screen.getByLabelText('Address Line 2')).toHaveValue('Block B')
  })

  it('tells that the place is set by the administrator and offers no place fields', () => {
    setup()
    expect(screen.getByText(/set by the administrator/)).toBeInTheDocument()
    expect(screen.queryByLabelText('Country')).not.toBeInTheDocument()
  })

  it('saves the changed texts and the address, then reports the saved hotel', async () => {
    const saved = { ...property, name: 'Hotel Grand' } as PartnerProperty
    vi.mocked(partnerAdapter.updateProperty).mockResolvedValue({ data: saved, error: null })
    const onSaved = setup()
    type('Hotel name (English)', ' Hotel Grand ')
    type('Hotel name (Oʻzbekcha)', 'Katta Mehmonxona')
    type('Address Line 1 *', '5 New Street')
    fireEvent.click(screen.getByRole('button', { name: 'Save changes' }))
    await waitFor(() => expect(onSaved).toHaveBeenCalledWith(saved))
    expect(partnerAdapter.updateProperty).toHaveBeenCalledWith(7, {
      translations: {
        uz: { name: 'Katta Mehmonxona', description: '' },
        ru: { name: 'Отель', description: '' },
        en: { name: 'Hotel Grand', description: 'Quiet' },
      },
      address_line1: '5 New Street',
      address_line2: 'Block B',
    })
    expect(await screen.findByRole('status')).toHaveTextContent('Changes saved')
  })

  it('refuses to save without any name', () => {
    setup()
    type('Hotel name (English)', '')
    type('Hotel name (Русский)', '   ')
    fireEvent.click(screen.getByRole('button', { name: 'Save changes' }))
    expect(screen.getByRole('alert')).toHaveTextContent('Give the hotel a name in at least one language.')
    expect(partnerAdapter.updateProperty).not.toHaveBeenCalled()
  })

  it('refuses to save without an address', () => {
    setup()
    type('Address Line 1 *', ' ')
    fireEvent.click(screen.getByRole('button', { name: 'Save changes' }))
    expect(screen.getByRole('alert')).toBeInTheDocument()
    expect(partnerAdapter.updateProperty).not.toHaveBeenCalled()
  })

  it('shows the error of the server and keeps what was typed', async () => {
    vi.mocked(partnerAdapter.updateProperty).mockResolvedValue({ data: null, error: 'Use plain text without < or >.' })
    const onSaved = setup()
    type('Hotel name (English)', 'Hotel <b>')
    fireEvent.click(screen.getByRole('button', { name: 'Save changes' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Use plain text without < or >.')
    expect(screen.getByLabelText('Hotel name (English)')).toHaveValue('Hotel <b>')
    expect(onSaved).not.toHaveBeenCalled()
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })

  it('disables the form while saving, so a second click cannot send it twice', async () => {
    let finish: (value: { data: PartnerProperty; error: null }) => void = () => {}
    vi.mocked(partnerAdapter.updateProperty).mockReturnValue(new Promise(resolve => { finish = resolve }))
    setup()
    fireEvent.click(screen.getByRole('button', { name: 'Save changes' }))
    const busy = await screen.findByRole('button', { name: 'Saving...' })
    expect(busy).toBeDisabled()
    finish({ data: property, error: null })
    await screen.findByRole('status')
    expect(partnerAdapter.updateProperty).toHaveBeenCalledTimes(1)
  })
})
