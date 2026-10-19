# PLAN R16: prices in four currencies, entered by the hotel owner; easy to add currencies and languages

Status: APPROVED by the owner 2026-10-19: (1) the guest pays in so'm using the owner's so'm price (recommended option a); (2) all four currencies are mandatory (new rate plans at once; existing ones when they are next edited, until then the other currencies show as converted); (3) date-specific prices follow the plan's ratio in the other currencies. S1 backend in progress.

## What the owner asked for (2026-10-19)
- The hotel owner enters the price of a room himself in several currencies (USD, so'm, tenge, ruble), because exchange rates change.
- Four currencies now: **USD, UZS (so'm), KZT (tenge), RUB (ruble)**. Three languages now: **English, Uzbek, Russian**.
- Adding another currency or language later must be easy (tomorrow, after the site launches).

## Today (facts from the code)
- A rate plan, room type and date price have ONE `base_price` + ONE `currency` (`properties/models.py`); `common/money.py` allows only `UZS` and `USD`.
- Guests are charged in UZS (Payme and Click take only UZS); a USD hotel is converted with the CBU rate, snapshotted on the booking (`exchange_rate*`, `charge_*`).
- The header currency selector exists but changes nothing real (the backend sends no price in a second currency).

## Design
1. **One registry of currencies** (backend `common/money.py`, frontend `i18n/options.ts`): code, name keys, number of decimals, symbol/format. Adding a currency = one line in each registry + translations of its name + (for the fallback below) a CBU rate fetch. Same for languages: one list (code, name, locale) feeding the selector, the catalogs and the date/number formats; a short "how to add a language / currency" note in `.ai/`.
2. **Price list per rate plan:** new table `RatePlanPrice(rate_plan, currency, amount)`, unique per (rate plan, currency). The existing `base_price` + `currency` stay as the hotel's main price (nothing existing breaks, old bookings untouched).
3. **What a guest sees in currency X:** the owner's own price in X if he entered one; otherwise the main price converted with the CBU rate and shown with "≈" (today's behaviour). The API says which one it is (`price_source: owner | converted`).
4. **Date-specific prices** (high season, `DateInventory.price`): the owner enters them in the main currency; the other currencies follow the same ratio as that plan's price list (e.g. +20% in so'm = +20% in dollars). No four boxes per date.
5. **Owner screens:** the room/rate-plan form gets one price box per currency (main one required, the others optional with a hint "leave empty to convert automatically, shown as ≈"). A banner for existing hotels: "Set your prices in other currencies".
6. **Guest screens:** the header currency selector becomes real (4 currencies, remembered), search cards, hotel page, booking summary and quote show prices in it.
7. **Booking and payment** (see question 1): the booking stores the currency the guest chose, the price list used and the amount charged. Prices are always computed on the backend; the frontend only displays.
8. **Status / revenue:** stays per currency (never added together), now with four currencies.
9. **CBU rates** for KZT and RUB are fetched like USD (fallback conversion and reports).

## Slices (one PR each; tests first; contract in API_CONTRACT.md; note in HANDOFF.md)
- S1 backend (done): currency registry (`common/money.py CURRENCIES`), CBU fetch for KZT and RUB, `RatePlanPrice` + migration `properties/0016` (additive, reversible, no backfill), price rules in `bookings/pricing.py`, owner write API (`prices`), `prices` on the hotel page, `currency` on the quote, booking charge from the owner's so'm price. The mandatory rule is behind `RATE_PLAN_PRICES_REQUIRED` (default off) so the current owner screens keep working until S3 sends the four prices; S3 flips the default.
- S2 backend: booking and charge rules, CBU for KZT/RUB, status in four currencies.
- S3 frontend: owner price boxes and banner.
- S4 frontend: real currency selector and price display everywhere.
- S5 docs + registry test ("adding a currency touches only the registry").

## Questions for the owner (default in brackets)
1. **In which currency does the guest actually pay?** (a) Always in so'm, using the owner's so'm price; the other currencies are shown for information. Payme and Click work today. [recommended] (b) In the currency the guest chose (dollar, tenge, ruble); needs a payment provider that takes it, which is not confirmed, so those methods stay off until the provider says yes.
2. **If the owner leaves a currency empty**, is it OK to show the converted price with "≈" for it? [yes: nothing breaks for existing hotels; the owner is reminded by a banner] Or must all four be filled before a room can be published?
3. **Date-specific prices** follow the same ratio in the other currencies (point 4)? [yes]
