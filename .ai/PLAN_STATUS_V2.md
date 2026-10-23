# Plan: Status v2 (2026-10-23)

Why: the owner found the Status screen confusing (one long page) and wants more numbers: earnings per month, guests coming, which room types are booked most. Commission work is parked.

## Owner Status (this PR)
- Four tabs: **Overview** (this month against last month, guests in the next 7 days, key numbers of the chosen period, yearly charts, hotels table), **Rooms** (room types ranked by bookings), **Arrivals** (today and tomorrow, unchanged), **Reports** (the old full report: stayed, insights, status counts, series, reconciliation, CSV/Excel).
- New numbers: booked ahead (average days between booking and check-in), returning guests (%), month comparison, room type ranking.
- One module for the rules: `bookings/metrics.py` (`month_comparison`, `room_type_stats`, `average_lead_days`, `repeat_guest_pct`); views stay thin.

## Admin Status (done)
- An Overview tab (platform-wide, same helpers) plus the existing Countries / Hotels / Users; admin language switch must translate every button, filter and type label (verified by switching languages).
