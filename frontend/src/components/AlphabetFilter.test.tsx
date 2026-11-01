import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { AlphabetFilter } from './AlphabetFilter'
import { nameMatchesLetter } from '../utils/alphabet'
import { I18nProvider } from '../i18n/I18nContext'

function show(value = '', language: 'en' | 'ru' | 'uz' = 'en') {
  localStorage.setItem('tickbron.language', language)
  const onChange = vi.fn()
  render(<I18nProvider><AlphabetFilter value={value} onChange={onChange} /></I18nProvider>)
  return onChange
}

describe('AlphabetFilter', () => {
  beforeEach(() => { localStorage.clear() })

  it('offers All, the 26 Latin letters and # in English and Uzbek', () => {
    show()
    expect(screen.getByRole('button', { name: 'All' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: 'Names starting with A' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Names starting with Z' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Names that do not start with a letter' })).toBeInTheDocument()
    expect(screen.getAllByRole('button').length).toBe(1 + 26 + 1 + 1)  // All, A-Z, #, the script switch
  })

  it('shows the Cyrillic letters when the page is Russian', () => {
    show('', 'ru')
    expect(screen.getByRole('button', { name: 'Имена на букву Я' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Имена на букву Ў' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Имена на букву Q' })).not.toBeInTheDocument()
  })

  it('switches between the two scripts by hand', () => {
    show()
    fireEvent.click(screen.getByRole('button', { name: 'А-Я' }))
    expect(screen.getByRole('button', { name: 'Names starting with Қ' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'A-Z' }))
    expect(screen.getByRole('button', { name: 'Names starting with Q' })).toBeInTheDocument()
  })

  it('picks a letter, marks it, and picks it again to clear it', () => {
    const onChange = show('B')
    expect(screen.getByRole('button', { name: 'Names starting with B' })).toHaveAttribute('aria-pressed', 'true')
    fireEvent.click(screen.getByRole('button', { name: 'Names starting with C' }))
    expect(onChange).toHaveBeenLastCalledWith('C')
    fireEvent.click(screen.getByRole('button', { name: 'Names starting with B' }))
    expect(onChange).toHaveBeenLastCalledWith('')
  })

  it('sends # for the names without a letter and "" for All', () => {
    const onChange = show('A')
    fireEvent.click(screen.getByRole('button', { name: 'Names that do not start with a letter' }))
    expect(onChange).toHaveBeenLastCalledWith('#')
    fireEvent.click(screen.getByRole('button', { name: 'All' }))
    expect(onChange).toHaveBeenLastCalledWith('')
  })

  it('opens on Cyrillic when the chosen letter is Cyrillic', () => {
    show('Я')
    expect(screen.getByRole('button', { name: 'Names starting with Я' })).toHaveAttribute('aria-pressed', 'true')
  })
})

describe('nameMatchesLetter', () => {
  it.each([
    ['Aziz Karimov', 'A', true], ['aziz', 'A', true], ['Bobur', 'A', false], ['  Anvar', 'A', true], ['Азиз', 'А', true],
    ['азиз', 'А', true], ['1st Guest', '#', true], ['"Quoted"', '#', true], ['Aziz', '#', false], ['Aziz', '', true], ['', '#', false],
  ])('%s under %s is %s', (name, letter, expected) => {
    expect(nameMatchesLetter(name, letter)).toBe(expected)
  })
})
