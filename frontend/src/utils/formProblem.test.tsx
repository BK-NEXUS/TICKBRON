import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { firstFormProblem, formAccepts } from './formProblem'
import { englishI18n } from '../i18n/I18nContext'

const t = englishI18n.t

function Form({ children }: { children: React.ReactNode }) {
  return <form aria-label="demo" noValidate>{children}</form>
}

const form = () => screen.getByRole('form', { name: 'demo' }) as HTMLFormElement

describe('firstFormProblem: the site words what the browser would have said', () => {
  it('a required field that is empty names itself by its label (the star is dropped)', () => {
    render(<Form><label htmlFor="n">Room name *</label><input id="n" required /></Form>)
    expect(firstFormProblem(form(), t)?.message).toBe('Room name is required.')
  })

  it('a trailing colon of the label is dropped', () => {
    render(<Form><label htmlFor="n">First Name:</label><input id="n" required /></Form>)
    expect(firstFormProblem(form(), t)?.message).toBe('First Name is required.')
  })

  it('a field without a label is named by its aria-label', () => {
    render(<Form><input aria-label="Phone" required /></Form>)
    expect(firstFormProblem(form(), t)?.message).toBe('Phone is required.')
  })

  it('a malformed e-mail gets the e-mail message', () => {
    render(<Form><label htmlFor="e">Email</label><input id="e" type="email" defaultValue="nope" /></Form>)
    expect(firstFormProblem(form(), t)?.message).toBe('Enter a valid email address.')
  })

  it('a number under the minimum and over the maximum', () => {
    render(<Form><label htmlFor="r">Rooms</label><input id="r" type="number" min="1" max="10" defaultValue="0" /></Form>)
    expect(firstFormProblem(form(), t)?.message).toBe('Rooms cannot be less than 1.')
    fireEvent.change(screen.getByLabelText('Rooms'), { target: { value: '11' } })
    expect(firstFormProblem(form(), t)?.message).toBe('Rooms cannot be more than 10.')
  })

  it('too short and too long text', () => {
    render(<Form><label htmlFor="c">Code</label><input id="c" minLength={3} maxLength={5} defaultValue="ab" /></Form>)
    const input = screen.getByLabelText('Code') as HTMLInputElement
    // The browser only flags length for what the user typed; the helper checks the value itself
    expect(firstFormProblem(form(), t)?.message).toBe('Code needs at least 3 characters.')
    fireEvent.change(input, { target: { value: 'abcdefg' } })
    expect(firstFormProblem(form(), t)?.message).toBe('Code can have at most 5 characters.')
  })

  it('a value that does not match its pattern', () => {
    render(<Form><label htmlFor="p">Code</label><input id="p" pattern="[0-9]+" defaultValue="abc" /></Form>)
    expect(firstFormProblem(form(), t)?.message).toBe('Code is not valid.')
  })

  it('returns the first problem in page order, with its field', () => {
    render(<Form>
      <label htmlFor="a">First</label><input id="a" defaultValue="fine" required />
      <label htmlFor="b">Second</label><input id="b" required />
      <label htmlFor="c">Third</label><input id="c" required />
    </Form>)
    const problem = firstFormProblem(form(), t)
    expect(problem?.message).toBe('Second is required.')
    expect(problem?.field).toBe(screen.getByLabelText('Second'))
  })

  it('is null for a valid form and ignores disabled fields', () => {
    render(<Form><label htmlFor="a">A</label><input id="a" defaultValue="x" required /><input aria-label="B" required disabled /></Form>)
    expect(firstFormProblem(form(), t)).toBeNull()
  })
})

describe('formAccepts', () => {
  it('reports the problem through the callback, focuses the field and says no', () => {
    render(<Form><label htmlFor="n">Name</label><input id="n" required /></Form>)
    const report = vi.fn()
    expect(formAccepts(form(), t, report)).toBe(false)
    expect(report).toHaveBeenCalledWith('Name is required.')
    expect(screen.getByLabelText('Name')).toHaveFocus()
  })

  it('says yes without reporting for a valid form', () => {
    render(<Form><label htmlFor="n">Name</label><input id="n" defaultValue="x" required /></Form>)
    const report = vi.fn()
    expect(formAccepts(form(), t, report)).toBe(true)
    expect(report).not.toHaveBeenCalled()
  })
})
