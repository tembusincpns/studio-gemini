# Ambil foto stok berlisensi bebas-komersial dari Openverse (tanpa API key).
# Job: {"items":[{"id":"f1","query":"student studying phone train","n":3}]}
# Hasil: out/<JOB_ID>/<id>-1.jpg ... + kredit.json (pencipta, lisensi, sumber) untuk dicantumkan bila CC BY.
import json, os, sys, time, urllib.parse, urllib.request

JOB = json.loads(os.environ["JOB"])
OUT = os.path.join("out", os.environ.get("JOB_ID") or time.strftime("%Y%m%d-%H%M%S"))
os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "tembusincpns-studio/1.0 (github.com/tembusincpns/studio-gemini)"}
BLOK = ("gta", "rockstar", "logo", "screenshot", "poster", "cover")

def get(url, raw=False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read() if raw else json.load(r)

hasil, kredit = [], []
for it in JOB.get("items", []):
    n = int(it.get("n", 3))
    q = urllib.parse.urlencode({"q": it["query"], "license_type": "commercial,modification",
                                "page_size": 40, "mature": "false", "extension": "jpg,png"})
    try:
        res = get("https://api.openverse.org/v1/images/?" + q).get("results", [])
        res = [r for r in res if (r.get("width") or 0) >= 1000
               and not any(b in (r.get("title") or "").lower() for b in BLOK)]
        res.sort(key=lambda r: -(r.get("width") or 0) * (r.get("height") or 0) / 1e6 if (r.get("width") or 0) < 2500 else 0)
        got = 0
        for r in res:
            if got >= n: break
            try:
                data = get(r["url"], raw=True)
                if len(data) < 60000: continue
                got += 1
                fn = f'{it["id"]}-{got}.jpg'
                open(os.path.join(OUT, fn), "wb").write(data)
                kredit.append({"file": fn, "judul": r.get("title"), "pencipta": r.get("creator"),
                               "lisensi": f'{r.get("license","").upper()} {r.get("license_version","")}'.strip(),
                               "sumber": r.get("foreign_landing_url"), "atribusi": r.get("attribution")})
            except Exception as e:
                print("lewati", r.get("url"), e, file=sys.stderr)
        hasil.append({"id": it["id"], "ok": got > 0, "jumlah": got})
        print("OK" if got else "KOSONG", it["id"], got)
    except Exception as e:
        hasil.append({"id": it["id"], "ok": False, "error": str(e)[:300]})
        print("GAGAL", it["id"], e, file=sys.stderr)
json.dump(kredit, open(os.path.join(OUT, "kredit.json"), "w"), indent=1, ensure_ascii=False)
json.dump(hasil, open(os.path.join(OUT, "hasil.json"), "w"), indent=1)
print(json.dumps(hasil))
