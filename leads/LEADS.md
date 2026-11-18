# Leads

One folder per customer: `<last-name>-<house number>/` (e.g. `carter-3308/`). Paid or lost → `done/<year>/<folder>/` (moved by `tools/sync.py`).

| File | Written by | What |
|---|---|---|
| `lead.md` | Claude (lead skill) or `sync.py` | what came in, word for word |
| `facts.json` | Claude, then `lead.py` once | name, phone, address, what they want, the house, drive, lot, quote number |
| `photos/` | `lead.py` | aerial photos, property line (`frame.json`), his traced outline (`surfaces.json`) |
| `history.md` | `lead.py`, `sync.py` | dated lines: lead in, traced, quote sent, won, paid |
| `state.json` | `sync.py` only | his work on the board: status, traced pieces, options, the priced quote |
| `notes.md` | `sync.py` | his notes from the board |
| `quote.html` · `quote.pdf` · `email.txt` | `quote.py` | the customer's quote, and the email to send with it |

Status (set on the board, or "mark Dana won"): new · traced · sent · won · done · paid · lost.

Board bookkeeping (not the record): `board.json` (the board's link and what was sent), `_push/` and `_sync/` (scratch, safe to delete).
