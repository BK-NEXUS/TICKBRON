// Mehmanxanada naqd: mehmann keliw waqtın aytadı; mehmanxana taǵı usı saat kútedi, keyin biykar etedi.
// Backend degi ARRIVAL_GRACE_HOURS penen birdey mánis (bookings/arrival.py), biykar etiwdi sol isleydi.
export const ARRIVAL_GRACE_HOURS = 2

export const DEFAULT_ARRIVAL_TIME = '14:00'

import { BUSINESS_TIME_ZONE, businessToday } from './dates'

/** "10:30:00" (API) yamasa "10:30" -> "10:30" */
export const formatArrivalTime = (value: string): string => value.slice(0, 5)

/** Is waqıt zonasında ótip ketken waqıtqa búgin keliw (backend te onı qabıllamaydı) */
export function isArrivalPassed(checkIn: string, time: string, now: Date = new Date()): boolean {
  if (checkIn !== businessToday(now)) return false
  const nowInTashkent = new Intl.DateTimeFormat('en-GB', {
    timeZone: BUSINESS_TIME_ZONE, hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
  }).format(now)
  return time <= nowInTashkent
}

