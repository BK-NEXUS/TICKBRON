import { describe, expect, it } from 'vitest'
import type { AppNotification } from '../adapters/notificationAdapter'
import { translate } from '../i18n/translateNow'
import { notificationText } from './notificationText'

const notice = (code: string): AppNotification => ({
  id: 1, code, params: { review_id: 3, property_id: 5, promotion_id: 7, end_date: '2026-11-30', until_date: '2026-12-05' }, title: 'English title', message: 'English message',
  is_read: false, booking: null, created_at: '2026-10-28T10:00:00Z',
})

const REVIEW_CODES = ['review_approved', 'review_rejected', 'new_review', 'review_reply']
const AD_CODES = ['ad_ending', 'ad_last_warning', 'ad_renewed', 'ad_removed']

describe('notificationText for the review and ad notices', () => {
  it.each(['uz', 'ru', 'en'] as const)('has its own text in %s for every review and ad code', (language) => {
    const t = (key: string, params?: Record<string, string | number>) => translate(language, key, params)
    for (const code of [...REVIEW_CODES, ...AD_CODES]) {
      const text = notificationText(notice(code), t)
      expect(text.title, code).not.toBe('English title')
      expect(text.message, code).not.toBe('English message')
      expect(text.title + text.message, code).not.toContain('notification.')
      expect(text.title + text.message, code).not.toContain('{')
    }
  })

  it('still falls back to the English text for a code it does not know', () => {
    const text = notificationText(notice('something_new'), (key) => key)
    expect(text).toEqual({ title: 'English title', message: 'English message' })
  })
})
