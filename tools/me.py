#!/usr/bin/env python3
"""Reads the owner's files, me/business.md, me/prices.md and me/voice.md, into one settings dict.
The only home of his prices, speeds, packages, terms and business details: every tool calls settings().

  python3 tools/me.py        print what the tools will use, and anything missing
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRICE_KEYS = {"concrete": "flatwork", "exposed": "aggregate", "aggregate": "aggregate", "pavers": "pavers", "house": "house_wash"}
SPEED_KEYS = {"concrete": "flatwork", "house": "house_wash", "setup": "setup_min"}

def _sections(path):
    """{"section title (lowercase)": [(label, value), ...]} from "- **Label:** value" bullets."""
    out, cur = {}, ""
    if not os.path.exists(path):
        return out
    for line in open(path, encoding="utf-8"):
        line = line.rstrip()
        if line.startswith("## "):
            cur = line[3:].strip().lower(); out.setdefault(cur, [])
        elif line.lstrip().startswith("- "):
            m = re.match(r"\s*-\s*\*\*(.+?)\*\*\s*(.*)", line)
            label, value = (m.group(1), m.group(2)) if m else ("", line.strip()[2:])
            if value.startswith("(") and "):" in value:  # "- **Concrete** (driveways, walks): $0.20"
                value = value.split("):", 1)[1]
            out.setdefault(cur, []).append((label.strip().rstrip(":"), value.strip().lstrip(":").strip()))
    return out

def _num(s):
    m = re.search(r"\$?\s*(\d[\d,]*(?:\.\d+)?)", s or "")
    return float(m.group(1).replace(",", "")) if m else None

def settings():
    b = _sections(os.path.join(ROOT, "me", "business.md"))
    p = _sections(os.path.join(ROOT, "me", "prices.md"))
    flat = {k.lower(): v for sec in b.values() for k, v in sec if k}
    prices, minimum, speed, packages = {}, None, {}, {}
    for label, value in p.get("prices", []):
        w = label.lower().split()[0] if label else ""
        if w == "minimum":
            minimum = _num(value)
        elif w in PRICE_KEYS and _num(value) is not None:
            prices[PRICE_KEYS[w]] = _num(value)
    for label, value in p.get("speed", []):
        w = label.lower().split()[0] if label else ""
        if w in SPEED_KEYS and _num(value) is not None:
            speed[SPEED_KEYS[w]] = _num(value)
    for label, value in p.get("packages", []):
        packages[label.lower()] = value
    good = [n.strip() for n in packages.get("good", "").split(",") if n.strip()]
    status = next((v for k, v in sum(p.values(), []) if k.lower() == "status"), "sample").lower()
    terms = [v or k for k, v in b.get("terms", []) if (v or k)]
    parcels = [u for u in re.findall(r"https?://\S+", flat.get("parcel map", ""))]
    v = _sections(os.path.join(ROOT, "me", "voice.md"))
    vf = {k.lower(): val for k, val in v.get("your voice", []) if k}
    ex_path, example = os.path.join(ROOT, "me", "voice.md"), ""
    if os.path.exists(ex_path):
        txt = open(ex_path, encoding="utf-8").read()
        if "## A real message you sent" in txt:
            example = txt.split("## A real message you sent", 1)[1].split("\n", 2)[-1].strip()
    voice = {"greeting": vf.get("greeting", ""), "signoff": vf.get("sign-off", ""), "tone": vf.get("tone", ""),
             "use": vf.get("words you use", ""), "avoid": vf.get("words you never use", ""), "example": example[:1500]}
    return {
        "business": {"name": flat.get("name", ""), "owner": flat.get("owner", ""), "phone": flat.get("phone", ""), "email": flat.get("email", "")},
        "start": flat.get("start point", ""), "parcels": parcels, "area": flat.get("service area", ""),
        "does": flat.get("does", ""), "doesnt": flat.get("doesn't do", ""),
        "prices": prices, "minimum": minimum or 0, "speed": speed, "good": good, "terms": terms,
        "sample": status != "mine", "voice": voice,
    }

def missing(s):
    out = []
    if not s["business"]["name"]: out.append("business name (me/business.md)")
    if not s["business"]["phone"]: out.append("phone (me/business.md)")
    if not s["start"]: out.append("start point, for drive times (me/business.md)")
    if not s["parcels"]: out.append("parcel map link, for property lines (me/business.md)")
    if not s["prices"].get("flatwork"): out.append("concrete price (me/prices.md)")
    if not s["minimum"]: out.append("minimum job (me/prices.md)")
    return out

if __name__ == "__main__":
    s = settings()
    print(json.dumps(s, indent=1))
    for m in missing(s):
        print("MISSING:", m)
    if s["sample"]:
        print("NOTE: prices are still the samples (me/prices.md Status: sample). Change it to: mine")
