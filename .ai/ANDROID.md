# Android ilovası (TICKBRON)

Ilova - Trusted Web Activity: `https://tickbron.com` saytın Chrome'da pútkil ekranda ashatuǵın kishkene Android qabıqshası. Onıń óz ekranları yamasa logikası joq; sayttaǵı hár ózgeris ilovaǵa birden jetip baradı. Atı `TICKBRON`, package `com.tickbron.app`.

- Source, build script, ikonkalar, imzalaw kilti (git'te hesh qashan): Kolya kompyuterinde `D:\TICKBRON-ANDROID`, óz `README.md` fayli menen. Bul bólek local git repository, usı repository'diń bólegi emes.
- Build: sol papkada `powershell -ExecutionPolicy Bypass -File scripts\build.ps1` `out\TICKBRON-<versiya>.apk` (telefonlar ushın) hám `.aab` (Google Play ushın) beredi. Hesh qanday ornatılǵan qural kerek emes: JDK 17, Android SDK 36 hám Gradle 8.11 onıń `tools\` papkasında.
- Saytıń tárepi (usı repo): `frontend/public/manifest.webmanifest`, `sw.js`, `offline.html`, `.well-known/assetlinks.json`, brend ikonkalar. HANDOFF'tıń "Android app preparation" bólimine qarań.
- Qáwipsizlik: imzalaw kilti hám onıń paroli `D:\TICKBRON-ANDROID\secrets\` ishinde. Onı git'ke qoymań hám basqa jerge (fleshka, shaxsiy bulut) nusqasın saqlań: joǵalsa ornatılǵan APK'nı jańalap bolmaydı.

## Server tayar bolǵannan keyingi qádemler
1. `https://tickbron.com/manifest.webmanifest`, `/sw.js`, `/.well-known/assetlinks.json` óz mazmunı menen 200 juwap beredi (JSON, bas bet emes).
2. APK'nı telefonǵa ornatıń. Joqarıda mánzil qatarı joq bolsa, sayt ilovanı tastıyıqlaǵan. Mánzil qatarı bar bolsa, `assetlinks.json` ornatılǵan ilovanı imzalaǵan kilttiń fingerprint'in dizimde kórsetpeydi.
3. Google Play Console (developer akkaunt bar): TICKBRON ilovasın jaratıń, package `com.tickbron.app`, aldın `.aab`'nı Internal testing'ke júkleń. "App signing key" SHA-256'nı (Setup -> App signing) `assetlinks.json`'ge qosıń (bar qatardı saqlań), saytıń jańa nusqasın joylastırıń.
4. Ilova sahifası ushın kerek: 512 ikonka hám feature graphic (tayar, `D:\TICKBRON-ANDROID\store`), jonli saytan telefon skrinshotları, qısqa hám tolıq táriyp (uz/ru/en), ashıq maxfiylik siyasatı beti mánzili, Data safety forması, content rating.
5. Google hám Apple májbúriy talap etetuǵın nárse: ilovada dizimnen ótiw bar bolsa, paydalanıwshı akkauntın ilovanıń ishinen óshire alıwı kerek (ele islenbegen, `LAUNCH_TODO.md`), hám tekseriwshi ushın kodsız kiriw jolı (demo akkaunt) kerek, sebebi kirisiw mail kodı menen.

## Iyesiniń qararları
- `www.tickbron.com` da ilovanı ashıwı kerekpe: házir `www` taza atqa jiberiledi, sonıń ushın ilova tek `tickbron.com`'dı qamtıydı.
- iOS bul jerde joq: ol token menen kirisiw haqqında qarardı talap etedi (ROADMAP qarań). Narxı hám tártibi buyırtpashı menen kelisim hújjetinde.
