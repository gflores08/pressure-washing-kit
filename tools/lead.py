#!/usr/bin/env python3
"""One command for a whole lead: drive, property line, lot size, photos, quote number, then the board data.

  python3 tools/lead.py leads/<folder>

Claude first writes leads/<folder>/facts.json with only what it learned about this lead:
  {"customer": "Dana Carter", "address": "12 Oak St, Anytown, CA 90000", "phone": "(555) 010-2233",
   "wants": "driveway and back patio", "home": {"sqft": 1850, "stories": 1, "built": 1992},
   "sources": "Zillow, Redfin", "notes": ["Ask: is the truck moved on wash day?"]}
Prices, start point and the parcel map come from me/ (tools/me.py), never from facts.json.
This adds drive {mi, min}, lot, walls (rough house-wash wall area), quote_no and created, writes history.md,
then runs tools/board.py, which prints what to send to the board.
"""
import glob, json, math, os, re, subprocess, sys, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import satellite as sat
from me import settings

folder = sys.argv[1] if len(sys.argv) > 1 else sys.exit(__doc__)
ff = os.path.join(folder, "facts.json")
f = json.load(open(ff))
for k in ("customer", "address"):
    if not f.get(k):
        sys.exit(f"facts.json needs \"{k}\". Ask the owner.")
S = settings()
warn = []

# The drive
if S["start"] and not f.get("drive"):
    try:
        (x1, y1, _), (x2, y2, _) = sat.geocode(S["start"]), sat.geocode(f["address"])
        r = json.loads(sat.get(f"https://router.project-osrm.org/route/v1/driving/{x1},{y1};{x2},{y2}?overview=false"))["routes"][0]
        f["drive"] = {"mi": round(r["distance"] / 1609.34, 1), "min": round(r["duration"] / 60)}
    except BaseException as e:
        warn.append(f"no drive time ({e}). Check the start point in me/business.md")
elif not S["start"]:
    warn.append("no start point in me/business.md, so no drive time")

# The property line: the first parcel map that has this address
lon, lat, matched = sat.geocode(f["address"])
use = None
for url in S["parcels"]:
    try:
        if sat.parcel_for(url, lon, lat, matched):
            use = url; break
    except Exception:
        pass
sat.fetch(f["address"], folder, use)
frame = json.load(open(os.path.join(folder, "photos", "frame.json")))
if frame.get("lot_sqft"):
    f["lot"] = frame["lot_sqft"]
else:
    warn.append("no property line found. Look at photos/satellite.png: is the right house in the middle?")
sat.dates(folder)

# A rough house-wash wall area: footprint perimeter x 9 ft per story
h = f.get("home") or {}
if h.get("sqft") and not f.get("walls"):
    st = h.get("stories") or 1
    f["walls"] = int(round(4 * math.sqrt(h["sqft"] / st) * 1.15 * 9 * st, -1))

# The next quote number: one more than the highest in any lead, open or finished
leads_dir = os.path.dirname(os.path.abspath(folder))
if not f.get("quote_no"):
    yr = datetime.date.today().year
    n = 0
    for p in glob.glob(os.path.join(leads_dir, "**", "facts.json"), recursive=True):
        m = re.search(rf"Q-{yr}-(\d+)", json.load(open(p)).get("quote_no") or "")
        n = max(n, int(m.group(1)) if m else 0)
    f["quote_no"] = f"Q-{yr}-{n + 1:03d}"
today = datetime.date.today().isoformat()
f.setdefault("created", today)
json.dump(f, open(ff, "w"), indent=1)
hist = os.path.join(folder, "history.md")
if not os.path.exists(hist):
    open(hist, "w").write(f"# History: {f['customer']}\n\n- {today} · lead in: {f.get('wants') or 'quote request'}\n")

d = f.get("drive") or {}
print(f"\nLEAD READY: {f['customer']} · {f['quote_no']}")
print(f"drive {d.get('mi', '?')} mi / {d.get('min', '?')} min · lot {f.get('lot', '?')} sq ft · walls ~{f.get('walls', '?')} · property line: {'yes' if use else 'NO'}")
print(f"his area: {S['area'] or '(not set)'} · doesn't do: {S['doesnt'] or '(not set)'}")
for w in warn:
    print("CHECK:", w)
subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "board.py")], check=True)
