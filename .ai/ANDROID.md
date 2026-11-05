# Android app (TICKBRON)

The app is a Trusted Web Activity: a small Android shell that opens `https://tickbron.com` full screen in Chrome. It has no screens or logic of its own; every site change reaches the app at once. Name `TICKBRON`, package `com.tickbron.app`.

- Source, build script, icons, signing key (never in git): `D:\TICKBRON-ANDROID` on Kolya's computer, with its own `README.md`. It is a separate local git repository, not part of this one.
- Build: `powershell -ExecutionPolicy Bypass -File scripts\build.ps1` in that folder gives `out\TICKBRON-<version>.apk` (phones) and `.aab` (Google Play). Needs no installed tools: JDK 17, Android SDK 36 and Gradle 8.11 are inside its `tools\` folder.
- The site side (this repo): `frontend/public/manifest.webmanifest`, `sw.js`, `offline.html`, `.well-known/assetlinks.json`, brand icons. See the HANDOFF section "Android app preparation".

## Steps after the server is up
1. `https://tickbron.com/manifest.webmanifest`, `/sw.js`, `/.well-known/assetlinks.json` answer 200 with their own content (JSON, not the home page).
2. Install the APK on a phone. No address bar at the top means the site confirmed the app. An address bar means `assetlinks.json` does not list the fingerprint of the key that signed the installed app.
3. Google Play Console (the developer account exists): create the app TICKBRON, package `com.tickbron.app`, upload the `.aab` to Internal testing first. Copy "App signing key" SHA-256 (Setup -> App signing) into `assetlinks.json` (keep the existing line), deploy the site.
4. Listing needs: icon 512 and feature graphic (made, in `D:\TICKBRON-ANDROID\store`), phone screenshots from the live site, short and long description (uz/ru/en), a public privacy-policy page address, the Data safety form, the content rating.

## Owner decisions
- Whether `www.tickbron.com` must also open the app: today `www` redirects to the bare name, so the app covers `tickbron.com` only.
- iOS is not part of this: it needs a decision about token sign-in (see ROADMAP).
