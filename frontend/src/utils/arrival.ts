// Cash at the hotel: the guest names an arrival time; the hotel waits this many hours more, then cancels.
// Same value as ARRIVAL_GRACE_HOURS on the backend (bookings/arrival.py), which does the cancelling.
export const ARRIVAL_GRACE_HOURS = 2

export const DEFAULT_ARRIVAL_TIME = '14:00'

import { BUSINESS_TIME_ZONE, businessToday } from './dates'

/** "10:30:00" (the API) or "10:30" -> "10:30" */
export const formatArrivalTime = (value: string): string => value.slice(0, 5)

/** Arriving today at a time that has already passed in the business time zone (the backend refuses it too) */
export function isArrivalPassed(checkIn: string, time: string, now: Date = new Date()): boolean {
  if (checkIn !== businessToday(now)) return false
  const nowInTashkent = new Intl.DateTimeFormat('en-GB', {
    timeZone: BUSINESS_TIME_ZONE, hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
  }).format(now)
  return time <= nowInTashkent
}

