#!/usr/bin/env python3
"""The customer's quote as a PDF, and the email that goes with it, from what he built on the board.

  python3 tools/quote.py leads/<folder>

The board fills the quote layout (tools/quote-template.html) and drafts the email in his voice (me/voice.md);
sync.py files both in leads/<folder>/state.json "quote". This prints that same page to quote.pdf and writes
email.txt, so the PDF he previewed on his phone is the PDF that goes out.
Writes quote.html, email.txt and, when Chrome or Edge is installed, quote.pdf.
No PDF → open quote.html in a browser → Print → Save as PDF.
"""
import json, os, shutil, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from me import settings

folder = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else sys.exit(__doc__)
st_p = os.path.join(folder, "state.json")
Q = (json.load(open(st_p)) if os.path.exists(st_p) else {}).get("quote")
if not Q:
    sys.exit("No quote on the board yet for this lead. He traces it and picks an option on the board, then sync.")
if not Q.get("html"):
    sys.exit("This quote was saved before the board made PDFs. He opens the lead's Quote on the board and changes anything (or picks an option), then sync.")

out = os.path.join(folder, "quote.html")
open(out, "w", encoding="utf-8").write(Q["html"])
print("quote:", out)

E = Q.get("email") or {}
if E.get("body"):
    mail = os.path.join(folder, "email.txt")
    open(mail, "w", encoding="utf-8").write(f"Subject: {E.get('subject', '')}\n\n{E['body'].strip()}\n")
    print("email:", mail, "(in his voice)" if E.get("voiced") or E.get("edited") else "(plain: rewrite it with tools/email-rules.md + me/voice.md)")

chrome = next((p for p in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                           "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
                           r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                           r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
               if os.path.exists(p)), None) or shutil.which("google-chrome") or shutil.which("chromium")
if chrome:
    pdf = os.path.join(folder, "quote.pdf")
    subprocess.run([chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={os.path.abspath(pdf)}",
                    "file://" + os.path.abspath(out)], capture_output=True, timeout=60)
    print("pdf:", pdf if os.path.exists(pdf) else "failed. Open quote.html → Print → Save as PDF")
else:
    print("pdf: no Chrome or Edge found. Open quote.html → Print → Save as PDF")
if Q.get("sample") or settings()["sample"]:
    print("CHECK: sample prices. This quote is stamped SAMPLE and must not go to a real customer.")
