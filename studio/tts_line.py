"""한 문장을 한 목소리로 생성 (느린 구간용). 사용: tts_line.py VOICE "TEXT" OUT.wav"""
import json, os, sys, base64, urllib.request, time
voice, text, out = sys.argv[1:4]
body = {"contents": [{"parts": [{"text": text}]}],
        "generationConfig": {"responseModalities": ["AUDIO"],
                             "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}
for attempt in range(4):
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash-tts:generateContent",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GOOGLE_API_KEY"]})
    try:
        d = json.load(urllib.request.urlopen(req, timeout=120))
        open(out, "wb").write(base64.b64decode(d["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]))
        print("ok", out); break
    except urllib.error.HTTPError as e:
        msg = e.read().decode()[:200]
        if e.code in (429, 500, 503) and attempt < 3:
            time.sleep(15 * (attempt + 1)); continue
        print("HTTP", e.code, msg); sys.exit(1)
