#!/usr/bin/env python3
"""The lead board's data. The board page (tools/board-template.html) is published once; leads reach it as small
database rows, so a new lead never republishes the page.

  python3 tools/board.py            write what the board doesn't have yet to leads/_push/ and print the one
                                    ArtifactData batch call that sends it (the url is in leads/board.json)
  python3 tools/board.py --done     after that call worked: remember it was sent, clear leads/_push/
  python3 tools/board.py --have leads/_have
                                    a send was refused because a row already exists: Claude lists biz, leads and
                                    shots (out_dir leads/_have); this remembers what the board has, then prints the rest
  python3 tools/board.py --restore leads/_have
                                    a fresh session (cloud sessions start empty): Claude lists biz and leads (out_dir
                                    leads/_have); this rebuilds me/ and a small facts.json per lead from them, so
                                    quote numbers, sync and "already sent" all work again
  python3 tools/board.py --offline  leads/board.html: the whole board in one file, for a computer without
                                    Claude artifacts (taps stay in that browser; "Save with Claude" copies them)

Rows (never edited, only added, so no versions are needed):
  biz/<hash>         name, phone, prices, minimum, speed, Good package, terms, sample flag, logo, and the me/ files
                     themselves (the board is his memory: a cloud session rebuilds me/ from the newest biz row)
  leads/<id>~<hash>  one lead's facts, map scale, property line, thumbnail, and its photo rows
  shots/<id>~<hash>~<n>  one aerial photo (a few hundred KB)
The board shows the newest row per lead. His taps live in work/<id> (written by the page, read by sync.py).
"""
import base64, glob, hashlib, io, json, os, shutil, sys, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from me import settings, missing

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEADS = os.path.join(ROOT, "leads")
PUSH = os.path.join(LEADS, "_push")
BJ = os.path.join(LEADS, "board.json")
WORK_KEEP = ("pieces", "q", "status", "memo", "sentAt", "updated", "total", "option", "quote")  # as sync.py KEEP
ME_FILES = ("business.md", "prices.md", "voice.md")
FACT_KEYS = ("customer", "address", "phone", "wants", "home", "drive", "lot", "walls", "quote_no", "created", "notes", "inbox")

def jpeg(path, size, q, limit=None):
    try:
        from PIL import Image
    except ImportError:
        sys.exit("Pillow is missing (it shrinks the photos for the board). Run: python3 tools/doctor.py")
    im = Image.open(path).convert("RGB")
    while True:
        t = im.copy(); t.thumbnail((size, size))
        buf = io.BytesIO(); t.save(buf, "JPEG", quality=q, optimize=True)
        uri = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
        if not limit or len(uri) < limit or size < 400:
            return uri
        size = int(size * .85)

def h(obj):
    return hashlib.sha1(json.dumps(obj, sort_keys=True).encode()).hexdigest()[:8]

def lead_docs(folder, with_shots=True):
    f = json.load(open(os.path.join(folder, "facts.json")))
    frame_p = os.path.join(folder, "photos", "frame.json")
    if not os.path.exists(frame_p):
        return []
    frame = json.load(open(frame_p))
    lid = os.path.basename(folder)
    shots = sorted(glob.glob(os.path.join(folder, "photos", "dates", "*.png")))[::-1][:2] or [os.path.join(folder, "photos", "satellite.png")]
    lead = {k: f[k] for k in FACT_KEYS if f.get(k) is not None}
    lead.update(id=lid, m_per_px=frame["m_per_px"], px=frame["px"], parcel=frame.get("parcel_px"), thumb=jpeg(shots[0], 160, 60))
    docs, refs = [], []
    if with_shots:
        for n, p in enumerate(shots):
            name = os.path.basename(p)
            shot = {"src": jpeg(p, 900, 62, limit=230_000), "date": name[:10] if name[:4].isdigit() else None}
            sid = f"{lid}~{h(shot)}~{n}"
            docs.append(("shots", sid, shot)); refs.append({"doc": sid, "date": shot["date"]})
    lead["shots"] = refs
    docs.insert(0, ("leads", f"{lid}~{h(lead)}", dict(lead, at=datetime.datetime.now().isoformat(timespec="seconds"))))
    return docs

def biz_doc():
    s = settings()
    logo = os.path.join(ROOT, "me", "logo.png")
    doc = {"name": s["business"]["name"], "owner": s["business"]["owner"], "phone": s["business"]["phone"], "email": s["business"]["email"], "prices": s["prices"], "minimum": s["minimum"],
           "speed": s["speed"], "good": s["good"], "terms": s["terms"], "sample": s["sample"],
           "logo": jpeg(logo, 160, 85) if os.path.exists(logo) else None, "voice": s["voice"],
           "email_rules": open(os.path.join(ROOT, "tools", "email-rules.md"), encoding="utf-8").read(),
           "quote_tpl": open(os.path.join(ROOT, "tools", "quote-template.html"), encoding="utf-8").read(),
           "me_files": {n: open(os.path.join(ROOT, "me", n), encoding="utf-8").read() for n in ME_FILES if os.path.exists(os.path.join(ROOT, "me", n))}}
    return ("biz", "b-" + h(doc), dict(doc, at=datetime.datetime.now().isoformat(timespec="seconds")))

def newest(d, col):
    """The rows Claude listed into d/<col>/ (a "~" in an id is saved as "@"), as {id: fields}."""
    out = {}
    for p in glob.glob(os.path.join(d, col, "*.json")):
        r = json.load(open(p)); r = r.get("data", r) if isinstance(r.get("data"), dict) else r
        out[os.path.basename(p)[:-5].replace("@", "~")] = r
    return out

def restore(d, board):
    biz = newest(d, "biz"); leads = newest(d, "leads")
    if biz:
        b = max(biz.values(), key=lambda r: r.get("at") or "")
        os.makedirs(os.path.join(ROOT, "me"), exist_ok=True)
        for n, text in (b.get("me_files") or {}).items():
            if n in ME_FILES:
                open(os.path.join(ROOT, "me", n), "w", encoding="utf-8").write(text)
        if (b.get("logo") or "").startswith("data:image"):
            open(os.path.join(ROOT, "me", "logo.png"), "wb").write(base64.b64decode(b["logo"].split(",", 1)[1]))
    by_lead = {}
    for rid, r in leads.items():
        lid = r.get("id") or rid.split("~")[0]
        if (r.get("at") or "") >= (by_lead.get(lid, {}).get("at") or ""):
            by_lead[lid] = r
    for lid, r in by_lead.items():
        folder = os.path.join(LEADS, lid)
        if not os.path.exists(os.path.join(folder, "facts.json")):
            os.makedirs(os.path.join(folder, "photos"), exist_ok=True)
            json.dump({k: r[k] for k in FACT_KEYS if r.get(k) is not None}, open(os.path.join(folder, "facts.json"), "w"), indent=1)
    for lid, s in newest(d, "work").items():  # his taps so far, so the next sync reports only what's new
        sp = os.path.join(LEADS, lid, "state.json")
        if os.path.isdir(os.path.dirname(sp)) and not os.path.exists(sp):
            json.dump({k: s[k] for k in WORK_KEEP if k in s}, open(sp, "w"), indent=1)
    board["pushed"] = sorted(set(board.get("pushed", [])) | {f"biz/{i}" for i in biz} | {f"leads/{i}" for i in leads})
    shutil.rmtree(d, ignore_errors=True)
    print(f"restored: {'his settings' if biz else 'NO SETTINGS ON THE BOARD (run setup)'} · {len(by_lead)} lead(s)")

def state_of(folder):
    p = os.path.join(folder, "state.json")
    return json.load(open(p)) if os.path.exists(p) else None

def main():
    board = json.load(open(BJ)) if os.path.exists(BJ) else {}
    opened = sorted(glob.glob(os.path.join(LEADS, "*", "facts.json")))
    finished = sorted(glob.glob(os.path.join(LEADS, "done", "*", "*", "facts.json")))
    if "--done" in sys.argv:
        sent = sorted(os.path.relpath(p, PUSH)[:-5].replace("@", "~") for p in glob.glob(os.path.join(PUSH, "*", "*.json")))
        board["pushed"] = sorted(set(board.get("pushed", [])) | set(sent))
        json.dump(board, open(BJ, "w"), indent=1)
        shutil.rmtree(PUSH, ignore_errors=True)
        print(f"board: {len(sent)} row(s) marked as sent.")
        return
    if "--restore" in sys.argv:
        restore(sys.argv[sys.argv.index("--restore") + 1], board)
        json.dump(board, open(BJ, "w"), indent=1)
        return
    if "--have" in sys.argv:
        d = sys.argv[sys.argv.index("--have") + 1]
        have = {f"{os.path.basename(os.path.dirname(p))}/{os.path.basename(p)[:-5].replace('@', '~')}" for p in glob.glob(os.path.join(d, "**", "*.json"), recursive=True)}
        board["pushed"] = sorted(set(board.get("pushed", [])) | have)
        json.dump(board, open(BJ, "w"), indent=1)
        shutil.rmtree(d, ignore_errors=True)
        print(f"board: {len(have)} row(s) already there.")
    for m in missing(settings()):
        print("CHECK: missing", m)
    if "--offline" in sys.argv:
        seed = {"biz": [biz_doc()[2]], "leads": [], "shots": {}, "work": {}}
        for fj in opened + finished:
            folder = os.path.dirname(fj)
            for col, did, doc in lead_docs(folder, with_shots=fj in opened):
                if col == "leads": seed["leads"].append(doc)
                else: seed["shots"][did] = doc
            st = state_of(folder)
            if st: seed["work"][os.path.basename(folder)] = st
        page = open(os.path.join(ROOT, "tools", "board-template.html")).read()
        page = page.replace("const SEED = null;", "const SEED = " + json.dumps(seed).replace("</", "<\\/") + ";", 1)
        out = os.path.join(LEADS, "board.html")
        open(out, "w").write(page)
        print(f"board: {out} · {len(seed['leads'])} lead(s) · {len(page) / 1e6:.1f} MB · open it in any browser")
        return
    if not settings()["business"]["name"]:
        sys.exit("No business name in me/. A fresh session restores it first: the board skill, Start. A new owner: the setup skill.")
    docs = [biz_doc()] + [d for fj in opened for d in lead_docs(os.path.dirname(fj))]
    done = set(board.get("pushed", []))
    new = [(c, i, d) for c, i, d in docs if f"{c}/{i}" not in done]
    shutil.rmtree(PUSH, ignore_errors=True)
    if not new:
        print("board: up to date, nothing to send.")
        return
    batches, cur, size = [], [], 0
    for c, i, d in new:
        os.makedirs(os.path.join(PUSH, c), exist_ok=True)
        p = os.path.join(PUSH, c, i.replace("~", "@") + ".json")  # plain file names: a scheduled run refuses odd ones
        body = json.dumps(d); open(p, "w").write(body)
        if cur and (size + len(body) > 900_000 or len(cur) == 50):
            batches.append(cur); cur, size = [], 0
        cur.append({"op": "set", "collection": c, "doc_id": i, "file_path": os.path.relpath(p, ROOT)}); size += len(body)
    batches.append(cur)
    if not board.get("url"):
        print("NO BOARD YET: publish tools/board-template.html once (the board skill, Publish), save its link in leads/board.json, then run this again.")
        return
    print(f"SEND TO THE BOARD: {len(batches)} ArtifactData batch call(s) (file paths are from this folder), url {board['url']}, then run: python3 tools/board.py --done")
    for b in batches:
        print("writes =", json.dumps(b))

if __name__ == "__main__":
    main()
