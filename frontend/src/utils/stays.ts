export interface StayDates {
  check_in: string
  check_out: string
  status: string
}

/**
 * True when one of the guest's live bookings shares a night with these dates (YYYY-MM-DD).
 * The check-out day is free, so a stay may start the day another ends. The backend decides; this
 * only tells the guest before sending.
 */
export function overlapsOwnStay(own: StayDates[], checkIn: string, checkOut: string): boolean {
  return own.some(stay =>
    (stay.status === 'pending' || stay.status === 'confirmed') && stay.check_in < checkOut && stay.check_out > checkIn)
}
