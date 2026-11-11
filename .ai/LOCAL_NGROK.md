# TICKBRON'dı óz kompyuterińizde isletip, ngrok arqalı kórsetiw

Frontend dev server'ine bir ngrok tunnel jetkilikli. Bet hám API bir mánzilde boladı: dev server (Vite) `/api` hám `/media`'nı backend'ke jiberedi, sonıń ushın cookie, CORS yamasa mixed-content mashqalaları bolmaydı.

## Bir buyrıq (Windows)
`powershell -ExecutionPolicy Bypass -File scripts\demo-tunnel.ps1` database'di (Docker) iske túsiredi, saytıń build'in qurıp xızmet etedi, ngrok'ti iske túsiredi, tunnel mánzilin `backend/.env` ishindegi `CSRF_TRUSTED_ORIGINS`'ke qoyadı, backend'ti iske túsiredi hám testlewshi ushın mánzildi shıǵaradı. `-Stop` hámmesin toqtatadı. Tómendegi bir martalıq sazlawdı talap etedi. Qurılǵan sayt (`npm run dev` emes) xızmet etiledi, sebebi dev server júzlegen kishi fayl jiberedi hám tunnel arqalı ol ásta.
`backend/.env` ishinde `DB_HOST=127.0.0.1` jazıń, `localhost` emes: Windows'ta `localhost` aldın IPv6 menen sınalıp, hár jańa database baylanısı 2 sekund kútip turdı (hár API juwabı 0.06 s orniǵa 2.1 s aldı).

## Bir martalıq sazlaw
1. PostgreSQL, Redis, Python 3.13, Node 22 hám [ngrok](https://ngrok.com/download) ornatıń; bir ret `ngrok config add-authtoken <sizdiń token>` isletiń.
2. Database (bir ret): `backend/.env.dev.example` ishinde atalǵan user hám database jaratıń (`tickbron_user` / `tickbron`).
3. Backend:
   ```
   cd backend
   python -m venv venv && source venv/bin/activate     # Windows: venv\Scripts\activate
   pip install -r requirements-dev.txt
   cp .env.dev.example .env
   python manage.py migrate
   python manage.py seed_property_types
   python manage.py createsuperuser                    # sizdiń administratorıńız
   ```
   Iqtıyarıy demo mehmanxanalar hám akkauntlar (tek DEBUG qosılǵanda isleydi): `python manage.py seed_demo`.
4. Frontend:
   ```
   cd frontend
   npm ci
   cp .env.example .env.local
   ```
   `frontend/.env.local` ishinde `VITE_API_BASE_URL=` qatarın **bos mánis** etip qoyıń (`=` den keyin hesh nárse).

## Hár ret
Tórt terminal:
```
redis-server                                         # 1 (service retinde islese, ótkizip jiberiń)
cd backend && source venv/bin/activate && python manage.py runserver     # 2
cd frontend && npm run dev                           # 3  (3000 port)
ngrok http 3000                                      # 4
```
ngrok `https://abc-123.ngrok-free.app` sıyaqlı mánzil shıǵaradı. Keyin:
1. `backend/.env` ishinde sol mánzildi (`https://` penen, sońında slash joq) `CSRF_TRUSTED_ORIGINS`'ke eki local mánzilden keyin qosıń, mısalı `CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,https://abc-123.ngrok-free.app`. Mail'lerdegi siltemeler (backend console'ǵa shıǵadı) sonda bariwın qalasańız, `FRONTEND_URL`'di de sonday qoyıń.
2. Backend'ti qayta iske túsiriń (2-qádem). Biypul ngrok mánzili hár ngrok iske túskende ózgeredi, sonıń ushın qaytalań; ngrok dashboard'tan alınǵan turaqlı (static) domen buǵan jol bermeydi.
3. ngrok mánzilin ashıń. Birinshi kirisiw ngrok eskertiw betin kórsetedi: "Visit Site" basıń.

Dev server `*.ngrok-free.app`, `*.ngrok-free.dev`, `*.ngrok.app`, `*.ngrok.dev` hám `*.ngrok.io` host'ların qabıl etedi. Ele de "Blocked request" desse, óz host'ıńızdı `frontend/vite.config.ts` ishindegi `TUNNEL_HOSTS`'ke qosıń.

## Turaqlıraq demo (hot reload joq)
```
cd frontend && npm run build && npm run preview -- --port 3000
```
`preview` qurılǵan saytqa xızmet etedi hám `/api` menen `/media`'nı sonday jiberedi; build `frontend/.env.local`'dı da oqıydı (`VITE_API_BASE_URL=` bos qaldırıń).

## Mashqalalar (Problems)
- **Login yamasa qálegen forma "CSRF Failed" deydi**: ngrok mánzili `CSRF_TRUSTED_ORIGINS`'te joq, yamasa qosqannan keyin backend qayta iske túsirilmegen.
- **Súwretler kórinbeydi**: backend `DEBUG=True` penen isleýi kerek (sonda `/media/`'nı ózi beredi) hám `vite.config.ts` ózgergennen keyin `npm run dev` qayta iske túsiriliwi kerek.
- **"Too many requests" (429)**: tunnel artındaǵı hámme bir kelushi bolıp kórinedi; dev fayl limitlerdi ózi kóteredi. Login hám dizimnen ótiwdiń hár mánzil boyınsha óz qatań limiti bar; bir minut kútiń.
- **Bet isleydi, biraq jańalanıwlar qayta júklemesten kórinbeydi**: hot reload tunnel arqalı ótpewi múmkin; betti qayta júkleń.
- ngrok mánzilin biletuǵın hár kim saytıńızdan paydalana aladı hám, eger demo administrator jaratqan bolsańız, sol retinde kire aladı: pitkende ngrok'ti toqtatıń hám tunnel ashıq waqıtta demo akkauntlardıń belgili parolların hesh qashan paydalanbań (ornına óz administratorıńızdı jaratıń).
