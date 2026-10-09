===== PLAN: R5 languages foundation (frontend only) =====
Scope: the base only. No backend change, no migration, no price conversion.
- `src/i18n/`: own small provider (no new dependency): `I18nProvider`, `useI18n()` -> `{ language, setLanguage, currency, setCurrency, t, formatMoney }`.
- Languages: uz (Latin, default when the browser language is none of the three), ru, en. Currencies: UZS (default), USD. Choice is remembered in localStorage (wrapped in try/catch) and `<html lang>` follows the language.
- Message catalogs `messages/{en,uz,ru}.ts`: flat keys; a test fails when a key is missing in any language or has different {placeholders}. Fallback at runtime: language -> en -> key.
- `formatMoney(amount, currency, language)`: UZS "1 250 000 so'm" (uz), "1 250 000 сум" (ru), "1 250 000 UZS" (en); USD "$1,250.00". Display only: totals are computed by the backend; showing an amount converted to the other currency waits for the R6 rate fields (frontend item 3).
- Selectors: only uz/ru/en and UZS/USD; flags are inline SVG components (no emoji, no stickers); chevron/check are lucide icons.
- Header and nav labels use `t()` as the first consumer. Moving the other strings is the next item (8 chunks); uz and ru texts need a native-speaker review.
- The i18n files of LanguageSelector/CurrencySelector leave the emoji allowlist.
Tests first: format, provider (default, persistence, fallback, html lang), catalog parity, selectors, Header language switch.
===== END OF PLAN =====
