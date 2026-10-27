"""오디오 받아쓰기 (대사 외 말이 섞였는지 검사용). 사용: transcribe.py a.wav b.wav ..."""
import json, os, sys, base64, urllib.request, time, mimetypes
MODELS = ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.6-flash"]
def transcribe(path):
    mime = "audio/wav" if path.endswith(".wav") else "audio/mp3"
    b = base64.b64encode(open(path, "rb").read()).decode()
    body = {"contents": [{"parts": [{"inlineData": {"mimeType": mime, "data": b}},
            {"text": "이 오디오에서 들리는 말을 그대로 받아 적어. 영어 단어가 들리면 그대로 적고, 다른 설명은 하지 마."}]}]}
    for attempt in range(3):
        for m in MODELS:
            req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent",
                data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GOOGLE_API_KEY"]})
            try:
                d = json.load(urllib.request.urlopen(req, timeout=90))
                return d["candidates"][0]["content"]["parts"][0]["text"].strip()
            except Exception:
                continue
        time.sleep(15)
    return None
if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(os.path.basename(p), "→", transcribe(p))
