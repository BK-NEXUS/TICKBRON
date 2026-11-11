# TICKBRON AI Agent Memory

Bul `.ai` papkası AI coding agent'leri ushın turaqlı yad (memory) hám óz ara muwapıqlastırıw qatlamı.

## Haqıyqat deregi (Source of truth)
1. Git repository'diń haqıyqıy jaǵdayı
2. `.ai/` state/contract/checkpoint fayllar
3. `docs/` proekt hújjetleri
4. TICKBRON jobası (plan)

Jumıstı dawam ettiriw ushın chat tariyxı KEREK EMES.

## Májbúriy sikl
READ → SYNC → AUDIT → (PLAN + APPROVAL, tek qadaǵan etilgen itemler) → SCOPE LOCK → IMPLEMENT → TEST → SECURITY CHECK → CONTRACT CHECK → CHECKPOINT → COMMIT → PUSH → NEXT ITEM

Keyingi item qaǵıydası (2026-10-03, Kolya tárepinen tastıyıqlanǵan): Item merge etilip push etilgennen keyin `.ai/ROADMAP.md` ishindegi keyingi BACKEND itemge avtomat ótiledi. Tastıyıq qaqpası (approval gate): pul (baha, valyuta, tólem, qaytarıw), qáwipsizlik yamasa database migration'larǵa tiyetuǵın item `.ai/PLAN_<item>.md` (mısalı `PLAN_R6.md`) planınan baslanadı; ol push etiledi, iyesine qısqasha juwmaq kórsetiledi hám kodtı ózgertiwden aldın iyesiniń ANIQ tastıyıǵın KÚTIW kerek. Qalǵanı kútpesten dawam etedi.

## Iyelik hám jumıs tártibi
- Backend iyesi: Kolya. Frontend iyesi: Baxram.
- 2025-09-25'ten (Kolya hám Baxram tastıyıqlaǵan) Kolya'nıń agent'i `backend/` hám `frontend/` ekewinde de aldın sorawsız isley aladı.
- GitHub - ortaq sinxronlastırıw noqatı.
- Hár agent baslamastan aldın sońǵı remote ózgerislerdi pull etiwi kerek.
- Agent'ler kodtı ózgertiwden aldın sońǵı commit'lerdi hám `.ai` jaǵdayın tekseriwi kerek.
- Basqa adamnıń jumısın hesh qashan qayta jazbań.
- Merge/rebase conflict shıqsa, TOQTAŃ hám BLOCKED dep xabarlań. Conflict sheshimin boljap qoymań.

## Commit atı (Commit identity)
2026-09-25'ten Kolya agent'iniń commit'leri:
- Backend jumısı: `kolya - backend: <qısqa táriyp>`
- Frontend jumısı: `kolya - frontend: <qısqa táriyp>`
- Tek hújjet / `.ai`: `kolya - docs: <qısqa táriyp>`

Eski commit'ler óz atın saqlaydı: `baxram NN` (frontend checkpoint'ler), `kolya NN project` (backend checkpoint'ler) hám `kolya - <summary>`. Olardı qayta jazbań.

## Qorǵalǵan muwapıqlastırıw fayllar
Ortaq contract/state ózgerisleri ataylap hám hújjetlestirilgen bolıwı kerek:
- `.ai/API_CONTRACT.md`
- `.ai/HANDOFF.md`
- `.ai/PROJECT_STATE.md`
- `.ai/BACKEND_STATE.md`
- `.ai/FRONTEND_STATE.md`

## Account almastırıw
AI account'lar almasqanda keyingi agent:
1. `git pull`
2. sońǵı Git tariyxın tekseredi
3. `.ai/README.md` oqıydı
4. tiyisli state/progress/checkpoint fayllardı oqıydı
5. sońǵı checkpoint'ti haqıyqıy repository'de tekseredi
6. tiyisli testlerdi isletedi
7. tek dál keyingi checkpoint'ten dawam etedi

## E2E testlerdi isletiw (Playwright)
Playwright'ti `C:\Users\MicroStar\Desktop\TICKBRON\frontend` jolınan **Desktop** sózindegi **bas D** menen isletiń. Kishi háripli joldan (`...\desktop\...`) Windows `@playwright/test`'ti eki ret júkleydi hám hár isletiw "Playwright Test did not expect test() to be called here" hám "No tests found" menen tawsıladı. Aldın backend'ti (`seed_demo`, `seed_demo_stats`, `runserver 8000`, `THROTTLE_ANON_RATE` / `THROTTLE_USER_RATE` = `100000/hour`) hám `npm run dev`'ti iske túsiriń; `frontend/playwright.config.ts` qarań.

## Backend testler: hár sessiyaǵa bir test database
Bir PostgreSQL server'de eki pytest isletiwi ortaq test database paydalanbawı kerek: ekinshisi "database test_tickbron already exists / is being used" qátesi menen qulaydı yamasa jamanı, birinshiniń kestelerin óshiredi. Hár backend sessiya (developer terminal, hár Claude sessiya, hár worktree) pytest isletiwden aldın óz suffix'in óz shell'inde yamasa `backend/.env` ishinde qoyadı:

```
set TICKBRON_TEST_DB_SUFFIX=r12b        (PowerShell: $env:TICKBRON_TEST_DB_SUFFIX = "r12b")
venv\Scripts\python.exe -m pytest --create-db -q -n 8
```

Sonda test database `test_tickbron_r12b` boladı (xdist worker'ler `_gw0`, `_gw1`, ... qosadı). Tek háripler, sanlar hám `_`, eń kóp 30 belgi (`config/settings.py`, `core/tests/test_settings_defaults.py` tekseredi). Suffix bolmasa Django'nıń standart `test_tickbron`'ı paydalanıladı. Isletiwden aldın basqa sessiyalardı kóriw múmkin: `select datname, pid, state from pg_stat_activity where datname like 'test_tickbron%';`
