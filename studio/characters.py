"""입체감 있는 성인 캐릭터 SVG 생성기.

캐릭터 설정(dict)으로 얼굴·머리·옷·소품을 조합한다. 표정 부위는 id가 붙은 레이어로 만들고,
영상 타임라인(GSAP)이 opacity를 바꿔 표정을 전환한다.
"""

W, H = 600, 900

SKIN = {
    "light": ("#fbe3d2", "#f3cdb4", "#d9a588"),
    "medium": ("#f5d3b5", "#e8b896", "#c48a68"),
    "tan": ("#e8bb92", "#d29a70", "#a8704c"),
}
LIP = {"female": ("#d9656e", "#b8434f"), "male": ("#c27a6c", "#9c5a4e")}


def _mirror(d):
    """좌측 기준 path의 x 좌표를 거울 반전한다 (숫자 쌍만 있는 단순 path 전용)."""
    import re
    out, toks = [], re.findall(r"[A-Za-z]|-?\d*\.?\d+", d)
    expect_x = True
    for t in toks:
        if t.isalpha():
            out.append(t)
            expect_x = True
            continue
        v = float(t)
        out.append(f"{W - v:g}" if expect_x else f"{v:g}")
        expect_x = not expect_x
    return " ".join(out)


def _hair_paths(style):
    back, front, extra = "", "", ""
    if style == "f_long":
        back = "M168 330 C158 185 230 150 300 150 C372 150 444 188 432 330 C442 470 458 620 474 720 L126 720 C142 620 158 470 168 330 Z"
        front = ("M178 345 C170 215 238 182 300 182 C372 182 430 220 424 350 C408 285 384 252 344 236 "
                 "C322 278 262 296 208 304 C194 316 184 330 178 345 Z")
        side = "M178 345 C172 430 182 520 198 590 L224 590 C206 500 200 410 208 330 Z"
        extra = side + " " + _mirror(side)
    elif style == "f_bob":
        back = "M170 330 C162 185 230 158 300 158 C372 158 440 188 430 330 C434 420 440 485 432 528 L168 528 C160 485 166 420 170 330 Z"
        front = ("M180 348 C172 212 238 184 300 184 C364 184 428 212 420 348 C404 302 392 282 370 270 "
                 "Q342 300 300 292 Q258 300 232 270 C206 286 190 312 180 348 Z")
        side = "M180 348 C176 425 180 485 190 522 L216 522 C206 465 205 405 210 340 Z"
        extra = side + " " + _mirror(side)
    elif style == "f_bun":
        back = "M300 108 m-62 0 a62 58 0 1 0 124 0 a62 58 0 1 0 -124 0 Z"
        front = ("M180 340 C172 200 240 168 300 168 C366 168 430 200 420 340 C410 290 392 258 360 240 "
                 "C330 232 270 232 240 240 C208 258 190 292 180 340 Z")
    elif style == "m_short":
        front = ("M180 332 C168 196 240 160 306 162 C376 164 432 206 420 332 C414 290 404 262 388 248 "
                 "C350 262 300 250 262 240 C230 254 204 282 192 322 Z")
    elif style == "m_sidepart":
        front = ("M180 336 C166 200 236 158 302 158 C384 158 434 206 420 336 C412 280 396 252 372 238 "
                 "C330 250 268 250 224 228 C204 252 190 292 180 336 Z")
    elif style == "m_older":
        front = ("M184 322 C180 218 240 186 300 186 C362 186 420 218 416 322 C410 286 400 262 382 250 "
                 "C340 236 262 236 220 250 C202 264 190 292 184 322 Z")
    return back, front, extra


def _outfit(o, cid):
    base, dark = o.get("color", "#e9dcc6"), o.get("shade", "#c7b79d")
    torso = "M86 900 C92 720 160 640 254 612 Q300 632 346 612 C440 640 508 720 514 900 Z"
    g = [f'<path d="{torso}" fill="url(#{cid}-cloth)"/>']
    kind = o.get("type", "knit")
    if kind == "knit":
        g.append('<path d="M246 610 Q300 650 354 610 Q300 676 246 610 Z" fill="%s"/>' % dark)
        g.append('<path d="M150 900 C160 800 170 740 190 700" stroke="%s" stroke-width="10" fill="none" opacity=".35"/>' % dark)
    elif kind == "shirt":
        g.append('<path d="M248 606 L300 676 L284 700 L222 640 Z" fill="#fafafa"/><path d="M352 606 L300 676 L316 700 L378 640 Z" fill="#f0f0f0"/>')
        g.append('<circle cx="300" cy="730" r="6" fill="#ddd"/><circle cx="300" cy="790" r="6" fill="#ddd"/>')
    elif kind == "blazer":
        inner = o.get("inner", "#f4f4f4")
        g.append(f'<path d="M250 612 L300 700 L350 612 Q300 640 250 612 Z" fill="{inner}"/>')
        g.append(f'<path d="M250 612 L300 760 L262 900 L214 900 L230 700 Z" fill="{dark}" opacity=".85"/>')
        g.append(f'<path d="M350 612 L300 760 L338 900 L386 900 L370 700 Z" fill="{dark}" opacity=".85"/>')
    elif kind == "apron":
        g.append('<path d="M248 606 L300 676 L284 700 L222 640 Z" fill="#fafafa"/><path d="M352 606 L300 676 L316 700 L378 640 Z" fill="#f0f0f0"/>')
        g.append(f'<rect x="212" y="700" width="176" height="200" rx="14" fill="{o.get("apron", "#3d5a40")}"/>')
        g.append(f'<path d="M222 700 L246 612 M378 700 L354 612" stroke="{o.get("apron", "#3d5a40")}" stroke-width="16"/>')
    elif kind == "hoodie":
        g.append(f'<path d="M210 640 Q300 700 390 640 Q380 600 300 596 Q220 600 210 640 Z" fill="{dark}"/>')
        g.append('<path d="M282 680 L278 760 M318 680 L322 760" stroke="#fafafa" stroke-width="6" stroke-linecap="round"/>')
    # 옷 주름 음영
    g.append(f'<path d="M420 900 C420 800 405 730 380 690" stroke="{dark}" stroke-width="22" fill="none" opacity=".25" stroke-linecap="round"/>')
    return "\n".join(g), base, dark


def character_svg(c):
    """c: {id, gender, skin, hair_style, hair_color, outfit{...}, glasses, earrings}"""
    cid = c["id"]
    hl, sk, sd = SKIN[c.get("skin", "medium")]
    female = c.get("gender") == "female"
    lip_l, lip_d = LIP["female" if female else "male"]
    hair = c.get("hair_color", "#3b2a22")
    hair_hi = c.get("hair_highlight", "#6b4c3c")
    back, front, extra = _hair_paths(c["hair_style"])
    outfit, cloth, cloth_d = _outfit(c.get("outfit", {}), cid)
    brow_w = 6 if female else 8

    def eye(cx, side):
        m = (lambda d: d) if side == "L" else _mirror
        white = m("M218 372 Q250 346 284 370 Q250 390 218 372 Z")
        lid = m("M214 371 Q250 341 288 367")
        lash = m("M219 369 L204 359") if female else ""
        lower = m("M224 378 Q250 390 280 375")
        ix = cx
        return f'''
      <g class="{cid}-eye">
        <clipPath id="{cid}-clip{side}"><path d="{white}"/></clipPath>
        <path d="{white}" fill="#fbf8f6"/>
        <g clip-path="url(#{cid}-clip{side})">
          <circle cx="{ix}" cy="369" r="14" fill="url(#{cid}-iris)"/>
          <circle cx="{ix}" cy="369" r="6.5" fill="#120c0a"/>
          <circle cx="{ix + 5}" cy="363" r="4" fill="#fff"/>
          <path d="{lid}" stroke="#000" stroke-opacity=".18" stroke-width="10" fill="none"/>
        </g>
        <path d="{lid}" stroke="#2a1d18" stroke-width="{6 if female else 5}" fill="none" stroke-linecap="round"/>
        {f'<path d="{lash}" stroke="#2a1d18" stroke-width="5" stroke-linecap="round"/>' if lash else ''}
        <path d="{lower}" stroke="{sd}" stroke-width="3" fill="none" opacity=".7"/>
      </g>'''

    brows = {
        "neutral": "M222 330 Q248 318 282 326",
        "sulky": "M222 320 Q252 322 282 336",
        "worried": "M222 332 Q252 322 282 314",
        "raised": "M222 316 Q250 298 282 310",
    }
    brow_layers = "\n".join(
        f'<g id="{cid}-brow-{k}" opacity="{1 if k == c.get("brow", "neutral") else 0}" stroke="{hair}" stroke-width="{brow_w}" '
        f'stroke-linecap="round" fill="none"><path d="{d}"/><path d="{_mirror(d)}"/></g>'
        for k, d in brows.items())

    mouths = {
        "neutral": f'<path d="M272 478 Q286 470 300 475 Q314 470 328 478 Q300 484 272 478 Z" fill="{lip_d}"/>'
                   f'<path d="M274 479 Q300 496 326 479 Q300 486 274 479 Z" fill="{lip_l}"/>',
        "smile": f'<path d="M264 472 Q300 504 336 472 Q300 490 264 472 Z" fill="{lip_d}"/>'
                 f'<path d="M272 476 Q300 492 328 476" stroke="#fff" stroke-width="4" fill="none" opacity=".8"/>',
        "pout": f'<path d="M282 480 Q300 470 318 480 Q300 492 282 480 Z" fill="{lip_l}"/>'
                f'<path d="M284 480 Q300 476 316 480" stroke="{lip_d}" stroke-width="3" fill="none"/>',
        "o": f'<ellipse cx="300" cy="482" rx="14" ry="18" fill="#4a1c1c" stroke="{lip_l}" stroke-width="5"/>',
        "worried": f'<path d="M276 484 Q300 474 324 484" stroke="{lip_d}" stroke-width="6" fill="none" stroke-linecap="round"/>',
    }
    mouth_layers = "\n".join(
        f'<g id="{cid}-mouth-{k}" opacity="{1 if k == c.get("mouth", "neutral") else 0}">{v}</g>' for k, v in mouths.items())
    talk = (f'<g id="{cid}-mouth-talk" opacity="0">'
            f'<path d="M270 474 Q300 468 330 474 Q326 506 300 509 Q274 506 270 474 Z" fill="#3e1616" stroke="{lip_l}" stroke-width="5"/>'
            f'<path d="M278 477 Q300 473 322 477 L320 484 Q300 482 280 484 Z" fill="#f5f0ea"/></g>')

    glasses = ""
    if c.get("glasses"):
        glasses = ('<g stroke="#2b2b2b" stroke-width="6" fill="#ffffff" fill-opacity=".08">'
                   '<rect x="206" y="340" width="92" height="62" rx="22"/><rect x="302" y="340" width="92" height="62" rx="22"/>'
                   '<path d="M298 362 Q300 356 302 362" fill="none"/></g>')
    earrings = ""
    if c.get("earrings"):
        earrings = '<circle cx="182" cy="410" r="7" fill="#e8c260"/><circle cx="418" cy="410" r="7" fill="#e8c260"/>'

    face = "M300 205 C372 205 420 255 420 345 C420 430 385 495 338 522 C322 531 312 535 300 535 C288 535 278 531 262 522 C215 495 180 430 180 345 C180 255 228 205 300 205 Z"
    return f'''<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <radialGradient id="{cid}-skin" cx="42%" cy="36%" r="72%">
      <stop offset="0" stop-color="{hl}"/><stop offset=".6" stop-color="{sk}"/><stop offset="1" stop-color="{sd}"/>
    </radialGradient>
    <linearGradient id="{cid}-neck" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{sd}"/><stop offset=".45" stop-color="{sk}"/><stop offset="1" stop-color="{sk}"/>
    </linearGradient>
    <linearGradient id="{cid}-hair" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{hair_hi}"/><stop offset=".55" stop-color="{hair}"/><stop offset="1" stop-color="#140d0a"/>
    </linearGradient>
    <linearGradient id="{cid}-cloth" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{cloth}"/><stop offset="1" stop-color="{cloth_d}"/>
    </linearGradient>
    <radialGradient id="{cid}-iris" cx="45%" cy="40%" r="60%">
      <stop offset="0" stop-color="#8a5f45"/><stop offset="1" stop-color="#2a1a12"/>
    </radialGradient>
    <radialGradient id="{cid}-blush"><stop offset="0" stop-color="#ff8c95" stop-opacity="{.38 if female else .22}"/><stop offset="1" stop-color="#ff8c95" stop-opacity="0"/></radialGradient>
    <filter id="{cid}-soft" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="6"/></filter>
    <filter id="{cid}-depth" x="-20%" y="-10%" width="140%" height="130%"><feDropShadow dx="0" dy="16" stdDeviation="16" flood-color="#1a0f0a" flood-opacity=".38"/></filter>
  </defs>
  <g id="{cid}-root" filter="url(#{cid}-depth)">
    <g id="{cid}-breath">
      {f'<path d="{back}" fill="url(#{cid}-hair)"/>' if back else ''}
      {outfit}
      <path d="M258 470 L258 596 Q300 622 342 596 L342 470 Z" fill="url(#{cid}-neck)"/>
      <ellipse cx="182" cy="372" rx="18" ry="34" fill="{sd}"/><ellipse cx="418" cy="372" rx="18" ry="34" fill="{sd}"/>
      <path d="{face}" fill="url(#{cid}-skin)"/>
      <path d="M216 240 Q300 300 384 240 L384 270 Q300 330 216 270 Z" fill="#000" opacity=".12" filter="url(#{cid}-soft)"/>
      <ellipse cx="240" cy="428" rx="36" ry="22" fill="url(#{cid}-blush)"/><ellipse cx="360" cy="428" rx="36" ry="22" fill="url(#{cid}-blush)"/>
      <path d="M307 384 Q316 424 318 442 Q308 452 294 448 Q306 440 307 384 Z" fill="{sd}" opacity=".55"/>
      <path d="M295 386 L292 428" stroke="#fff" stroke-width="5" opacity=".35" stroke-linecap="round"/>
      <path d="M286 446 Q300 456 316 446" stroke="{sd}" stroke-width="4" fill="none" opacity=".8"/>
      {eye(252, "L")}
      {eye(W - 252, "R")}
      {brow_layers}
      {mouth_layers}
      {talk}
      <path d="{front}" fill="url(#{cid}-hair)"/>
      {f'<path d="{extra}" fill="url(#{cid}-hair)"/>' if extra else ''}
      <path d="M250 206 Q300 190 350 206" stroke="#fff" stroke-width="9" fill="none" opacity=".1" stroke-linecap="round"/>
      {glasses}
      {earrings}
    </g>
  </g>
</svg>'''
