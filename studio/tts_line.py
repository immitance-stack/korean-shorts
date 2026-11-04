"""한 문장을 한 목소리로 생성 (느린 구간용). 사용: tts_line.py VOICE "TEXT" OUT.wav"""
import json, os, sys, base64, urllib.request, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gemini_keys import KEYS
voice, text, out = sys.argv[1:4]
body = {"contents": [{"parts": [{"text": text}]}],
        "generationConfig": {"responseModalities": ["AUDIO"],
                             "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}
for attempt in range(4):
    last = None
    for key in KEYS:  # 첫 키가 한도(429)에 걸리면 다음 키(다른 계정)로 넘어간다
        req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash-tts:generateContent",
                                     data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json", "x-goog-api-key": key})
        try:
            d = json.load(urllib.request.urlopen(req, timeout=120))
            open(out, "wb").write(base64.b64decode(d["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]))
            print("ok", out); sys.exit(0)
        except urllib.error.HTTPError as e:
            last = (e.code, e.read().decode()[:200])
            if e.code not in (429, 500, 503):
                break
    if last and last[0] in (429, 500, 503) and attempt < 3:
        time.sleep(15 * (attempt + 1)); continue
    print("HTTP", *(last or ("?", "GOOGLE_API_KEY 없음"))); sys.exit(1)
