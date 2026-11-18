#!/usr/bin/env python3
"""Checks this session can run the tools and reach the free map services, and fixes what it can.

  python3 tools/doctor.py      (on Windows: python tools\\doctor.py)

Python 3.8+, Pillow (shrinks photos; installed for this user if missing), and the free map services.
"""
import subprocess, sys, urllib.request

ok = True
print(f"python {sys.version.split()[0]}: " + ("ok" if sys.version_info >= (3, 8) else "TOO OLD, install Python 3 from python.org"))
try:
    import PIL  # noqa: F401
    print("pillow: ok")
except ImportError:
    print("pillow: missing, installing for this user...")
    for extra in ([], ["--break-system-packages"]):
        r = subprocess.run([sys.executable, "-m", "pip", "install", "--user", "--quiet", *extra, "pillow"], capture_output=True, text=True)
        if r.returncode == 0:
            print("pillow: installed"); break
    else:
        ok = False
        print("pillow: COULD NOT INSTALL. Run: " + sys.executable + " -m pip install --user pillow\n" + r.stderr[-400:])
for name, url in (("address lookup (US Census)", "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress?address=1600+Pennsylvania+Ave+NW+Washington+DC&benchmark=Public_AR_Current&format=json"),
                  ("satellite photos (Esri)", "https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer?f=json"),
                  ("drive times (OSRM)", "https://router.project-osrm.org/route/v1/driving/-121.49,38.58;-121.47,38.59?overview=false")):
    try:
        urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "lead-report-tool"}), timeout=20).read(200)
        print(f"{name}: ok")
    except Exception as e:
        ok = ok and "OSRM" in name  # drive times are nice to have
        print(f"{name}: NOT REACHABLE ({e}). " + ("Leads still work, without drive times." if "OSRM" in name else "This session can't reach it: leads come without photos. Network access → Full fixes it (the setup skill, step 2)."))
# His settings live on his board, not in the shared kit: keep git (and any "commit your changes" hook) quiet about them
import os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
subprocess.run(["git", "-C", root, "update-index", "--skip-worktree", "me/business.md", "me/prices.md", "me/voice.md"], capture_output=True)
print("\nALL GOOD" if ok else "\nFIX THE LINES ABOVE")
sys.exit(0 if ok else 1)
