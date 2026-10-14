import { describe, it, expect } from 'vitest'
import { newPasswordProblem } from './passwordRules'

describe('newPasswordProblem', () => {
  it('accepts a long password typed twice', () => {
    expect(newPasswordProblem('Fresh9Grape#Tower42', 'Fresh9Grape#Tower42')).toBeNull()
  })

  it('reports different texts before anything else', () => {
    expect(newPasswordProblem('short', 'other')).toBe('mismatch')
  })

  it('reports a password shorter than 12 characters', () => {
    expect(newPasswordProblem('Short#1abc', 'Short#1abc')).toBe('short')
  })

  it('accepts exactly 12 characters', () => {
    expect(newPasswordProblem('Abcdefgh#123', 'Abcdefgh#123')).toBeNull()
  })
})
