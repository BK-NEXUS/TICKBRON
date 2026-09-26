import type { User } from '../adapters/authAdapter'

// Mirrors the backend permission classes: partner.views.IsHotelOwner and
// admin_panel.views.IsSuperAdminOrStaff. The backend is the real check;
// these only decide what the UI shows.

export const HOTEL_OWNER_ROLE = 'hotel-owner'

export function canUseAdminPanel(user: User | null | undefined): boolean {
  return Boolean(user && (user.is_staff || user.is_superuser))
}

export function canUsePartnerPanel(user: User | null | undefined): boolean {
  return Boolean(user && (user.role === HOTEL_OWNER_ROLE || canUseAdminPanel(user)))
}
