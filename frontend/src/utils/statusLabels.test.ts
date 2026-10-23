import { describe, it, expect } from 'vitest'
import { bookingStatusLabel, paymentStatusLabel, propertyStatusLabel } from './statusLabels'
import { en } from '../i18n/messages/en'
import { ru } from '../i18n/messages/ru'
import { uz } from '../i18n/messages/uz'
import type { MessageKey } from '../i18n/messages/en'

const translator = (catalog: Record<string, string>) => (key: MessageKey) => catalog[key]

describe('status labels', () => {
  it('translate every booking, payment and property status in all three languages', () => {
    const bookings = ['pending', 'confirmed', 'cancelled', 'completed', 'no_show']
    const payments = ['pending', 'paid', 'failed', 'refunded', 'partially_refunded']
    const properties = ['draft', 'pending_approval', 'active', 'suspended', 'rejected']
    for (const catalog of [en, ru, uz]) {
      const t = translator(catalog)
      for (const code of bookings) expect(bookingStatusLabel(code, t)).not.toBe(code)
      for (const code of payments) expect(paymentStatusLabel(code, t)).not.toBe(code)
      for (const code of properties) expect(propertyStatusLabel(code, t)).not.toBe(code)
    }
  })

  it('page language: ru and uz read differently from en', () => {
    expect(bookingStatusLabel('confirmed', translator(en))).toBe('Confirmed')
    expect(bookingStatusLabel('confirmed', translator(ru))).toBe('Подтверждено')
    expect(propertyStatusLabel('pending_approval', translator(uz))).not.toBe(propertyStatusLabel('pending_approval', translator(en)))
  })

  it('an unknown code is shown as it came', () => {
    expect(bookingStatusLabel('on_hold', translator(en))).toBe('on_hold')
  })
})
