#!/usr/bin/env python3
"""Bring what he did on the lead board back into the folders (the record).

  python3 tools/sync.py <dir or file>
  python3 tools/sync.py --mark <lead-folder-name> <new|traced|sent|won|done|paid|lost>

<dir>: where Claude saved the board's rows (ArtifactData list of "work" and of "inbox", out_dir <dir>).
<file>: text he pasted from "Save with Claude" (the offline board), one or more "QUOTE MAP for <id> ... DATA {...}".

work/<id>  his taps on one lead → leads/<id>/state.json (status, traced pieces, quote choices, the quote, notes),
           photos/surfaces.json, notes.md, a dated line in history.md per status change. Paid or lost → leads/done/<year>/.
inbox/<id> a lead he typed on his phone → a new leads/<last-name>-<number>/ with lead.md and facts.json, for the
           lead skill to finish (look up the house, run lead.py).
--mark     sets a status from the office; prints the one ArtifactData update that tells the board.
"""
import datetime, glob, json, os, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEADS = os.path.join(ROOT, "leads")
LABEL = {"new": "New", "traced": "Traced", "sent": "Quote sent", "won": "Won", "done": "Job done", "paid": "Paid", "lost": "Lost"}
KEEP = ("pieces", "q", "status", "memo", "sentAt", "updated", "total", "option", "quote")

def unwrap(d):
    """A saved row: the fields themselves, or {id, data: {...}}."""
    return d["data"] if isinstance(d, dict) and isinstance(d.get("data"), dict) else d

def rows(path):
    if os.path.isdir(path):
        out = {"work": {}, "inbox": {}}
        for p in glob.glob(os.path.join(path, "**", "*.json"), recursive=True):
            col = os.path.basename(os.path.dirname(p))
            if col in out:
                out[col][os.path.basename(p)[:-5]] = unwrap(json.load(open(p)))
        return out
    raw = open(path).read()
    return {"work": {m.group(1): json.loads(m.group(2)) for m in re.finditer(r"QUOTE MAP for (\S+).*?\nDATA (\{[^\n]*\})", raw, re.S)}, "inbox": {}}

def find(lid):
    for p in [os.path.join(LEADS, lid)] + sorted(glob.glob(os.path.join(LEADS, "done", "*", lid)), reverse=True):
        if os.path.exists(os.path.join(p, "facts.json")):
            return p
    return None

def money(s):
    return f" ({'$' + format(s['total'], ',.2f')}, {s.get('option')})" if s.get("total") else ""

def file_work(lid, s, today):
    folder = find(lid)
    if not folder:
        print(f"skip {lid}: no folder"); return False
    sp = os.path.join(folder, "state.json")
    old = json.load(open(sp)) if os.path.exists(sp) else {}
    if (s.get("updated") or 0) <= (old.get("updated") or 0):
        return False
    customer = json.load(open(os.path.join(folder, "facts.json"))).get("customer", "")
    lines = []
    st = s.get("status") or "new"
    if st != (old.get("status") or "new"):
        lines.append(f"- {today} · {LABEL.get(st, st)}{money(s) if st in ('sent', 'won', 'paid') else ''}")
    if (s.get("memo") or "") != (old.get("memo") or ""):
        open(os.path.join(folder, "notes.md"), "w").write(f"# Notes: {customer}\n\n{s['memo']}\n")
        lines.append(f"- {today} · notes updated")
    pieces = s.get("pieces") or []
    if pieces:
        json.dump({p["name"]: p["pts"] for p in pieces}, open(os.path.join(folder, "photos", "surfaces.json"), "w"))
        if [p["name"] for p in pieces] != [p["name"] for p in old.get("pieces") or []]:
            lines.append(f"- {today} · traced: {', '.join(p['name'] for p in pieces)}")
    new = {k: s[k] for k in KEEP if k in s}
    new["status"] = st
    json.dump(new, open(sp, "w"), indent=1)
    if lines:
        with open(os.path.join(folder, "history.md"), "a") as h:
            h.write("\n".join(lines) + "\n")
    print(f"{lid}: {LABEL.get(st, st)}" + (f" · ${s['total']:,.2f}" if s.get("total") else ""))
    if st in ("paid", "lost") and os.path.dirname(folder) == LEADS:
        dest = os.path.join(LEADS, "done", today[:4], lid)
        os.makedirs(os.path.dirname(dest), exist_ok=True); shutil.move(folder, dest)
        print(f"  filed → leads/done/{today[:4]}/{lid}")
        bj = os.path.join(LEADS, "board.json")
        board = json.load(open(bj)) if os.path.exists(bj) else {}
        shots = [p for p in board.get("pushed", []) if p.startswith(f"shots/{lid}~")]
        if shots:
            print("  FREE ITS PHOTOS ON THE BOARD: ArtifactData batch, writes = " + json.dumps(
                [{"op": "delete", "collection": "shots", "doc_id": p.split("/", 1)[1], "if_version": 1} for p in shots]))
            board["pushed"] = [p for p in board["pushed"] if p not in shots]
            json.dump(board, open(bj, "w"), indent=1)
    return True

def file_inbox(iid, s, today):
    taken = {json.load(open(p)).get("inbox") for p in glob.glob(os.path.join(LEADS, "**", "facts.json"), recursive=True)}
    if iid in taken or not s.get("customer"):
        return False
    last = re.sub(r"[^a-z0-9]+", "-", (s["customer"].split() or ["lead"])[-1].lower()).strip("-") or "lead"
    num = (re.findall(r"\d+", s.get("address") or "") or [iid[-4:]])[0]
    folder = base = os.path.join(LEADS, f"{last}-{num}")
    n = 2
    while os.path.exists(folder):
        folder = f"{base}-{n}"; n += 1
    os.makedirs(folder)
    facts = {k: s.get(k) for k in ("customer", "phone", "address", "wants") if s.get(k)}
    facts["inbox"] = iid
    json.dump(facts, open(os.path.join(folder, "facts.json"), "w"), indent=1)
    open(os.path.join(folder, "lead.md"), "w").write(f"# Lead (typed on the board, {today})\n\n" + "\n".join(f"- **{k}:** {v}" for k, v in facts.items() if k != "inbox") + "\n")
    print(f"NEW FROM THE PHONE: leads/{os.path.basename(folder)}/ ({s['customer']}). Finish it with the lead skill: look up the house, then lead.py.")
    if not s.get("address"):
        print("  CHECK: no address yet. Ask him.")
    return True

def main():
    a = sys.argv[1:]
    today = datetime.date.today().isoformat()
    if a[:1] == ["--mark"] and len(a) == 3:
        lid, st = a[1], a[2]
        if st not in LABEL: sys.exit("status must be one of: " + " ".join(LABEL))
        folder = find(lid) or sys.exit(f"no lead folder for {lid}")
        sp = os.path.join(folder, "state.json")
        old = json.load(open(sp)) if os.path.exists(sp) else {}
        now = int(datetime.datetime.now().timestamp() * 1000)
        change = {"status": st, "updated": now, **({"sentAt": now} if st == "sent" else {})}
        file_work(lid, {**old, **change}, today)
        print("TELL THE BOARD: ArtifactData update, url from leads/board.json, collection work, doc_id " + lid +
              ", if_version = the version the work list showed for it (none: use set, no if_version), data " + json.dumps(change))
        return
    if not a:
        sys.exit(__doc__)
    if not os.path.exists(a[0]):
        print("Nothing new on the board."); return
    r = rows(a[0])
    changed = sum(file_inbox(i, s, today) for i, s in r["inbox"].items())
    changed += sum(file_work(i, s, today) for i, s in r["work"].items())
    print(f"{changed} change(s) filed." if changed else "Nothing new on the board.")

if __name__ == "__main__":
    main()
