export interface StayDates {
  check_in: string
  check_out: string
  status: string
}

/**
 * Mehmannıń aktiv bronlarınıń biri usı sanalar menen bir túndi bólisse true (YYYY-MM-DD).
 * Shıǵıw kúni bos, sol sebepli turıw basqası pitken kúni baslana aladı. Backend sheshedi; bul
 * tek jibermesten aldın mehmanǵa aytadı.
 */
export function overlapsOwnStay(own: StayDates[], checkIn: string, checkOut: string): boolean {
  return own.some(stay =>
    (stay.status === 'pending' || stay.status === 'confirmed') && stay.check_in < checkOut && stay.check_out > checkIn)
}
