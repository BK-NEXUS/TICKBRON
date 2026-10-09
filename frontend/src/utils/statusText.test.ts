import { describe, it, expect } from 'vitest'
import { statusText } from './statusText'
import { en } from '../i18n/messages/en'

const t = (key: string) => (en as Record<string, string>)[key] ?? key

describe('statusText', () => {
  it('translates a known booking or payment status', () => {
    expect(statusText('status.booking', 'no_show', t)).toBe('No-show')
    expect(statusText('status.payment', 'partially_refunded', t)).toBe('Partially refunded')
  })

  it('shows an unknown status capitalized instead of a missing key', () => {
    expect(statusText('status.booking', 'on_hold', t)).toBe('On_hold')
  })
})
