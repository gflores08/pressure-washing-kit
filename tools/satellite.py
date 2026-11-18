#!/usr/bin/env python3
"""Satellite measuring for a lead. Standard library only; Pillow is optional (pictures).

  python3 tools/satellite.py fetch "<address>" <lead-folder> [--parcels <url>] [--meters 60]
      Finds the address (US Census geocoder, free, no key) and saves a satellite image at a known scale
      (Esri World Imagery, free, no key) → photos/satellite.png + frame.json.
      --parcels <ArcGIS parcel layer URL> (from business-info.md): pulls the lot's property line, centers the
      image on the lot and draws the line → photos/parcel.geojson. With Pillow also: satellite-grid.png
      (pixel ruler + property line) and satellite-enhanced.png (shadows lifted, contrast up).

  python3 tools/satellite.py dates <lead-folder> [--max 3]
      Every sharp past photo of the same frame (Esri Wayback archive, free, no key): checks the archive,
      keeps only the looks that really differ → photos/dates/<date>.png. Different years show what a
      parked truck or a tree hid in another.

  python3 tools/satellite.py measure <lead-folder> <surfaces.json>
      surfaces.json = {"front driveway": [[x,y],...], ...} in pixels of satellite.png.
      Square feet + edge length per surface → satellite-surfaces.png.

  python3 tools/satellite.py parcel "<address>" <parcel layer URL>
      Does this county parcel map find the property line for this address? (set-up uses it)

  python3 tools/satellite.py drive "<from address>" "<to address>"
      Miles and minutes by road (public OSRM demo server, free, no key).

Rough numbers only. Confirm on site. Uses free public services: fine for a few lookups a day.
Satellite photos can be a year or more old.
"""
import json, math, os, sys, urllib.parse, urllib.request

R = 6378137
UA = {"User-Agent": "lead-report-tool"}
ESRI = "https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer"

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
        return r.read()

def geocode(address):
    q = urllib.parse.urlencode({"address": address, "benchmark": "Public_AR_Current", "format": "json"})
    m = json.loads(get("https://geocoding.geo.census.gov/geocoder/locations/onelineaddress?" + q))["result"]["addressMatches"]
    if not m:
        sys.exit(f"Address not found: {address}")
    c = m[0]["coordinates"]
    return c["x"], c["y"], m[0]["matchedAddress"]

def merc(lon, lat):
    return R * math.radians(lon), R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))

def shoelace(pts):
    return abs(sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))) / 2

def parcel_for(url, lon, lat, matched):
    """The lot for this address. The geocoder's point can land a few houses off, so look close first, then wider,
    and keep the parcel whose fields hold both the house number and the street name."""
    parts = matched.replace(",", " ").split()
    number, street = parts[0], (parts[1] if len(parts) > 1 else "").upper()
    for dist in (30, 250):
        q = urllib.parse.urlencode({"geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint", "inSR": 4326,
                                    "spatialRel": "esriSpatialRelIntersects", "distance": dist, "units": "esriSRUnit_Meter",
                                    "outFields": "*", "outSR": 4326, "f": "geojson"})
        feats = json.loads(get(url.rstrip("/") + "/query?" + q)).get("features", [])
        vals = lambda f: [str(v).strip().upper() for v in f["properties"].values() if v is not None]
        hit = [f for f in feats if number in vals(f) and (not street or any(street in v for v in vals(f)))]
        if hit:
            return hit[0]
        if dist == 30 and len(feats) == 1:
            return feats[0]
    return None

def export(base, bbox, px):
    service = base.rstrip("/")
    if service.endswith("ImageServer"):
        q = {"bbox": ",".join(map(str, bbox)), "bboxSR": 3857, "imageSR": 3857, "size": f"{px},{px}", "format": "png", "f": "image"}
        return get(service + "/exportImage?" + urllib.parse.urlencode(q))
    q = {"bbox": ",".join(map(str, bbox)), "bboxSR": 3857, "imageSR": 3857, "size": f"{px},{px}", "format": "png", "f": "image"}
    return get(service + "/export?" + urllib.parse.urlencode(q))

def to_px(frame, lon, lat):
    x, y = merc(lon, lat); b = frame["bbox"]; px = frame["px"]
    return [(x - b[0]) / (b[2] - b[0]) * px, (b[3] - y) / (b[3] - b[1]) * px]

def pictures(folder, frame):
    try:
        from PIL import Image, ImageDraw, ImageOps
    except ImportError:
        return ""
    ph = os.path.join(folder, "photos"); px = frame["px"]
    base = Image.open(os.path.join(ph, "satellite.png")).convert("RGB")
    lift = ImageOps.autocontrast(base, cutoff=1).point(lambda v: int(255 * (v / 255) ** 0.7))
    for name, im in (("satellite-grid.png", base.copy()), ("satellite-enhanced.png", lift)):
        d = ImageDraw.Draw(im)
        if frame.get("parcel_px"):
            d.line([tuple(p) for p in frame["parcel_px"]] + [tuple(frame["parcel_px"][0])], fill=(255, 40, 40), width=3)
        for i in range(0, px, 50):
            c = (255, 255, 0)
            d.line([(i, 0), (i, 14 if i % 100 == 0 else 6)], fill=c, width=2); d.line([(0, i), (14 if i % 100 == 0 else 6, i)], fill=c, width=2)
            if i % 100 == 0:
                d.text((i + 2, 16), str(i), fill=c); d.text((16, i + 2), str(i), fill=c)
        im.save(os.path.join(ph, name))
    return " + satellite-grid.png (ruler" + (", property line in red" if frame.get("parcel_px") else "") + ") + satellite-enhanced.png"

def fetch(address, folder, parcels=None, meters=None, px=1000):
    lon, lat, matched = geocode(address)
    ph = os.path.join(folder, "photos"); os.makedirs(ph, exist_ok=True)
    parcel, note = None, "the address point is the image center (a street-level guess: find the right lot by eye)"
    if parcels:
        parcel = parcel_for(parcels, lon, lat, matched)
        if parcel:
            ring = parcel["geometry"]["coordinates"][0]
            while isinstance(ring[0][0], list):
                ring = ring[0]
            json.dump(parcel, open(os.path.join(ph, "parcel.geojson"), "w"))
            xs, ys = zip(*[merc(*p[:2]) for p in ring])
            k = math.cos(math.radians(lat))
            lot_sqft = shoelace(list(zip(xs, ys))) * k * k * 10.7639
            span = max(max(xs) - min(xs), max(ys) - min(ys)) * k
            meters = meters or max(60.0, span * 1.35)  # under 0.06 m per pixel the imagery server returns errors
            lon = sum(p[0] for p in ring[:-1]) / (len(ring) - 1); lat = sum(p[1] for p in ring[:-1]) / (len(ring) - 1)
            note = f"property line from the parcel map (red) · lot {lot_sqft:,.0f} sq ft"
        else:
            note = "no parcel found at this address — " + note
    meters = meters or 60.0
    x, y = merc(lon, lat)
    half = meters / 2 / math.cos(math.radians(lat))
    bbox = [x - half, y - half, x + half, y + half]
    open(os.path.join(ph, "satellite.png"), "wb").write(export(ESRI, bbox, px))
    frame = {"address": matched, "lon": lon, "lat": lat, "m_per_px": meters / px, "px": px, "bbox": bbox}
    if parcel:
        frame["parcel_px"] = [to_px(frame, *p[:2]) for p in ring]
        frame["lot_sqft"] = round(lot_sqft)
    json.dump(frame, open(os.path.join(ph, "frame.json"), "w"), indent=1)
    extra = pictures(folder, frame)
    print(f"{matched}\nsaved {os.path.abspath(os.path.join(ph, 'satellite.png'))}{extra}\n"
          f"{meters / px:.3f} m per pixel · 10 px = {meters / px * 10 * 3.28084:.1f} ft · {note}")

WAYBACK_CONFIG = "https://s3-us-west-2.amazonaws.com/config.maptiles.arcgis.com/waybackconfig.json"
WAYBACK_TILE = "https://wayback.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/WMTS/1.0.0/default028mm/MapServer/tile/{k}/{z}/{row}/{col}"

def tile_xy(x, y, z):
    s = 2 * math.pi * R / 2 ** z
    return (x + math.pi * R) / s, (math.pi * R - y) / s

def frame_from_tiles(tmpl, z, bbox, px):
    from PIL import Image
    import io
    x0, y0 = tile_xy(bbox[0], bbox[3], z); x1, y1 = tile_xy(bbox[2], bbox[1], z)
    tx, ty = range(int(x0), int(x1) + 1), range(int(y0), int(y1) + 1)
    mos = Image.new("RGB", (256 * len(tx), 256 * len(ty)))
    for i, c in enumerate(tx):
        for j, r in enumerate(ty):
            mos.paste(Image.open(io.BytesIO(get(tmpl.format(z=z, row=r, col=c)))).convert("RGB"), (i * 256, j * 256))
    box = ((x0 - int(x0)) * 256, (y0 - int(y0)) * 256, (x1 - int(x0)) * 256, (y1 - int(y0)) * 256)
    return mos.crop(tuple(round(v) for v in box)).resize((px, px), Image.LANCZOS)

def dates(folder, most=3):
    import hashlib, concurrent.futures as cf
    try:
        import PIL  # noqa
    except ImportError:
        sys.exit("dates needs Pillow: python3 -m pip install pillow")
    frame = json.load(open(os.path.join(folder, "photos", "frame.json"))); bbox = frame["bbox"]
    cx, cy = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
    rel = sorted((v["itemTitle"][-11:-1], k) for k, v in json.loads(get(WAYBACK_CONFIG)).items())
    def look(item):
        date, k = item
        for z in (21, 20):
            tx, ty = tile_xy(cx, cy, z)
            try:
                b = get(WAYBACK_TILE.format(k=k, z=z, row=int(ty), col=int(tx)))
                if len(b) > 8000:
                    return date, k, z, hashlib.md5(b).hexdigest()
            except Exception:
                pass
        return date, k, None, None
    with cf.ThreadPoolExecutor(12) as ex:
        res = list(ex.map(look, rel))
    seen = {}
    for date, k, z, h in res:
        if z and (z, h) not in seen:
            seen[(z, h)] = (date, k, z)
    picks = sorted(seen.values())[-most:]
    out = os.path.join(folder, "photos", "dates"); os.makedirs(out, exist_ok=True)
    for date, k, z in picks:
        frame_from_tiles(WAYBACK_TILE.replace("{k}", k), z, bbox, frame["px"]).save(os.path.join(out, f"{date}.png"))
        print("sharp photo:", date)
    if not picks:
        print("no sharp past photos here — the main satellite.png is the only look")

def draw(folder, polys, outname, parcel_fill=False):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("(Pillow not installed — no picture; the numbers above are complete)")
        return
    frame = json.load(open(os.path.join(folder, "photos", "frame.json")))
    im = Image.open(os.path.join(folder, "photos", "satellite.png")).convert("RGBA")
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    if frame.get("parcel_px"):
        d.polygon([tuple(p) for p in frame["parcel_px"]], fill=(255, 0, 0, 110) if parcel_fill else None, outline=(255, 40, 40, 255))
    cols = [(0, 200, 255), (255, 0, 200), (0, 255, 120), (255, 200, 0), (160, 90, 255), (255, 255, 255)]
    for i, (name, pts) in enumerate(polys.items()):
        c = cols[i % len(cols)]
        d.polygon([tuple(p) for p in pts], fill=c + (255 if parcel_fill else 90,) if parcel_fill and not name.startswith("concrete") else c + (110,), outline=c + (255,))
        d.text((sum(p[0] for p in pts) / len(pts) - 20, sum(p[1] for p in pts) / len(pts)), name, fill=(255, 255, 255, 255))
    out = os.path.join(folder, "photos", outname)
    Image.alpha_composite(im, ov).convert("RGB").save(out)
    print("drew", os.path.abspath(out), "— open it and check every outline")

def areas(folder, polys):
    m = json.load(open(os.path.join(folder, "photos", "frame.json")))["m_per_px"]
    return {n: (shoelace(p) * m * m * 10.7639, sum(math.dist(p[i], p[(i + 1) % len(p)]) for i in range(len(p))) * m * 3.28084) for n, p in polys.items()}

def measure(folder, surfaces):
    polys = json.load(open(surfaces)); total = 0
    for name, (sqft, edge) in areas(folder, polys).items():
        total += sqft
        print(f"{name}: {sqft:,.0f} sq ft · edge {edge:,.0f} ft")
    print(f"total: {total:,.0f} sq ft")
    draw(folder, polys, "satellite-surfaces.png")

def drive(a, b):
    (x1, y1, _), (x2, y2, _) = geocode(a), geocode(b)
    r = json.loads(get(f"https://router.project-osrm.org/route/v1/driving/{x1},{y1};{x2},{y2}?overview=false"))["routes"][0]
    print(f"{r['distance'] / 1609.34:.1f} mi · {r['duration'] / 60:.0f} min")

def opt(a, flag):
    return a[a.index(flag) + 1] if flag in a else None

if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["fetch"] and len(a) >= 3:
        fetch(a[1], a[2], opt(a, "--parcels"), float(opt(a, "--meters")) if opt(a, "--meters") else None)
    elif a[:1] == ["dates"] and len(a) >= 2:
        dates(a[1], int(opt(a, "--max") or 3))
    elif a[:1] == ["measure"] and len(a) == 3:
        measure(a[1], a[2])
    elif a[:1] == ["parcel"] and len(a) == 3:
        lon, lat, m = geocode(a[1]); hit = parcel_for(a[2], lon, lat, m)
        print(f"{m}: " + ("property line FOUND, this parcel map works" if hit else "NOT FOUND on this parcel map"))
    elif a[:1] == ["drive"] and len(a) == 3:
        drive(a[1], a[2])
    else:
        sys.exit(__doc__)
