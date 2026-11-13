import type { User } from '../adapters/authAdapter'

// Backend ruxsat klasların kórsetedi: partner.views.IsHotelOwner hám
// admin_panel.views.IsSuperAdminOrStaff. Haqıyqıy tekseriw backend te;
// bular tek UI ne kórsetetuǵının sheshedi.

export const HOTEL_OWNER_ROLE = 'hotel-owner'

export function canUseAdminPanel(user: User | null | undefined): boolean {
  return Boolean(user && (user.is_staff || user.is_superuser))
}

export function canUsePartnerPanel(user: User | null | undefined): boolean {
  return Boolean(user && (user.role === HOTEL_OWNER_ROLE || canUseAdminPanel(user)))
}
