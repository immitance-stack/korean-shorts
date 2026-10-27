"""장면 배경(뒤)과 전경(앞) SVG. 배경은 흐림 처리로 원근감(얕은 피사계 심도)을 준다."""


def _wrap(inner, defs="", z=0, sid="bg"):
    return (f'<svg id="{sid}" class="layer clip" data-start="0" data-duration="__DUR__" viewBox="0 0 1080 1920" '
            f'style="z-index:{z}"><defs>{defs}</defs>{inner}</svg>')


BLUR = '<filter id="dof" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="7"/></filter>'
VIGNETTE = ('<radialGradient id="vig" cx="50%" cy="45%" r="75%"><stop offset=".55" stop-color="#000" stop-opacity="0"/>'
            '<stop offset="1" stop-color="#000" stop-opacity=".55"/></radialGradient>')


def cafe():
    defs = BLUR + VIGNETTE + '''
      <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4b4078"/><stop offset=".6" stop-color="#d9877a"/><stop offset="1" stop-color="#f3c08a"/></linearGradient>
      <linearGradient id="wall" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5e4136"/><stop offset="1" stop-color="#3e2a23"/></linearGradient>
      <radialGradient id="lampglow"><stop offset="0" stop-color="#ffd99a" stop-opacity=".95"/><stop offset="1" stop-color="#ffd99a" stop-opacity="0"/></radialGradient>
      <linearGradient id="shelf" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8a5c40"/><stop offset="1" stop-color="#5e3d2a"/></linearGradient>'''
    inner = '''
      <rect width="1080" height="1920" fill="url(#wall)"/>
      <g filter="url(#dof)">
        <rect x="60" y="360" width="620" height="840" rx="24" fill="url(#sky)"/>
        <g fill="#352c55" opacity=".9"><rect x="80" y="880" width="110" height="320"/><rect x="200" y="800" width="80" height="400"/>
          <rect x="300" y="930" width="130" height="270"/><rect x="450" y="840" width="100" height="360"/><rect x="560" y="900" width="110" height="300"/></g>
        <g fill="#ffe2a0" opacity=".85"><rect x="220" y="830" width="16" height="22"/><rect x="250" y="880" width="16" height="22"/>
          <rect x="470" y="870" width="16" height="22"/><rect x="590" y="930" width="16" height="22"/><rect x="120" y="920" width="16" height="22"/></g>
        <rect x="60" y="360" width="620" height="840" rx="24" fill="none" stroke="#2c1d18" stroke-width="20"/>
        <line x1="370" y1="360" x2="370" y2="1200" stroke="#2c1d18" stroke-width="14"/>
        <rect x="730" y="420" width="300" height="24" fill="url(#shelf)"/><rect x="730" y="640" width="300" height="24" fill="url(#shelf)"/>
        <g><rect x="750" y="350" width="40" height="70" rx="6" fill="#c9d6c4"/><rect x="800" y="330" width="46" height="90" rx="6" fill="#e8c27a"/>
          <circle cx="900" cy="385" r="34" fill="#d98a6a"/><rect x="950" y="345" width="50" height="75" rx="8" fill="#9fb8c9"/>
          <rect x="760" y="560" width="70" height="80" rx="10" fill="#f0e6d6"/><path d="M880 640 q40 -110 80 0 z" fill="#5f8f5c"/></g>
        <line x1="210" y1="0" x2="210" y2="250" stroke="#1c120e" stroke-width="5"/><line x1="880" y1="0" x2="880" y2="200" stroke="#1c120e" stroke-width="5"/>
        <circle cx="210" cy="300" r="220" fill="url(#lampglow)"/><circle cx="880" cy="250" r="220" fill="url(#lampglow)"/>
        <path d="M160 250 h100 l-18 52 h-64 z" fill="#f0b44a"/><path d="M830 200 h100 l-18 52 h-64 z" fill="#f0b44a"/>
      </g>'''
    return _wrap(inner, defs, 0, "bg")


def cafe_front():
    defs = '''<linearGradient id="tabletop" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#c99567"/><stop offset="1" stop-color="#7a4c31"/></linearGradient>
      <linearGradient id="cup" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ffffff"/><stop offset=".7" stop-color="#ece8e4"/><stop offset="1" stop-color="#c9c3bd"/></linearGradient>
      <radialGradient id="vig2" cx="50%" cy="40%" r="80%"><stop offset=".6" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".45"/></radialGradient>'''
    inner = '''
      <path d="M-20 1215 L1100 1215 L1100 1320 L-20 1320 Z" fill="url(#tabletop)"/>
      <path d="M-20 1215 L1100 1215" stroke="#e7b98d" stroke-width="10"/>
      <ellipse cx="540" cy="1222" rx="420" ry="10" fill="#fff" opacity=".18"/>
      <g transform="translate(250 1150)"><ellipse cx="0" cy="70" rx="95" ry="16" fill="#000" opacity=".25"/><ellipse cx="0" cy="64" rx="90" ry="16" fill="#e9e4de"/>
        <path d="M-58 0 L-50 58 Q0 70 50 58 L58 0 Z" fill="url(#cup)"/><ellipse cx="0" cy="0" rx="58" ry="12" fill="#5a3322"/>
        <path d="M56 12 q40 6 0 40" stroke="#e3ddd6" stroke-width="12" fill="none"/></g>
      <g transform="translate(830 1158)"><ellipse cx="0" cy="62" rx="85" ry="14" fill="#000" opacity=".25"/><ellipse cx="0" cy="56" rx="80" ry="14" fill="#e9e4de"/>
        <path d="M-50 0 L-44 50 Q0 62 44 50 L50 0 Z" fill="url(#cup)"/><ellipse cx="0" cy="0" rx="50" ry="10" fill="#5a3322"/>
        <path d="M-48 10 q-36 6 0 36" stroke="#e3ddd6" stroke-width="11" fill="none"/></g>
      <rect width="1080" height="1320" fill="url(#vig2)"/>'''
    return _wrap(inner, defs, 12, "fg")


SCENES = {"cafe": (cafe, cafe_front)}
