# CLIENT DECISIONS (buyırtpashıdan kerek qararlar; Word fayl retinde jiberilgen, 2026-10-12)

Jaǵday: bólekshe JUWAP ALINǴAN (2026-10-12, iyesi tárepinen). Usınıslar - meniki. Keyin onlayn tólem alıp taslandı (naqd tólem, `PLAN_CASH_ONLY.md`), sonıń ushın qaytarıw (refund) haqqındaǵı punktler tariyxıy.

## Alınǵan juwaplar
1. Tólengen bronnı biykar etiw: A variant (rate plan boyınsha); qaytarıw 50%. Ashıq punktler: 50% kelip jetiwden aldın qálegen waqıtta qollanılama, hám biypul biykar etiw aynası barma. Aytılmaǵansha standart: qálegen waqıtta 50%, rate plan procent hám aynanı ózgerte aladı.
2. Kim qaytaradı: iyesi qarar etpedi, másláhát soradı. Meniń másláhátim: tek super-admin, sebep májbúriy (biykar etiw hám no-show qaytarıwları avtomat qaǵıydalarǵa aylanadı, sonıń ushın qolda qaytarıwlar - istisna).
3. No-show: A variant (50% qaldırıw, 7 kún, staff qarar etedi).
4. VIP: B variant (xona túrindegi flag, mehmanxana iyesi qoyadı, admin tastıyıqlaydı). Bólek izlew filtri tańlanbadı.
5. JAŃA hám qarar etilmegen: mehmanxanalarǵa qalay tólenedi. Iyesiniń házirge jobası joq: yamasa hár mehmanxana óz kartasın/merchant'ın dizimnen ótkeredi (Uzum Market satıwshıları sıyaqlı) hám pul oǵan baradı, yamasa pútkil pul platforma akkauntına baradı hám admin mehmanxanalarǵa aylıq tóleydi. Meniń másláhátim: aldın platforma akkaunti, aylıq tólewler (bir provayder shártnaması, ápiwayı qaytarıwlar); komissiya, hár mehmanxananıń balans ledger'i, aylıq esabat, "tólengen" jazıwları hám CSV, iyesiniń balans ekranı kerek. Úshinshi tárep qarjısın uslaw boyınsha buxgalter/yurist pikiri kerek. Hár qanday koddan aldın óz tastıyıqlanǵan jobası kerek.

## Dáslepki sorawlar

| # | Qarar | Házir | Variantlar | Usınıs | Juwap |
|---|---|---|---|---|---|
| 1 | Tólengen bronnı biykar etiw (N-16) | Mehmanlar hár qanday juwmaqlanbaǵan bronnı qálegen waqıtta biykar ete aladı; inventory bosatıladı (`Booking.cancel_booking`); qaytarıw jaratılmaydı (staff qolda qaytara aladı) | A rate plan boyınsha: biypul biykar etiw deadline + qaytarıw procenti; B hámme ushın bir qaǵıyda; C tólemnen keyin biykar etiw joq | A, standart 100% qaytarıw kelip jetiwden 48 saat aldınǵa shekem, keyin 0%, hár rate plan boyınsha; summa backend'te esaplanadı | |
| 2 | Kim qaytarıwı múmkin (N-14) | Qálegen `is_staff` paydalanıwshı refund jaratadı (`payments/views.py:327`); retry/mark-done tek super-admin | A tek super-admin; B staff shekke shekem, odan joqarı super-admin; C hámme staff, biraq sebep májbúriy hám jazıladı | B, sebep hár waqıt májbúriy; audit log qosıladı (2a qádem) | |
| 3 | "Kelmadi" (no-show) qaǵıydaları | Iyesi 7 kún ishinde xabarlaydı (`NO_SHOW_REPORT_WINDOW_DAYS`), staff qarar etedi, mehman 50% aladı (`NO_SHOW_REFUND_PERCENT`) | A qaldırıw; B basqa procent/mudet | Aldın A, haqıyqıy jaǵdaylardan keyin qaytadan kóriw | |
| 4 | VIP xona | Bunday túsinik joq | A baha dárejesi; B xona túri flag'ı iyesi qoyadı, admin tastıyıqlaydı; C qosımsha xızmetler toplamı; D izlew filtri hám dizim | B + D; xızmetler keyinirek | |
| 5 | Basqa | n/a | komissiya hám tólem modeli; karta xızmeti (Google/Yandex/OpenStreetMap); logo fayllar; Telegram bot token; arzanlatıw túrleri (R10b); dizimnen ótiw forması maydanları (buyırtpashı at, telefon, email soradı: parol kerekpe?) | n/a | |

Hár juwap koddı neni ózgertetuǵını juwap kelgende `.ai/PLAN_*.md` ishinde jobalastırıladı (pul qaǵıydaları aldın tastıyıqlanǵan joba talap etedi).
