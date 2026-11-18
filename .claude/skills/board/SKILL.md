---
name: board
description: Keep the owner's lead board and the lead folders in step. Trigger on "sync", "update the board", "how are my leads", "mark <name> won/sent/done/paid/lost", or when the lead skill needs the board made.
---

# board: his phone page and the folders, in step

The board is one page in his Claude account: `tools/board-template.html`, published once. Leads reach it as data rows (`tools/board.py`), and his taps come back as rows (`tools/sync.py`). Its link lives in `leads/board.json`.

## Sync ("sync", "how are my leads", start of a work session)
1. **Pull his taps**, in one turn: ArtifactData `list` of collection `work`, and of collection `inbox`, both with `url` from `leads/board.json` and `out_dir` `leads/_sync`.
2. **File them:** `python3 tools/sync.py leads/_sync`. It updates each lead's folder and moves paid or lost leads to `leads/done/`. It may print:
   - `NEW FROM THE PHONE: leads/<folder>/` → a lead he typed on his phone: finish it with the lead skill, steps 1 to 3.
   - `FREE ITS PHOTOS ON THE BOARD` → make that ArtifactData `batch` call.
3. **Tell him** in 2 lines what changed ("Dana: won, $437.50. Pat added; it's on the board now.").

## Watch (he leaves Claude open on his computer so phone leads fill in by themselves)
- **He says "watch" with his board link in the message** → ArtifactComments `watch` on that link (his link in his own message is what lets the board wake you). Say: "Watching. Leave this window open; leads you add on your phone fill in by themselves."
- **A board comment arrives saying "New lead from the board: …"** → Sync (steps 1 and 2) and finish every `NEW FROM THE PHONE` with the lead skill. Nothing new in the inbox → make the lead from the comment's words. Then ArtifactComments `resolve` that thread. Don't reply in it (the board already answered him).
- **Any other comment** → it's him asking about the board: answer or make the change, then resolve.

## Mark a status ("mark Dana won")
Sync first (step 1 and 2), then `python3 tools/sync.py --mark <folder> <new|traced|sent|won|done|paid|lost>`. It files it and prints the one ArtifactData call that tells the board; use the version the `work` list showed for that lead.

## Publish (first time, or after `tools/board-template.html` changed)
- **No link in `leads/board.json` yet:** Artifact publish `tools/board-template.html`, `capabilities` `{"db": {}, "sample": {}, "downloads": true, "comments": {}}` (db = his leads; sample = Claude writes his emails on the page; downloads = Save the PDF; comments = New lead wakes a watching Claude), `icon` "list". Save `{"url": "<link>"}` as `leads/board.json`. Then `python3 tools/board.py` and send what it prints (the lead skill, step 3).
- **Has a link and the page changed:** Artifact `read` that url, then publish `tools/board-template.html` with `url` set. Never publish without the url: that makes a second, empty board.
- **No Artifact tool:** `python3 tools/board.py --offline` and open `leads/board.html` in his browser. His taps stay in that browser; "Save with Claude" on a lead copies them, then `python3 tools/sync.py <file you saved the paste in>`.

More than one crew, or hundreds of open leads → that's a job for a CRM like Jobber. Say so.
