# Ambil foto stok dari Pixabay (gratis untuk komersial, tanpa wajib atribusi).
# Job: {"items":[{"id":"krl","query":"train passenger phone","n":2,"orientation":"vertical"}]}
import json, os, sys, time, urllib.parse, urllib.request

KEY = os.environ["PIXABAY_API_KEY"]
JOB = json.loads(os.environ["JOB"])
OUT = os.path.join("out", os.environ.get("JOB_ID") or time.strftime("%Y%m%d-%H%M%S"))
os.makedirs(OUT, exist_ok=True)

def get(url, raw=False):
    req = urllib.request.Request(url, headers={"User-Agent": "tembusincpns-studio/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read() if raw else json.load(r)

hasil, kredit = [], []
for it in JOB.get("items", []):
    n = int(it.get("n", 2))
    q = urllib.parse.urlencode({"key": KEY, "q": it["query"], "image_type": "photo", "safesearch": "true",
                                "orientation": it.get("orientation", "all"), "per_page": 20,
                                "min_width": 1000, "order": it.get("order", "popular")})
    try:
        hits = get("https://pixabay.com/api/?" + q).get("hits", [])
        got = 0
        for p in hits:
            if got >= n: break
            try:
                data = get(p.get("largeImageURL") or p["webformatURL"], raw=True)
                got += 1
                fn = f'{it["id"]}-{got}.jpg'
                open(os.path.join(OUT, fn), "wb").write(data)
                kredit.append({"file": fn, "fotografer": p.get("user"), "sumber": p.get("pageURL"),
                               "tag": p.get("tags"), "lisensi": "Pixabay Content License (bebas komersial)"})
            except Exception as e:
                print("lewati", p.get("id"), e, file=sys.stderr)
        hasil.append({"id": it["id"], "ok": got > 0, "jumlah": got})
        print("OK" if got else "KOSONG", it["id"], got)
    except Exception as e:
        msg = str(e).replace(KEY, "***")
        hasil.append({"id": it["id"], "ok": False, "error": msg[:300]})
        print("GAGAL", it["id"], msg, file=sys.stderr)
json.dump(kredit, open(os.path.join(OUT, "kredit.json"), "w"), indent=1, ensure_ascii=False)
json.dump(hasil, open(os.path.join(OUT, "hasil.json"), "w"), indent=1)
print(json.dumps(hasil))
