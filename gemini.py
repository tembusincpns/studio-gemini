# Studio Gemini TembusinCPNS: membuat suara (TTS) dan foto dari daftar job JSON.
# Job: {"items":[{"id":"v1","type":"tts","text":"...","voice":"Puck","style":"..."},
#                {"id":"f1","type":"image","prompt":"...","aspect":"4:5"}]}
import base64, json, os, sys, time, urllib.request, urllib.error, wave

KEY = os.environ["GEMINI_API_KEY"]
JOB = json.loads(os.environ["JOB"])
OUT = os.path.join("out", os.environ.get("JOB_ID") or time.strftime("%Y%m%d-%H%M%S"))
os.makedirs(OUT, exist_ok=True)
BASE = "https://generativelanguage.googleapis.com/v1beta/models/"
TTS_MODEL = os.environ.get("TTS_MODEL", "gemini-2.5-flash-preview-tts")
IMG_MODEL = os.environ.get("IMG_MODEL", "gemini-2.5-flash-image")

def call(model, body):
    req = urllib.request.Request(BASE + model + ":generateContent", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "x-goog-api-key": KEY})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:300]
            print("HTTP", e.code, msg, file=sys.stderr)
            if e.code in (429, 500, 503) and attempt < 2:
                time.sleep(20 * (attempt + 1)); continue
            raise RuntimeError(f"HTTP {e.code}: {msg}")

def inline(resp):
    for c in resp.get("candidates", []):
        for p in c.get("content", {}).get("parts", []):
            if "inlineData" in p:
                return p["inlineData"]
    raise RuntimeError("tidak ada data di respons: " + json.dumps(resp)[:300])

hasil = []
for it in JOB.get("items", []):
    try:
        if it["type"] == "tts":
            teks = (it.get("style", "Bacakan dengan gaya santai, semangat, jelas, bahasa Indonesia:") + "\n" + it["text"])
            d = inline(call(TTS_MODEL, {"contents": [{"parts": [{"text": teks}]}],
                "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"voiceConfig":
                {"prebuiltVoiceConfig": {"voiceName": it.get("voice", "Puck")}}}}}))
            pcm = base64.b64decode(d["data"])
            path = os.path.join(OUT, it["id"] + ".wav")
            with wave.open(path, "wb") as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(pcm)
        elif it["type"] == "image":
            d = inline(call(IMG_MODEL, {"contents": [{"parts": [{"text": it["prompt"]}]}],
                "generationConfig": {"responseModalities": ["IMAGE"],
                "imageConfig": {"aspectRatio": it.get("aspect", "4:5")}}}))
            ext = "png" if "png" in d.get("mimeType", "png") else "jpg"
            path = os.path.join(OUT, it["id"] + "." + ext)
            open(path, "wb").write(base64.b64decode(d["data"]))
        else:
            raise RuntimeError("type tidak dikenal")
        hasil.append({"id": it["id"], "ok": True, "file": os.path.basename(path)})
        print("OK", it["id"])
    except Exception as e:
        hasil.append({"id": it.get("id"), "ok": False, "error": str(e)[:300]})
        print("GAGAL", it.get("id"), e, file=sys.stderr)
json.dump(hasil, open(os.path.join(OUT, "hasil.json"), "w"), indent=1)
print(json.dumps(hasil))
