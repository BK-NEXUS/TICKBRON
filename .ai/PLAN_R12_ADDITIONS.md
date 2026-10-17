# PLAN R12 additions (Status: comparison, rates, averages, Excel, owner rank)

Status: APPROVED by the owner 2026-10-17: Q1 yes, Q2 by number of bookings, Q3 yes (5), Q4 library chosen by me: XlsxWriter (write-only, small, no extra dependencies; openpyxl is only needed to read files).

## Already built (do not redo)
CSV export (admin lists, owner reconciliation), owner "arriving today/tomorrow" (`/partner/status/arrivals/`), periods, series, totals with all counts (`bookings/metrics.py`).

## Still missing, in 4 slices
1. **Backend numbers** (one module, `bookings/metrics.py`, same for admin and owner; read only, no migration, no money rule changed):
   - `previous_period`: the same totals for the period right before (same length), plus `change_pct` per number (`null` when the previous value is 0). Not for `all`.
   - `cancellation_rate` = cancelled (not expired) / (cancelled + counted + no_show) bookings in the period, in percent.
   - `occupancy_rate` = room_nights / (sum of `total_rooms` of the hotel x days in the period), in percent, never above 100. Owner and hotel detail only.
   - `average_booking_value` per currency (booking_value / bookings) and `average_stay_nights` (nights / bookings).
2. **Owner anonymous rank**: "your hotel is #N of M in your region" by number of counted bookings in the period. Only the owner's own position and the count M are returned, never other hotels' names or numbers. Region with fewer than 5 hotels: no rank.
3. **Excel export** (`?export=xlsx`) next to CSV, same permissions, row limit and audit log. Needs the new library `XlsxWriter` in requirements.
4. **Frontend**: +/- % chips on the stat cards, the new cards, rank card, "Download Excel" button; uz/ru/en keys; 390px and 1440px checks.

Each slice: tests first, contract in `API_CONTRACT.md`, note in `HANDOFF.md`, one PR per slice.

## Questions for the owner (defaults in brackets)
1. Occupancy: count only available room-nights as above (hotel rooms x days)? [yes]
2. Rank: by what? stayed nights [yes] / revenue / number of bookings.
3. Rank: hide it if the region has fewer than 5 hotels, so nobody can guess who is who? [yes, 5]
4. Excel: OK to add the library `openpyxl`? [yes]
