import { describe, it, expect } from 'vitest'
import { newPasswordProblem, passwordFormatProblem } from './passwordRules'

describe('passwordFormatProblem', () => {
  it.each(['sayr5$ol', 'KITOB7#YOZ', 'Fresh9Grape#Tower42', 'Хорошо7!ok', 'bu yol9! ok', 'sayr5_ol'])(
    'accepts %s',
    (password) => {
      expect(passwordFormatProblem(password)).toBeNull()
    },
  )

  it('reports fewer than 8 characters', () => {
    expect(passwordFormatProblem('sayr5$o')).toBe('short')
  })

  it('reports a password without a letter', () => {
    expect(passwordFormatProblem('12345678')).toBe('noLetter')
    expect(passwordFormatProblem('!@#$%^&*')).toBe('noLetter')
  })

  it('reports a password without a digit', () => {
    expect(passwordFormatProblem('kitobyoz#')).toBe('noDigit')
  })

  it('reports a password without a special character; a space is not one', () => {
    expect(passwordFormatProblem('kitobyoz7')).toBe('noSpecial')
    expect(passwordFormatProblem('kitob7  yoz')).toBe('noSpecial')
  })
})

describe('newPasswordProblem', () => {
  it('accepts a good password typed twice', () => {
    expect(newPasswordProblem('Fresh9Grape#Tower42', 'Fresh9Grape#Tower42')).toBeNull()
  })

  it('reports different texts before anything else', () => {
    expect(newPasswordProblem('short', 'other')).toBe('mismatch')
  })

  it('reports a password shorter than 8 characters', () => {
    expect(newPasswordProblem('Sh#1abc', 'Sh#1abc')).toBe('short')
  })

  it('accepts exactly 8 characters', () => {
    expect(newPasswordProblem('Abcdef#1', 'Abcdef#1')).toBeNull()
  })

  it('reports a missing character kind', () => {
    expect(newPasswordProblem('abcdefgh#', 'abcdefgh#')).toBe('noDigit')
  })
})
