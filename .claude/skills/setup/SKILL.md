---
name: setup
description: First run. Fill in the owner's business and prices from a voice dump, make his lead board, run a practice lead. Trigger on "set me up", "get started", or when me/business.md has no business name.
---

# setup: from an empty folder to his lead board

**In:** his words. **Out:** `me/` filled in, his lead board link, one practice lead on it. **He checks:** the prices and the board on his phone.

1. **Check the computer:** `python3 tools/doctor.py` (Windows: `python`). Fix what it says; it installs the photo add-on itself. You can't run commands here → tell him this folder needs Claude Code, and stop.
2. **Ask for the five-minute talk**, one message, voice memo or typing: his name and company, phone and email for quotes, the street address where his day starts, the towns he covers, what he does and doesn't do, his prices and minimum, how fast he works, how he gets paid, his terms (what goes on every quote), where leads come from, how quotes go out, and one real text or email he sent a customer, pasted as is (his emails get written in that voice). Wait for it.
3. **Fill `me/business.md`, `me/prices.md` and `me/voice.md`** from his words (voice: his greeting, sign-off, tone, and the message he pasted under "A real message you sent"). Keep the labels exactly as they are (the tools read them). Leave a blank where he said nothing. Prices he didn't give → ask; never use the samples as his. Set `Status: mine` only when every price is his. Packages he didn't describe → keep the lines as they are (they're a sensible start; say so). "Priced on site" → his list, or empty.
4. **Find his county's parcel map** (draws the property line): web search `<county> county parcels ArcGIS FeatureServer` or the county GIS open-data page; you need a layer URL ending in `/FeatureServer/<n>` or `/MapServer/<n>`. Prove it: `python3 tools/satellite.py parcel "<his start address>" <url>` must say FOUND. Put the URL in `me/business.md` → Parcel map. Can't find one → leave it blank and say leads come without a property line.
5. **His logo:** if he sends one, save it as `me/logo.png`.
6. **Make his board** (the board skill § Publish; the first publish reads the page file once, that's expected). Then `python3 tools/me.py`: anything MISSING → ask him.
7. **Practice lead** on his own address, customer name "PRACTICE <his first name>" (the lead skill). It shows him the board on a house he knows.
8. **Tell him** in 5 short lines: the board link (open it on his phone, add it to the Home Screen), what to check in his prices, that "lead" adds a lead, "sync" files his taps, and to type `watch <board link>` in a Claude window he leaves open on his computer so leads he adds on the phone fill in by themselves.
