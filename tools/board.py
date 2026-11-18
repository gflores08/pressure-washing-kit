#!/usr/bin/env python3
"""The lead board's data. The board page (tools/board-template.html) is published once; leads reach it as small
database rows, so a new lead never republishes the page.

  python3 tools/board.py            write what the board doesn't have yet to leads/_push/ and print the one
                                    ArtifactData batch call that sends it (the url is in leads/board.json)
  python3 tools/board.py --done     after that call worked: remember it was sent, clear leads/_push/
  python3 tools/board.py --have leads/_have
                                    a send was refused because a row already exists: Claude lists biz, leads and
                                    shots (out_dir leads/_have); this remembers what the board has, then prints the rest
  python3 tools/board.py --offline  leads/board.html: the whole board in one file, for a computer without
                                    Claude artifacts (taps stay in that browser; "Save with Claude" copies them)

Rows (never edited, only added, so no versions are needed):
  biz/<hash>         name, phone, prices, minimum, speed, Good package, terms, sample flag, logo (from me/)
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
           "quote_tpl": open(os.path.join(ROOT, "tools", "quote-template.html"), encoding="utf-8").read()}
    return ("biz", "b-" + h(doc), dict(doc, at=datetime.datetime.now().isoformat(timespec="seconds")))

def state_of(folder):
    p = os.path.join(folder, "state.json")
    return json.load(open(p)) if os.path.exists(p) else None

def main():
    board = json.load(open(BJ)) if os.path.exists(BJ) else {}
    opened = sorted(glob.glob(os.path.join(LEADS, "*", "facts.json")))
    finished = sorted(glob.glob(os.path.join(LEADS, "done", "*", "*", "facts.json")))
    if "--done" in sys.argv:
        sent = sorted(os.path.relpath(p, PUSH)[:-5] for p in glob.glob(os.path.join(PUSH, "*", "*.json")))
        board["pushed"] = sorted(set(board.get("pushed", [])) | set(sent))
        json.dump(board, open(BJ, "w"), indent=1)
        shutil.rmtree(PUSH, ignore_errors=True)
        print(f"board: {len(sent)} row(s) marked as sent.")
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
        p = os.path.join(PUSH, c, i + ".json")
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
