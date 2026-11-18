---
name: quote
description: Make the customer's quote as a PDF from what the owner built on his board. Trigger on "quote", "quote for <name>", "make the PDF".
---

# quote: the PDF, from the board

**In:** a lead he traced and priced on the board. **Out:** `quote.pdf` (the same page he previewed on the board) and `email.txt` (the email in his voice) in its folder. **He checks:** the total and the email, then he sends it.

On site he does it all on the board: trace, type his tape numbers (Quote → Change sq ft and extras), stains, extra items, pick the option, See the customer's quote (the PDF and the email, written in his voice on the board), Finalize quote (sends both from his phone). The board's price is the price; never re-price it here.

1. **Sync first** (the board skill § Sync) so the folder has his latest.
2. **Run** `python3 tools/quote.py leads/<folder>`. "No quote on the board yet" → tell him to trace it and pick an option on the board. It says the email is `plain` → rewrite only its sentences (greeting, the intro, the closing, the sign-off) by `tools/email-rules.md` in his voice from `me/voice.md` (the humanizer skill too, if this computer has it). Never touch the options, prices or terms lines.
3. **Tell him** the total and the option in 2 lines, where the PDF is, and paste `email.txt` so he can send it by email, text or wherever he keeps quotes (attach the PDF). He sends it, never you. Sample prices → it's stamped SAMPLE: say it's practice only.

He gives you new measurements here instead → tell him where to type them on the board (Quote → Change sq ft and extras), so the board and the folder agree.
