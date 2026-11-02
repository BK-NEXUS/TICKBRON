import { describe, expect, it } from 'vitest'
import { profile } from './profile'

describe('profile data', () => {
  it('has five certificates with unique ids', () => {
    const ids = profile.certificates.map((c) => c.id)
    expect(ids).toHaveLength(5)
    expect(new Set(ids).size).toBe(5)
  })

  it('uses only https or mailto social links', () => {
    for (const link of profile.socials) {
      expect(link.href).toMatch(/^(https:\/\/|mailto:)/)
    }
  })

  it('points the website to an https url', () => {
    expect(profile.website.url).toMatch(/^https:\/\//)
  })
})
