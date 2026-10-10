import { describe, it, expect, vi } from 'vitest'
import { generatePassword } from './generatePassword'

describe('generatePassword', () => {
  it('returns a password of the requested length from the allowed characters', () => {
    const password = generatePassword(16)

    expect(password).toHaveLength(16)
    expect(password).toMatch(/^[A-Za-z0-9!@#$%^&*]+$/)
  })

  it('uses the secure random source, never Math.random', () => {
    const secure = vi.spyOn(crypto, 'getRandomValues')
    const insecure = vi.spyOn(Math, 'random')

    generatePassword(16)

    expect(secure).toHaveBeenCalled()
    expect(insecure).not.toHaveBeenCalled()
    secure.mockRestore()
    insecure.mockRestore()
  })

  it('does not return the same password twice', () => {
    expect(generatePassword(16)).not.toBe(generatePassword(16))
  })

  it('has no modulo bias towards the first characters', () => {
    // 256 is not a multiple of the 70-character set; bytes above the last full multiple must be skipped
    const counts = new Map<string, number>()
    for (const ch of generatePassword(20000)) counts.set(ch, (counts.get(ch) ?? 0) + 1)
    const values = [...counts.values()]

    expect(Math.max(...values) / Math.min(...values)).toBeLessThan(1.6)
  })
})
