"""에피소드 JSON → HyperFrames 프로젝트(index.html + 오디오) 생성.

구성: 인트로 → ① 대화 듣기(보통 속도) → 전환 카드 → ② 천천히 한 번 더(천천히 새로 읽은 음성, 문장 사이 따라 말할 쉼) → 아웃트로
언어 버전마다 따로 만든다(자막: 한국어 + 해당 언어).
사용: python3 build.py ep001/episode.json en   →  ep001/project_en/
"""
import json, os, re, shutil, subprocess, sys
from characters import character_svg
from scenes import SCENES

STUDIO = os.path.dirname(os.path.abspath(__file__))
INTRO, TRANSITION, OUTRO = 1.4, 2.6, 1.4
NORMAL_GAP, SLOW_GAP, TARGET_DB = 0.35, 1.2, -18.0
SLOW_TEMPO = 0.75          # 느린 구간 속도 (음높이는 그대로)
MIN_RATE, MAX_RATE = 3.0, 9.0  # 보통 속도 음성의 정상 범위 (초당 음절)


def sh(*a):
    return subprocess.run(a, check=True, capture_output=True, text=True)


def duration(path):
    return float(sh("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path).stdout)


def speech_spans(path, ws=0.0, we=None):
    """오디오에서 소리가 나는 구간 목록 (입 모양 애니메이션용)."""
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "silencedetect=noise=-38dB:d=0.12", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    total = duration(path)
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    spans, cur = [], 0.0
    for s, e in zip(starts, ends + [total] * (len(starts) - len(ends))):
        if s > cur:
            spans.append((cur, s))
        cur = e
    if cur < total:
        spans.append((cur, total))
    we = total if we is None else we
    return [(max(a, ws), min(b, we)) for a, b in spans if b > ws and a < we and min(b, we) - max(a, ws) > 0.05]


UI = {
    "en": {"chip": "Korean Today", "listen": "Listen", "slow": "Slowly", "repeat": "Repeat after me!"},
    "vi": {"chip": "Tiếng Hàn hôm nay", "listen": "Nghe", "slow": "Chậm lại", "repeat": "Hãy nói theo!"},
}


def mean_db(path, a=None, b=None):
    cmd = ["ffmpeg", "-hide_banner"] + (["-ss", str(a), "-to", str(b)] if a is not None else []) + ["-i", path, "-af", "volumedetect", "-f", "null", "-"]
    return float(re.search(r"mean_volume: (-?[\d.]+)", subprocess.run(cmd, capture_output=True, text=True).stderr).group(1))


def normalize_dialogue(src, lines, out):
    """대화 음성에서 문장마다 음량을 TARGET_DB로 맞춘다 (작게 녹음된 문장 보정)."""
    vols = []
    for l in lines:
        g = max(-6.0, min(9.0, TARGET_DB - mean_db(src, l["start"], l["end"])))
        vols.append(f"volume={g:.1f}dB:enable='between(t,{max(0, l['start'] - 0.2):.2f},{l['end'] + 0.25:.2f})'")
    sh("ffmpeg", "-y", "-i", src, "-af", ",".join(vols + ["alimiter=limit=0.95"]), "-b:a", "160k", out)


def syllable_rate(path, ko):
    return len(re.findall(r"[가-힣]", ko)) / duration(path)


def make_line(raw, voice, ko, emotion=None):
    """한 문장 음성을 만든다.
    1) 감정 지시 없는 기본 음성(raw 옆 .plain.wav)을 만든다 — 기준 길이이자 예비용.
    2) 감정 지시(영어 태그)를 넣어 만들고, 지시문을 소리 내 읽었는지 검사한다:
       기본 음성보다 20% + 0.2초 넘게 길거나, '영어가 들리나?' 질문에 YES면 버리고 다시(최대 3번).
    3) 끝까지 실패하면 기본 음성을 쓴다."""
    from transcribe import has_english
    plain = raw[:-4] + ".plain.wav"
    if not os.path.exists(plain):
        for _ in range(3):
            sh(sys.executable, os.path.join(STUDIO, "tts_line.py"), voice, ko, plain)
            if MIN_RATE <= syllable_rate(plain, ko) <= MAX_RATE:
                break
            os.remove(plain)
        else:
            raise RuntimeError(f"음성 속도가 계속 비정상입니다: {ko}")
    if emotion:
        limit = duration(plain) * 1.2 + 0.2
        trial = raw[:-4] + ".try.wav"
        for n in range(3):
            sh(sys.executable, os.path.join(STUDIO, "tts_line.py"), voice, f"[{emotion}] {ko}", trial)
            d = duration(trial)
            if d <= limit and has_english(trial) is False:
                os.replace(trial, raw)
                print(f"  감정 음성 사용 ({n + 1}번째): {ko} [{emotion}] {d:.2f}s ≤ {limit:.2f}s")
                return
            print(f"  감정 음성 탈락 ({n + 1}번째): {d:.2f}s, 기준 {limit:.2f}s")
        os.remove(trial)
    shutil.copy(plain, raw)
    print(f"  기본 음성 사용: {ko}")


def assemble(ep_dir, proj, ep, mode):
    """문장마다 따로 생성한 음성을 다듬어(앞뒤 무음 제거, 음량 통일) 이어 붙인다. 문장별 (시작, 끝)을 돌려준다.
    mode="normal": 보통 속도, 짧은 쉼 / mode="slow": 같은 음성을 음높이 그대로 느리게(SLOW_TEMPO), 따라 말할 쉼.
    생성된 문장 파일은 ep_dir/tts_normal/에 보관해 다시 만들 때 재사용한다(무료 한도 절약)."""
    lines, chars = ep["lines"], {c["id"]: c for c in ep["characters"]}
    cache = os.path.join(ep_dir, "tts_normal")
    tmp = os.path.join(ep_dir, f"_{mode}")
    os.makedirs(cache, exist_ok=True)
    os.makedirs(tmp, exist_ok=True)
    gap_len = SLOW_GAP if mode == "slow" else NORMAL_GAP
    gap = os.path.join(tmp, "gap.wav")
    sh("ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", str(gap_len), gap)
    parts, times, t = [], [], 0.0
    for i, ln in enumerate(lines):
        raw = os.path.join(cache, f"l{i}.wav")
        if not os.path.exists(raw):
            make_line(raw, chars[ln["speaker"]]["voice"], ln["ko"], ln.get("emotion"))
        piece = os.path.join(tmp, f"l{i}.wav")
        trim = "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse"
        tempo = f",atempo={SLOW_TEMPO}" if mode == "slow" else ""
        sh("ffmpeg", "-y", "-i", raw, "-af", f"{trim}{tempo},adelay=80,apad=pad_dur=0.12", "-ar", "24000", "-ac", "1", piece)
        g = max(-6.0, min(9.0, TARGET_DB - mean_db(piece)))
        sh("ffmpeg", "-y", "-i", piece, "-af", f"volume={g:.1f}dB,alimiter=limit=0.95", "-ar", "24000", piece + ".n.wav")
        os.replace(piece + ".n.wav", piece)
        d = duration(piece)
        times.append((t, t + d))
        parts += [piece, gap]
        t += d + gap_len
    lst = os.path.join(tmp, "list.txt")
    open(lst, "w").write("".join(f"file '{p}'\n" for p in parts[:-1]))
    out = os.path.join(proj, "slow.mp3" if mode == "slow" else "voice.mp3")
    sh("ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-b:a", "160k", out)
    shutil.rmtree(tmp)
    return times, out


FLOWERS = '''<svg viewBox="0 0 300 380"><defs>
  <radialGradient id="pet1" cx="40%" cy="35%"><stop offset="0" stop-color="#ffc2d1"/><stop offset="1" stop-color="#e2456a"/></radialGradient>
  <radialGradient id="pet2" cx="40%" cy="35%"><stop offset="0" stop-color="#ffe0e8"/><stop offset="1" stop-color="#f07895"/></radialGradient>
  <linearGradient id="wrap" x1="0" x2="1"><stop offset="0" stop-color="#fbeee4"/><stop offset="1" stop-color="#d9c2ae"/></linearGradient></defs>
  <path d="M95 190 L150 372 L205 190 Z" fill="url(#wrap)"/>
  <g stroke="#3f7a4c" stroke-width="7"><line x1="150" y1="320" x2="108" y2="150"/><line x1="150" y1="320" x2="150" y2="125"/><line x1="150" y1="320" x2="196" y2="150"/></g>
  <circle cx="105" cy="132" r="44" fill="url(#pet1)"/><circle cx="198" cy="136" r="42" fill="url(#pet1)"/><circle cx="150" cy="100" r="48" fill="url(#pet2)"/>
  <circle cx="105" cy="132" r="14" fill="#f6c453"/><circle cx="198" cy="136" r="13" fill="#f6c453"/><circle cx="150" cy="100" r="15" fill="#f6c453"/>
  <path d="M120 262 Q150 290 180 262 L176 296 L150 280 L124 296 Z" fill="#e2456a"/></svg>'''


def build(ep_path, lang):
    ui = UI[lang]
    ep = json.load(open(ep_path))
    ep_dir = os.path.dirname(os.path.abspath(ep_path))
    proj = os.path.join(ep_dir, f"project_{lang}")
    os.makedirs(proj, exist_ok=True)
    for f in ("gsap.min.js",):
        shutil.copy(os.path.join(STUDIO, f), proj)
    shutil.copytree(os.path.join(STUDIO, "fonts"), os.path.join(proj, "fonts"), dirs_exist_ok=True)
    lines, chars = ep["lines"], {c["id"]: c for c in ep["characters"]}
    if ep.get("audio"):  # 대화 전체를 한 번에 생성한 음성 + 문장 시간을 직접 적은 경우 (시범 영상)
        src = os.path.join(proj, "voice.mp3")
        normalize_dialogue(os.path.join(ep_dir, ep["audio"]), lines, src)
        norm_times = [(l["start"], l["end"]) for l in lines]
    else:
        norm_times, src = assemble(ep_dir, proj, ep, "normal")

    # 시간 계산
    p1 = INTRO
    a1 = duration(src)
    slow_times, slow_path = assemble(ep_dir, proj, ep, "slow")
    a2 = duration(slow_path)
    p2 = p1 + a1 + 0.4 + TRANSITION
    total = round(p2 + a2 + OUTRO, 2)
    part1 = [(p1 + a, p1 + b) for a, b in norm_times]
    part2 = [(p2 + a, p2 + b) for a, b in slow_times]

    # 문장별 표정 상태 (이전 상태를 이어받음)
    state = {cid: {"brow": c.get("brow", "neutral"), "mouth": c.get("mouth", "neutral")} for cid, c in chars.items()}
    states = []
    for l in lines:
        for cid, e in l.get("expr", {}).items():
            state[cid] = {**state[cid], **e}
        states.append({k: dict(v) for k, v in state.items()})

    html = []
    photo = ep.get("style") == "photo"
    if photo:  # 실사풍: 대사마다 지정한 장면 사진(shot)을 보여 준다
        shots = list(dict.fromkeys(l["shot"] for l in lines))
        os.makedirs(os.path.join(proj, "shots"), exist_ok=True)
        for k, s in enumerate(shots):
            shutil.copy(os.path.join(ep_dir, s), os.path.join(proj, "shots", os.path.basename(s)))
            html.append(f'<img id="shot{k}" class="shot clip" src="shots/{os.path.basename(s)}" data-start="0" data-duration="{total}" alt="">')
        html.append(f'<div id="shade" class="clip" data-start="0" data-duration="{total}"></div>')
    else:
        bg, fg = SCENES[ep.get("scene", "cafe")]
        html.append(bg().replace("__DUR__", str(total)))
        for c in ep["characters"]:
            s0 = states[0][c["id"]]
            svg = character_svg({**c, **s0})
            pos = "left:-30px; top:430px;" if c["side"] == "left" else "left:550px; top:418px;"
            html.append(f'<div id="{c["id"]}" class="char clip" data-start="0" data-duration="{total}" style="{pos}">{svg}</div>')
        for p in ep.get("props", []):
            if p["type"] == "flowers":
                html.append(f'<div id="prop-flowers" class="prop clip" data-start="0" data-duration="{total}" '
                            f'style="left:640px; top:1000px; width:260px; height:330px; opacity:0;">{FLOWERS}</div>')
        html.append(fg().replace("__DUR__", str(total)))

    t = ep["topic"]
    html.append(f'''<div id="title" class="clip" data-start="0" data-duration="{total}" data-layout-allow-overlap>
      <div class="chip">오늘의 한국어 · {ui["chip"]}</div>
      <div class="topic">{t["ko"]}</div>
      <div class="topic-sub">{t[lang]}</div></div>''')
    html.append(f'<div id="part1" class="pill clip" data-start="{INTRO - 0.2}" data-duration="{a1 + 0.6}">① 대화 듣기 · {ui["listen"]}</div>')
    html.append(f'<div id="part2" class="pill slow clip" data-start="{p2 - 0.2}" data-duration="{a2 + 0.4}">② 천천히 한 번 더 · {ui["slow"]}</div>')
    html.append(f'<div id="panel" class="clip" data-start="0" data-duration="{total}"></div>')

    def subs(prefix, spans, until):
        for i, (l, (a, b)) in enumerate(zip(lines, spans)):
            end = spans[i + 1][0] - 0.2 if i + 1 < len(spans) else until  # 다음 자막이 나오기 전에 사라지게
            c = chars[l["speaker"]]
            size = " long" if len(l["ko"]) > 34 or len(l[lang]) > 85 else ""  # 긴 대사는 글자를 줄여 카드 안에 맞춘다
            html.append(f'''<div id="{prefix}{i}" class="sub{size} clip" data-start="{a - 0.15:.2f}" data-duration="{end - a + 0.15:.2f}" data-layout-allow-overlap>
      <div class="who" style="background:{c["color"]}">{c["name"]}</div>
      <div class="ko">{l["ko"]}</div><div class="tr">{l[lang]}</div></div>''')
    subs("s1-", part1, p1 + a1 + 0.3)
    subs("s2-", part2, total)

    html.append(f'''<div id="trans" class="clip" data-start="{p1 + a1 + 0.4:.2f}" data-duration="{TRANSITION:.2f}" data-layout-allow-overlap>
      <div class="big">천천히 한 번 더</div><div class="small">{ui["slow"]}</div><div class="hint">따라 말해 보세요! · {ui["repeat"]}</div></div>''')
    html.append(f'<audio id="voice1" class="clip" src="voice.mp3" data-start="{p1}" data-duration="{a1 - 0.06:.2f}"></audio>')
    html.append(f'<audio id="voice2" class="clip" src="slow.mp3" data-start="{p2:.2f}" data-duration="{a2 - 0.06:.2f}"></audio>')

    # 타임라인 이벤트
    js = []
    if photo:
        sid = {s: f"#shot{k}" for k, s in enumerate(shots)}
        js.append(f'tl.set("{sid[lines[0]["shot"]]}",{{opacity:1}},0);')
        for spans, end in ((part1, p1 + a1 + 0.4), (part2, total)):
            for i, l in enumerate(lines):
                a = spans[i][0] - 0.35
                nxt = spans[i + 1][0] - 0.35 if i + 1 < len(spans) else end
                me = sid[l["shot"]]
                for other in sid.values():
                    if other != me:
                        js.append(f'tl.to("{other}",{{opacity:0,duration:0.5}},{a:.2f});')
                js.append(f'tl.to("{me}",{{opacity:1,duration:0.5}},{a:.2f});')
                f = l.get("focus")
                if f:  # 한 장의 사진에서 말하는 사람 얼굴로 확대 (가상 클로즈업). 얼굴을 화면 가로 중앙, 세로 45% 지점에 둔다
                    def at(s):
                        px, py = f["x"] * 1080, f["y"] * 1920
                        return round(540 - 540 - s * (px - 540)), round(864 - 960 - s * (py - 960))
                    z0, z1 = f["zoom"], f["zoom"] * 1.06
                    (x0, y0), (x1, y1) = at(z0), at(z1)
                    js.append(f'tl.fromTo("{me}",{{scale:{z0},x:{x0},y:{y0}}},{{scale:{z1:.3f},x:{x1},y:{y1},duration:{nxt - a + 0.5:.2f},ease:"none"}},{a:.2f});')
                else:
                    js.append(f'tl.fromTo("{me}",{{scale:1.0,x:0,y:0}},{{scale:1.08,x:{-18 if i % 2 else 18},y:0,duration:{nxt - a + 0.5:.2f},ease:"none"}},{a:.2f});')
    for part, spans, audio_off, audio_file in ((1, part1, p1, src), (2, part2, p2, slow_path)):
        if photo:
            break
        for i, (l, (a, b)) in enumerate(zip(lines, spans)):
            for cid, st in states[i].items():
                for kind in ("brow", "mouth"):
                    js.append(f'expr("{cid}","{kind}","{st[kind]}",{a - 0.1:.2f});')
            spk = l["speaker"]
            for cid in chars:
                js.append(f'tl.to("#{cid}",{{filter:"brightness({1 if cid == spk else 0.72})",duration:0.25}},{a - 0.2:.2f});')
            ws, we = a - audio_off, b - audio_off
            for sa, sb in speech_spans(audio_file, ws, we):
                js.append(f'talk("{spk}",{audio_off + sa:.2f},{audio_off + sb:.2f});')
        for p in ep.get("props", []):
            if p["type"] == "flowers":
                sc = lambda i: 1 if part == 1 else (part2[i][1] - part2[i][0]) / (part1[i][1] - part1[i][0])
                show = spans[p["line"]][0] + p["at"] * sc(p["line"])
                give = spans[p["give_line"]][0] + p["give_at"] * sc(p["give_line"])
                js.append(f'tl.set("#prop-flowers",{{opacity:0,x:0,y:120,rotation:10}},{spans[0][0] - 0.3:.2f});')
                js.append(f'tl.to("#prop-flowers",{{opacity:1,y:0,rotation:0,duration:0.45,ease:"back.out(2)"}},{show:.2f});')
                js.append(f'tl.to("#prop-flowers",{{x:-360,y:-30,rotation:-8,duration:0.8,ease:"power2.inOut"}},{give:.2f});')
    for cid in ([] if photo else chars):
        js.append(f'tl.to("#{cid}",{{filter:"brightness(1)",duration:0.3}},{p1 + a1 + 0.2:.2f});')
        js.append(f'tl.to("#{cid}",{{filter:"brightness(1)",duration:0.3}},{p2 + a2 + 0.2:.2f});')
    for i, cid in enumerate([] if photo else chars):
        for x in range(1, int(total / 3.4)):
            js.append(f'blink("{cid}",{x * 3.4 + i * 1.1:.2f});')
        js.append(f'tl.to("#{cid}-breath",{{y:-7,duration:{1.3 + i * 0.15:.2f},repeat:{int(total / 1.3)},yoyo:true,ease:"sine.inOut"}},{i * 0.4});')

    out = TEMPLATE.replace("__DUR__", str(total)).replace("__BODY__", "\n".join(html)).replace("__JS__", "\n  ".join(js))
    open(os.path.join(proj, "index.html"), "w").write(out)
    for f, body in (("package.json", PKG), ("hyperframes.json", HFJ), ("meta.json", json.dumps({"id": ep["id"], "name": f'{ep["id"]}_{lang}'}))):
        open(os.path.join(proj, f), "w").write(body)
    print(f"built {proj}  total={total}s  part1={p1}+{a1:.2f}  part2={p2:.2f}+{a2:.2f}")


PKG = json.dumps({"name": "episode", "private": True, "type": "module", "scripts": {
    "check": "npx --yes hyperframes@0.8.191 check", "render": "npx --yes hyperframes@0.8.191 render"}}, indent=2)
HFJ = json.dumps({"paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"},
                  "media": {"autoProxy": True}}, indent=2)

TEMPLATE = '''<!doctype html>
<html lang="ko" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="gsap.min.js"></script>
<style>
  @font-face { font-family:"NanumSquareRound"; src:url("fonts/NanumSquareRoundB.ttf"); font-weight:700 900; }
  @font-face { font-family:"NanumSquareRound"; src:url("fonts/NanumSquareRoundR.ttf"); font-weight:400; }
  @font-face { font-family:"Latin"; src:url("fonts/LiberationSans-Bold.ttf"); font-weight:700; }
  @font-face { font-family:"Latin"; src:url("fonts/LiberationSans-Regular.ttf"); font-weight:400; }
  * { margin:0; padding:0; box-sizing:border-box; }
  html, body { width:1080px; height:1920px; overflow:hidden; background:#1d1614; }
  #root { width:100%; height:100%; position:relative; overflow:hidden; font-family:"NanumSquareRound",sans-serif; background:#1d1614; }
  .layer { position:absolute; left:0; top:0; width:1080px; height:1920px; }
  .char { position:absolute; width:560px; height:840px; z-index:6; }
  .char svg { width:560px; height:840px; }
  .prop { position:absolute; z-index:9; }
  .shot { position:absolute; left:0; top:0; width:1080px; height:1920px; object-fit:cover; opacity:0; z-index:1; transform-origin:50% 50%; }
  #shade { position:absolute; left:0; top:0; width:1080px; height:1920px; z-index:2;
    background:linear-gradient(180deg, rgba(0,0,0,.78) 0%, rgba(0,0,0,.55) 13%, rgba(0,0,0,0) 27%, rgba(0,0,0,0) 60%, rgba(0,0,0,.45) 100%); }
  .prop svg { width:100%; height:100%; }
  #title { position:absolute; top:70px; left:0; width:1080px; text-align:center; z-index:20; color:#fff; }
  #title .chip { display:inline-block; background:#c8324a; font-size:34px; font-weight:800; padding:10px 28px; border-radius:30px; }
  #title .topic { margin-top:18px; font-size:76px; font-weight:800; letter-spacing:-1px; text-shadow:0 6px 18px rgba(0,0,0,.45); }
  #title .topic-sub { margin-top:8px; font-family:"Latin",sans-serif; font-size:40px; font-weight:700; color:#ffffff; text-shadow:0 3px 10px rgba(0,0,0,.5); }
  .pill { position:absolute; top:350px; left:50%; transform:translateX(-50%); z-index:21; white-space:nowrap;
    font-size:34px; font-weight:800; color:#fff; background:rgba(20,12,10,.55); padding:10px 30px; border-radius:30px; }
  .pill.slow { background:rgba(200,50,74,.85); }
  #panel { position:absolute; left:30px; top:1345px; width:1020px; height:540px; z-index:15; border-radius:44px;
    background:linear-gradient(180deg,#fffaf4,#f4ebe1); box-shadow:0 -12px 40px rgba(0,0,0,.35); }
  .sub { position:absolute; left:30px; top:1345px; width:1020px; height:540px; z-index:16; padding:44px 56px; }
  .sub .who { display:inline-block; color:#fff; font-size:36px; font-weight:800; padding:8px 26px; border-radius:26px; margin-bottom:22px; }
  .sub .ko { font-size:64px; font-weight:800; color:#211915; line-height:1.3; letter-spacing:-1px; word-break:keep-all; }
  .sub .tr { margin-top:28px; font-family:"Latin",sans-serif; font-size:46px; color:#5a4c44; line-height:1.3; }
  .sub.long .ko { font-size:54px; }
  .sub.long .tr { margin-top:20px; font-size:39px; }
  #trans { position:absolute; left:0; top:0; width:1080px; height:1920px; z-index:40; background:rgba(25,16,14,.82);
    display:flex; flex-direction:column; align-items:center; justify-content:center; color:#fff; }
  #trans .big { font-size:96px; font-weight:800; }
  #trans .small { margin-top:16px; font-family:"Latin",sans-serif; font-size:44px; color:#ffd2c4; }
  #trans .hint { margin-top:46px; font-size:36px; background:#c8324a; padding:14px 34px; border-radius:40px; font-weight:800; }
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="__DUR__" data-width="1080" data-height="1920">
__BODY__
</div>
<script>
  window.__timelines = window.__timelines || {};
  const tl = gsap.timeline({ paused: true });
  const KINDS = { brow: ["neutral","sulky","worried","raised"], mouth: ["neutral","smile","pout","o","worried"] };
  function expr(cid, kind, val, t) {
    KINDS[kind].forEach(k => tl.set(`#${cid}-${kind}-${k}`, { opacity: k === val ? 1 : 0 }, t));
  }
  function talk(cid, a, b) {
    for (let t = a; t < b - 0.04; t += 0.15) {
      tl.set(`#${cid}-mouth-talk`, { opacity: 1 }, t);
      tl.set(`#${cid}-mouth-talk`, { opacity: 0 }, Math.min(t + 0.08, b));
    }
  }
  function blink(cid, t) {
    tl.to(`#${cid} .${cid}-eye`, { scaleY: 0.08, transformOrigin: "50% 50%", duration: 0.06, yoyo: true, repeat: 1 }, t);
  }
  tl.from("#title", { y: -50, opacity: 0, duration: 0.6, ease: "back.out(1.8)" }, 0);
  tl.from(".char", { y: 70, opacity: 0, duration: 0.6, ease: "power3.out", stagger: 0.12 }, 0.1);
  tl.from("#panel", { y: 200, opacity: 0, duration: 0.5, ease: "power3.out" }, 0.3);
  document.querySelectorAll(".sub").forEach(el => {
    tl.fromTo(el, { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: 0.25 }, parseFloat(el.dataset.start));
  });
  tl.from("#trans .big", { scale: 0.7, opacity: 0, duration: 0.4, ease: "back.out(2)" }, parseFloat(document.querySelector("#trans").dataset.start));
  __JS__
  window.__timelines["main"] = tl;
  tl.seek(0);
</script>
</body>
</html>
'''

if __name__ == "__main__":
    for lang in (sys.argv[2:] or ["en", "vi"]):
        build(sys.argv[1], lang)
