# Plan: commission the site takes from hotel owners

Status: approved by the owner in chat (2026-10-31); built: backend (parts 1 and 2) and the screens (owner Commission section, super admin / staff Commission section, percent and role in the account forms, contact change in the users list), all in one pull request at the owner's request.

## Owner's rules
- Every hotel owner has one commission percent: what the site takes from each booking. The super admin types it when creating the owner (required). Existing owners have none until the super admin sets it; no percent means no commission.
- The site only calculates and shows it; no money moves through the site.
- Figures per month and per currency; per year only for an owner account at least one year old.
- Counted bookings: confirmed and completed (`COUNTED_STATUSES`), by the month of check-in. (The owner said "confirmed only"; a stay that has finished turns `completed`, so leaving it out would drop every finished stay. Say if you meant otherwise.)
- A percent applies from the month it is set; earlier months keep their old percent (or none).
- A staff admin or super admin confirms that an owner paid a month; the confirmer's name and role (super admin / admin) are shown with it. A month can only be confirmed after it has ended (my rule).
- The super admin and staff screen lists all owners and searches by owner name, e-mail, phone or hotel name. The owner sees the same figures for their own account.
- Only a super admin sets the percent; staff may confirm and take back a confirmation.

## Built (backend)
`partner/commission.py` (the rules), `partner/commission_views.py`, models `CommissionRate` and `CommissionPayment` (migration `partner/0003`), audit actions `commission_rate_set`, `commission_paid`, `commission_unpaid` (`admin_panel/0018`). Contract: `.ai/API_CONTRACT.md`.

## Decisions to confirm
- Per-month rounding (gross of the month x percent, rounded once to cents), not per booking.
- Months with no bookings are listed only for the current month.
- Currencies are never converted or added together.
