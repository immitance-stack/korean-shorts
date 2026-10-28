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
def has_english(path):
    """음성에 영어 말소리가 섞였는지 따로 묻는다. True/False, 판단 실패 시 None."""
    mime = "audio/wav" if path.endswith(".wav") else "audio/mp3"
    b = base64.b64encode(open(path, "rb").read()).decode()
    body = {"contents": [{"parts": [{"inlineData": {"mimeType": mime, "data": b}},
            {"text": "Listen carefully. Does this audio contain ANY spoken English words (for example stage directions like 'slowly', 'warmly', 'apologetic')? Answer with exactly one word: YES or NO."}]}]}
    for attempt in range(3):
        for m in MODELS:
            req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent",
                data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GOOGLE_API_KEY"]})
            try:
                d = json.load(urllib.request.urlopen(req, timeout=90))
                ans = d["candidates"][0]["content"]["parts"][0]["text"].strip().upper()
                return ans.startswith("YES")
            except Exception:
                continue
        time.sleep(15)
    return None


if __name__ == "__main__":
    import re
    bad = 0
    for p in sys.argv[1:]:
        t = transcribe(p)
        flag = ""
        if t is None:
            flag, bad = "  ⚠ 받아쓰기 실패", bad + 1
        elif re.search(r"[A-Za-z]{2,}", t):  # 영어 단어가 들리면 실패로 본다
            flag, bad = "  ⚠ 영어가 섞임", bad + 1
        print(os.path.basename(p), "→", t, flag)
    sys.exit(1 if bad else 0)
