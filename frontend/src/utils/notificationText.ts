import type { AppNotification } from '../adapters/notificationAdapter'

/** Saytta óz uz/ru/en teksti bar kodlar (kilt ler `notification.<code>.title` hám `.message`) */
const KNOWN_CODES = new Set([
  'booking_confirmed', 'new_booking', 'booking_cancelled_by_guest', 'booking_not_arrived', 'guest_not_arrived',
  'no_show_marked', 'no_show_marked_no_refund', 'no_show_report_approved', 'no_show_report_rejected', 'refund_succeeded',
  'review_approved', 'review_rejected', 'new_review', 'review_reply',
  'ad_ending', 'ad_last_warning', 'ad_renewed', 'ad_removed', 'two_factor_reset',
])

type Translate = (key: string, params?: Record<string, string | number>) => string

/** Bet tilindegi sarlawha hám xabar; belgisiz kodlı (yamasa kodsız eski) xabarlandırıw inglizsha zapas tekstin kórsetedi */
export function notificationText(notice: AppNotification, t: Translate): { title: string; message: string } {
  if (!notice.code || !KNOWN_CODES.has(notice.code)) return { title: notice.title, message: notice.message }
  const params = notice.params ?? {}
  return {
    title: t(`notification.${notice.code}.title`, params),
    message: t(`notification.${notice.code}.message`, params),
  }
}
