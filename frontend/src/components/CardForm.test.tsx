import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { CardForm } from './CardForm'

const fill = (label: string, value: string) => fireEvent.change(screen.getByLabelText(label), { target: { value } })

function fillValidCard() {
  fill('Card number', '4111111111111111')
  fill('Expiry (MM/YY)', '1230')
  fill('CVV', '123')
  fill('Name on card', 'Alisher Navoiy')
}

describe('CardForm', () => {
  afterEach(() => vi.useRealTimers())

  it('says clearly that it is a test mode form and that nothing is sent', () => {
    render(<CardForm onValidityChange={() => {}} />)
    expect(screen.getByRole('note')).toHaveTextContent(/test mode/i)
    expect(screen.getByRole('note')).toHaveTextContent(/not sent or stored/i)
  })

  it('has the four fields with card autocomplete hints and numeric keyboards', () => {
    render(<CardForm onValidityChange={() => {}} />)
    expect(screen.getByLabelText('Card number')).toHaveAttribute('autocomplete', 'cc-number')
    expect(screen.getByLabelText('Card number')).toHaveAttribute('inputmode', 'numeric')
    expect(screen.getByLabelText('Expiry (MM/YY)')).toHaveAttribute('autocomplete', 'cc-exp')
    expect(screen.getByLabelText('CVV')).toHaveAttribute('autocomplete', 'cc-csc')
    expect(screen.getByLabelText('Name on card')).toHaveAttribute('autocomplete', 'cc-name')
  })

  it('groups the number and the expiry as the user types', () => {
    render(<CardForm onValidityChange={() => {}} />)
    fill('Card number', '4111111111111111999')
    fill('Expiry (MM/YY)', '1230')
    expect(screen.getByLabelText('Card number')).toHaveValue('4111 1111 1111 1111')
    expect(screen.getByLabelText('Expiry (MM/YY)')).toHaveValue('12/30')
  })

  it('reports valid only when all four fields are valid', () => {
    const onValidityChange = vi.fn()
    render(<CardForm onValidityChange={onValidityChange} />)
    expect(onValidityChange).toHaveBeenLastCalledWith(false)

    fillValidCard()
    expect(onValidityChange).toHaveBeenLastCalledWith(true)

    fill('CVV', '12')
    expect(onValidityChange).toHaveBeenLastCalledWith(false)
  })

  it('shows an error under a field after the user leaves it, not before', () => {
    render(<CardForm onValidityChange={() => {}} />)
    fill('Card number', '4111 1111 1111 1112')
    expect(screen.queryByText('Enter a valid card number.')).not.toBeInTheDocument()

    fireEvent.blur(screen.getByLabelText('Card number'))
    expect(screen.getByText('Enter a valid card number.')).toBeInTheDocument()
    expect(screen.getByLabelText('Card number')).toHaveAttribute('aria-invalid', 'true')

    fill('Card number', '4111 1111 1111 1111')
    expect(screen.queryByText('Enter a valid card number.')).not.toBeInTheDocument()
  })

  it('reports an expired card', () => {
    render(<CardForm onValidityChange={() => {}} />)
    fill('Expiry (MM/YY)', '0120')
    fireEvent.blur(screen.getByLabelText('Expiry (MM/YY)'))
    expect(screen.getByText('Enter a valid expiry date (MM/YY).')).toBeInTheDocument()
  })

  it('never puts the card data on the page outside its own fields, and does not autofill into other inputs', () => {
    const { container } = render(<CardForm onValidityChange={() => {}} />)
    fillValidCard()
    const form = container.querySelector('.card-form')!
    expect(form.querySelectorAll('input[type="hidden"]')).toHaveLength(0)
    expect(screen.getByLabelText('CVV')).toHaveAttribute('type', 'password')
  })

  it('disables the fields when asked', () => {
    render(<CardForm onValidityChange={() => {}} disabled />)
    expect(screen.getByLabelText('Card number')).toBeDisabled()
  })
})
