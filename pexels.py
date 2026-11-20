# Ambil foto stok dari Pexels (gratis untuk komersial, tanpa wajib atribusi).
# Job: {"items":[{"id":"krl","query":"commuter train phone","n":2,"orientation":"portrait"}]}
import json, os, sys, time, urllib.parse, urllib.request

KEY = os.environ["PEXELS_API_KEY"]
JOB = json.loads(os.environ["JOB"])
OUT = os.path.join("out", os.environ.get("JOB_ID") or time.strftime("%Y%m%d-%H%M%S"))
os.makedirs(OUT, exist_ok=True)

def get(url, auth=True, raw=False):
    h = {"User-Agent": "tembusincpns-studio/1.0"}
    if auth: h["Authorization"] = KEY
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=60) as r:
        return r.read() if raw else json.load(r)

hasil, kredit = [], []
for it in JOB.get("items", []):
    n = int(it.get("n", 2))
    q = urllib.parse.urlencode({"query": it["query"], "per_page": 15,
                                "orientation": it.get("orientation", "portrait"), "locale": it.get("locale", "id-ID")})
    try:
        fotos = get("https://api.pexels.com/v1/search?" + q).get("photos", [])
        got = 0
        for p in fotos[: max(n, 1) * 2]:
            if got >= n: break
            try:
                data = get(p["src"]["large2x"], auth=False, raw=True)
                got += 1
                fn = f'{it["id"]}-{got}.jpg'
                open(os.path.join(OUT, fn), "wb").write(data)
                kredit.append({"file": fn, "fotografer": p.get("photographer"), "sumber": p.get("url"),
                               "alt": p.get("alt"), "lisensi": "Pexels License (bebas komersial)"})
            except Exception as e:
                print("lewati", p.get("id"), e, file=sys.stderr)
        hasil.append({"id": it["id"], "ok": got > 0, "jumlah": got})
        print("OK" if got else "KOSONG", it["id"], got)
    except Exception as e:
        hasil.append({"id": it["id"], "ok": False, "error": str(e)[:300]})
        print("GAGAL", it["id"], e, file=sys.stderr)
json.dump(kredit, open(os.path.join(OUT, "kredit.json"), "w"), indent=1, ensure_ascii=False)
json.dump(hasil, open(os.path.join(OUT, "hasil.json"), "w"), indent=1)
print(json.dumps(hasil))
