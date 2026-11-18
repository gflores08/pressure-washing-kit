---
name: lead
description: Put a new lead on the owner's board before he drives out. Trigger when he says "lead", pastes a lead, or forwards a lead email.
---

# lead: the new lead on his board, in about four turns

**In:** a lead (pasted, an email, or a folder `sync.py` made from his phone). **Out:** the lead on his board with the house, drive and aerial photos. **He checks:** the board.

Every extra turn re-reads everything, so do each step in one turn and read nothing else (not `me/`, not other leads: the scripts read them).

1. **Look up the house:** one web search for the address (Zillow, Redfin or Realtor.com list square feet, stories and year built). Missing name or address → ask him first.
2. **Write** `leads/<last-name>-<house number>/lead.md` (the lead, word for word) and `facts.json`, only these keys:
   `{"customer": "Dana Carter", "address": "12 Oak St, Anytown, CA 90000", "phone": "(555) 010-2233", "wants": "driveway and patio", "home": {"sqft": 1850, "stories": 1, "built": 1992}, "sources": "Redfin", "notes": ["Ask where the hose bib is"]}`
   `notes` = what to check on site. A lead `sync.py` made already has its folder: just add `home`, `sources`, `notes`.
3. **Run** `python3 tools/lead.py leads/<folder>`. It prints `SEND TO THE BOARD` with one or more `writes = [...]`: make one ArtifactData `batch` call per line with exactly those writes and the url it names, then run `python3 tools/board.py --done`. Refused because a row already exists → ArtifactData `list` of `biz`, `leads` and `shots` with `out_dir` `leads/_have`, then `python3 tools/board.py --have leads/_have` and send what it prints. It says `NO BOARD YET` → the board skill § Publish first. A note that the rows hold "embedded images" is expected (the photos travel as data); ignore it. `property line: NO` → look at `photos/satellite.png` and say whether the right house is in the middle.
   **A lead from the board's inbox that can't be finished** (no city, the address isn't found, the lookup fails) → ArtifactData `update` that inbox row with `failed`: the reason in a few words ("address not found: needs a city"), so the lead check stops retrying it. Tell him what to fix.
4. **Tell him** in 2 lines: it's on the board, and the one thing to check on site. Outside his area or a service he doesn't do (`lead.py` prints both), or public records that disagree → say so.

