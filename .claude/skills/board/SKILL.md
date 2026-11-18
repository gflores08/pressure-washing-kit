---
name: board
description: Keep the owner's lead board and the lead folders in step. Trigger on "sync", "update the board", "how are my leads", "mark <name> won/sent/done/paid/lost", the lead check, a fresh session for an owner who already has a board, or when the lead skill needs the board made.
---

# board: his phone page, his memory

The board is one page in his Claude account: `tools/board-template.html`, published once. It holds his settings (the `biz` rows carry his `me/` files) and every lead. Leads reach it as data rows (`tools/board.py`); his taps come back as rows (`tools/sync.py`). This session keeps its link in `leads/board.json`.

## Start (a fresh session, he already has a board)
1. Write `{"url": "<his board link>"}` to `leads/board.json`.
2. In one turn: ArtifactData `list` of collection `biz`, and of collection `leads`, both with that url and `out_dir` `leads/_have`.
3. `python3 tools/board.py --restore leads/_have`. It rebuilds `me/` and a small folder per lead. `NO SETTINGS ON THE BOARD` → the setup skill.

## Sync ("sync", "how are my leads", the lead check)
1. **Pull his taps**, in one turn: ArtifactData `list` of collection `work`, and of collection `inbox`, url from `leads/board.json`, `out_dir` `leads/_sync`.
2. **File them:** `python3 tools/sync.py leads/_sync`. It may print:
   - `NEW FROM THE PHONE: leads/<folder>/` → a lead he typed on the board: finish it with the lead skill, steps 1 to 3.
   - `FREE ITS PHOTOS ON THE BOARD` → make that ArtifactData `batch` call.
3. **Tell him** in 2 lines what changed ("Dana: won, $437.50. Pat added; it's on the board now."). The lead check with nothing new says nothing.

## The lead check (setup makes it once)
A scheduled task (create_trigger) at 7am, 10am, 1pm, 4pm and 7pm his time (`0 7,10,13,16,19 * * *`, shifted to UTC if the tool wants UTC; Pro plans allow about 5 scheduled runs a day), this session's cloud environment, named "Lead board check", then set its model to Haiku (an update right after; create has no model setting). The prompt (put his board link in):

> Lead board check for <board link>. If Gmail is connected: search his email from the last day for new customer inquiries (pressure washing, quote, estimate, driveway; Facebook, Nextdoor, Thumbtack, Angi or Google notifications, or a direct email), and for each new one write an `inbox` row on the board (customer, phone, address, wants, at, `source`: the email's id) unless an inbox row already has that `source`. Then ArtifactData `list` collection `inbox` of that board, then collection `leads`. If every inbox row's id already appears as the `inbox` field of a lead, stop and say nothing. Otherwise: `git clone https://github.com/gflores08/pressure-washing-kit kit && cd kit`, read `CLAUDE.md`, do the board skill § Start with that link, then § Sync, and finish every NEW FROM THE PHONE with the lead skill. Keep it short.

## Gmail and Calendar (when connected; the chat had them when it started)
- **Lead emails:** the lead check finds them (above). He forwards or pastes one → the lead skill.
- **A quote to send by email:** after the quote skill, make a Gmail **draft** to the customer with `email.txt` as the body (attach the PDF if the tool allows). He reviews and sends. Never send it yourself.
- **Booked** ("Dana's booked Thursday 9am"): mark the lead `won` (below), then a Google Calendar event: title "<customer>: <what> ($<total>)", the address as the location, his phone notes and the customer's phone in the description, length from the board's time on site (or 2 hours).
- Not connected and he asks → the one line from the setup skill, step 8.

## Mark a status ("mark Dana won")
Sync first (steps 1 and 2), then `python3 tools/sync.py --mark <folder> <new|traced|sent|won|done|paid|lost>`. It files it and prints the one ArtifactData call that tells the board; use the version the `work` list showed for that lead.

## Publish (first time, or after `tools/board-template.html` changed)
- **No board yet:** Artifact publish `tools/board-template.html`, `capabilities` `{"db": {}, "sample": {}, "downloads": true}` (db = his leads and settings; sample = Claude writes his emails on the page; downloads = Save the PDF), `icon` "list". Save `{"url": "<link>"}` as `leads/board.json`. Then `python3 tools/board.py` and send what it prints (the lead skill, step 3).
- **Has a board and the page changed:** Artifact `read` that url, then publish `tools/board-template.html` with `url` set. Never publish without the url: that makes a second, empty board.

More than one crew, or hundreds of open leads → that's a job for a CRM like Jobber. Say so.
