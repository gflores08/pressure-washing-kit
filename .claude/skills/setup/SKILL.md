---
name: setup
description: First run. Fill in the owner's business and prices from a five-minute talk, make his lead board, run a practice lead, start the lead check. Trigger on "set me up", "get started", or when he has no board yet.
---

# setup: from a pasted message to his lead board

**In:** his words. **Out:** his lead board link, his settings saved on it, one practice lead, the lead check. **He checks:** the prices and the board on his phone.

1. **Already set up?** Artifact `list`: a "Lead board" there, or he gave a board link → he's been here before. Don't make a second board: the board skill § Start with that link. Gmail or Calendar newly connected → make the lead check again from this chat (step 9; delete the old "Lead board check" first) so it can use them. Then tell him he's all set.
2. **Check this session:** `python3 tools/doctor.py`. A map line says `NOT REACHABLE` → tell him the one setting, then keep going (leads come without photos until it's on):
   "One setting so leads get satellite photos: under the message box, tap the cloud name → the gear → Network access → **Full** → Save. Then start a new session and paste the same message again."
3. **Ask for the five-minute talk**, one message, voice memo or typing: his name and company, phone and email for quotes, the street address where his day starts, the towns he covers, what he does and doesn't do, his prices and minimum, how fast he works, how he gets paid, his terms (what goes on every quote), where leads come from, how quotes go out, and one real text or email he sent a customer, pasted as is (his emails get written in that voice). His logo, if he has one. Wait for it.
4. **Fill `me/business.md`, `me/prices.md` and `me/voice.md`** from his words (voice: his greeting, sign-off, tone, and the message he pasted under "A real message you sent"). Keep the labels exactly as they are (the tools read them). Leave a blank where he said nothing. Prices he didn't give → ask; never use the samples as his. Set `Status: mine` only when every price is his. Packages he didn't describe → keep the lines as they are (a sensible start; say so). A logo he attached → save it as `me/logo.png`.
5. **Find his county's parcel map** (draws the property line): web search `<county> county parcels ArcGIS FeatureServer`; you need a layer URL ending in `/FeatureServer/<n>` or `/MapServer/<n>`. Prove it: `python3 tools/satellite.py parcel "<his start address>" <url>` must say FOUND. Put the URL in `me/business.md` → Parcel map. None works → leave it blank; leads come without a property line.
6. **Make his board** (the board skill § Publish). `python3 tools/board.py` saves his settings on it. Then `python3 tools/me.py`: anything MISSING → ask him.
7. **Practice lead** on his own start address, customer name "PRACTICE <his first name>" (the lead skill).
8. **Gmail and Calendar:** ListConnectors (or look at your tools). Gmail and/or Google Calendar there → say so in one line; the lead check uses them. Not there → one line: "Want leads from your email and jobs on your calendar? Connect Gmail and Google Calendar at claude.ai/customize/connectors, then start a new chat and paste the same message." Don't wait for it.
9. **The lead check:** his pasted message asked for it; create the scheduled task in the board skill § The lead check, with his board link and his time zone (from his start address). Blocked or he didn't ask → ask him once: "Want me to check your board for new leads 5 times a day?" A yes → create it. Still can't → tell him to say "sync" when he adds leads.
10. **Tell him** in 4 short lines: his board link (open it, Share → Add to Home Screen), what to check in his prices, that leads he adds with **New lead** on the board fill in at the next check (7, 10, 1, 4 and 7) or right away when he says "sync" here, and that for anything else ("lead", "quote for Dana") he comes back to this chat.
