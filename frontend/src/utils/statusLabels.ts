import type { MessageKey } from '../i18n/messages/en'

type Translate = (key: MessageKey) => string

const BOOKING: Record<string, MessageKey> = {
  pending: 'status.booking.pending',
  confirmed: 'status.booking.confirmed',
  cancelled: 'status.booking.cancelled',
  completed: 'status.booking.completed',
  no_show: 'status.booking.no_show',
}

const PAYMENT: Record<string, MessageKey> = {
  pending: 'status.payment.pending',
  paid: 'status.payment.paid',
  failed: 'status.payment.failed',
  refunded: 'status.payment.refunded',
  partially_refunded: 'status.payment.partially_refunded',
}

const PROPERTY: Record<string, MessageKey> = {
  draft: 'propertyStatus.draft',
  pending_approval: 'propertyStatus.pending_approval',
  active: 'propertyStatus.active',
  suspended: 'propertyStatus.suspended',
  rejected: 'propertyStatus.rejected',
}

/** A status the API sends as a code, in the page language; an unknown code is shown as it came. */
const label = (keys: Record<string, MessageKey>, status: string, t: Translate) => (keys[status] ? t(keys[status]) : status)

export const bookingStatusLabel = (status: string, t: Translate) => label(BOOKING, status, t)
export const paymentStatusLabel = (status: string, t: Translate) => label(PAYMENT, status, t)
export const propertyStatusLabel = (status: string, t: Translate) => label(PROPERTY, status, t)
