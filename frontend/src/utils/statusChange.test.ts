import { describe, it, expect } from 'vitest'
import { monthChange } from './statusChange'

const t = (key: string, params?: Record<string, string | number>) => `${key}${params ? JSON.stringify(params) : ''}`

describe('monthChange', () => {
  it('says "up" with the size for a rise and "down" for a fall', () => {
    expect(monthChange('25.0', t as never)).toEqual({ text: 'ownerStatus.change.up{"value":"25.0"}', tone: 'up' })
    expect(monthChange('-12.34', t as never)).toEqual({ text: 'ownerStatus.change.down{"value":"12.3"}', tone: 'down' })
  })

  it('says "same" for zero and "none" when last month was empty', () => {
    expect(monthChange('0.0', t as never).tone).toBe('same')
    expect(monthChange(null, t as never)).toEqual({ text: 'ownerStatus.change.none', tone: 'none' })
  })
})
