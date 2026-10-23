# Plan: ads with photos, ads by region (2026-10-23)

Owner request: when a hotel is advertised, show its photos; the ads must not be the same everywhere (the guest sees the ads of the place they chose, and the advertising panel shows, region by region, the hotels that run ads there); an ad can have up to 10 photos; write which picture sizes are accepted.

## Decisions (made without asking; change them if the owner wants it differently)
- Ads are still bought and set up by the super admin (the price is only an agreed amount, nothing is charged online). So the ad's pictures are put there by the super admin too.
- An ad has its **own pictures** (up to 10, `PromotionPhoto`). An ad without its own pictures shows the **hotel's own photos** (cover first, at most 10). The banner shows the pictures one after another and stays longer on a banner with many pictures (5 s minimum, 12 s maximum).
- "The ads of the chosen place": the home banner follows the country the guest opens under "Where to?"; a region opens the search for that place, and the search page already shows only the promoted hotels that match the search; both banners now say "Ads in {place}".
- "Region by region in the advertising panel": a panel with one card per region (ads running, ads waiting, the hotels that run them, empty regions too, so the admin sees where ads can still be sold); choosing a region limits the list below to it.
- Accepted pictures (same rules as every upload, checked on the server): JPG, PNG, WebP or GIF, up to 10 MB each, at most 40 megapixels. Advice written next to the ad upload: wide photos, at least 1920 x 720 px (the banner is a wide strip, 16:6, on computers and 16:9 on phones, so keep the main subject in the middle). The hotel and room photo uploads show the same limits with "at least 1600 x 900 px".

## Not done
- Ordering the ad pictures by hand (they show in upload order; delete and add again to change it).
- Owners cannot buy or edit ads themselves.
- A choice of region on the home page itself (only the country; a region opens the search page, which is region-specific).
