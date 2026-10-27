# 한국어 학습 쇼츠 제작 — 작업 설명서

이 저장소는 한국어 선생님(사용자)이 준 짧은 대화 대본으로 학습용 쇼츠를 만들어 올리는 시스템이다.
매 세션은 이 문서의 절차를 따른다. 사용자는 컴퓨터에 익숙하지 않으므로 **쉬운 한국어로, 단계별로** 안내한다.
시간은 항상 **한국 시간(KST)** 으로 말한다.

## 영상 형식
- 9:16 세로(1080×1920), 길이는 대화에 따라 30~60초.
- 구성: 인트로(주제) → ① 대화 듣기(보통 속도) → "천천히 한 번 더 / 따라 말해 보세요" 카드 → ② 천천히 한 번 더(문장 사이 쉼) → 끝.
- 언어 버전 2개: `en`(한국어+영어 자막), `vi`(한국어+베트남어 자막). 그림·음성은 같고 자막만 다르다.
- 그림체: 성숙한 비율의 입체 일러스트(명암·그림자). 배경은 흐림 처리(원근감).
- 다음 화 예고 없음. 매 편이 독립된 대화.

## 업로드 대상
| 플랫폼 | 버전 | 방법 |
|---|---|---|
| YouTube | en, vi 둘 다 (**한 채널**에 같은 날 2편) | Zapier `upload_video` (영상 파일은 GitHub Release의 공개 주소로 전달) |
| TikTok | vi | 사용자가 직접 업로드. 영상 파일 + 설명/해시태그를 SendUserFile로 전달 |
| Instagram 릴스 | — | 사용하지 않음 |

**사용자가 승인하기 전에는 절대 업로드하지 않는다.** 승인은 매번 받는다.

## 주간 흐름
1. **월·화요일 – 대본 받기 (사용자가 세션을 열어 대본을 붙여넣음)**
   - 대본: 여자와 남자가 2번 정도 주고받는 대화.
   - 그 상황의 **앞뒤 이야기를 조금 덧붙여 3~4편**으로 나눈다. 각 편은 4~6문장, 자연스러운 구어체, 학습자 수준에 맞는 표현.
   - 편마다 `episodes/<YYYY-Www>/<NN>/episode.json`을 만든다(아래 형식). 번역은 **DeepL**(`translate-text`, EN-US·VI)로 하고, 베트남어 호칭(anh/em, chị/em, bạn 등)은 관계에 맞게 다듬는다.
   - 편별 줄거리·대사·번역을 표로 보여 주고 **대본 승인**을 받는다. 승인되면 `status: "script_approved"`, 업로드 예정일(`publish_date`, 다음 날부터 하루 1편)을 적고 커밋·푸시한다.
2. **화~토요일 – 매일 제작 (루틴이 새 세션을 자동으로 연다)**
   - `status == "script_approved"`이고 `publish_date`가 오늘 이전인 편 중 가장 이른 것 1편을 만든다. 없으면 아무것도 하지 않고 끝낸다.
   - 제작 → 검사 → 사용자에게 영상 2개(en, vi)와 YouTube 제목·설명, TikTok 설명을 보내고 **승인 요청**. `status: "awaiting_approval"`.
   - 사용자가 "승인" → 업로드(아래) → `status: "uploaded"`, 링크 기록 → 커밋·푸시.
   - "수정: ..." → 고쳐서 다시 보여 준다.

## 제작 명령
```bash
cd studio
python3 build.py ../episodes/<주>/<NN>/episode.json        # en, vi 두 프로젝트 생성 (TTS 자동 생성·캐시)
cd ../episodes/<주>/<NN>/project_en
HYPERFRAMES_SKIP_SKILLS=1 npx -y hyperframes@0.8.191 check     # 오류 0개여야 함
HYPERFRAMES_SKIP_SKILLS=1 npx -y hyperframes@0.8.191 snapshot --at 3,8,15   # 프레임을 직접 보고 확인
HYPERFRAMES_SKIP_SKILLS=1 npx -y hyperframes@0.8.191 render    # renders/*.mp4
```
- 필요 환경: `GOOGLE_API_KEY`(환경 변수), ffmpeg, Node 22, Chromium(클라우드 기본 설치). 폰트·GSAP은 저장소에 포함(외부 CDN은 렌더러에서 막힘).
- 음성: Gemini `gemini-3.8-flash-tts`, 문장마다 따로 생성. 감정 지시는 **영어 태그**(`[apologetic]`)로만 — 한국어 태그는 소리 내어 읽어 버린다.
- 음량은 문장마다 -18dB로 자동 통일.

### 제작 후 검사 (반드시)
1. `python3 studio/transcribe.py episodes/.../tts_normal/*.wav episodes/.../tts_slow/*.wav`
   받아쓰기가 대사와 다르거나 영어 단어(감정 태그)가 들리면 그 문장 wav를 지우고 다시 build.
2. `hyperframes check` 통과, snapshot 프레임을 직접 열어 자막 잘림·캐릭터 겹침 확인.
3. 무료 한도(429)나 서버 혼잡(503)이 나면 기다렸다 재시도. 같은 요청을 무한 반복하지 않는다.

## episode.json 형식
```json
{
  "id": "2026-W45-01",
  "status": "script_approved",
  "publish_date": "2026-11-04",
  "topic": {"ko": "늦었을 때 사과하기", "en": "Apologizing for being late", "vi": "Xin lỗi khi đến muộn"},
  "scene": "cafe",
  "characters": [
    {"id": "jisu", "name": "지수", "side": "left", "color": "#d64b72", "voice": "Kore",
     "gender": "female", "skin": "light", "hair_style": "f_long", "hair_color": "#3b2a22", "earrings": true,
     "outfit": {"type": "knit", "color": "#efe2cc", "shade": "#c9b796"}},
    {"id": "minho", "name": "민호", "side": "right", "color": "#3f6fd1", "voice": "Charon",
     "gender": "male", "skin": "medium", "hair_style": "m_sidepart", "hair_color": "#1d1715",
     "outfit": {"type": "shirt", "color": "#3a5a8c", "shade": "#243a5e"}}
  ],
  "lines": [
    {"speaker": "jisu", "ko": "...", "en": "...", "vi": "...", "emotion": "a little sulky",
     "expr": {"jisu": {"brow": "sulky", "mouth": "pout"}, "minho": {"brow": "worried", "mouth": "worried"}}}
  ],
  "props": [{"type": "flowers", "line": 1, "at": 2.0, "give_line": 2, "give_at": 1.6}],
  "youtube": {"en": {"title": "...", "description": "..."}, "vi": {"title": "...", "description": "..."}},
  "tiktok_vi": {"caption": "..."},
  "uploads": {}
}
```
- 캐릭터 선택지(`studio/characters.py`)
  - hair_style: `f_long`, `f_bob`, `f_bun`, `m_short`, `m_sidepart`, `m_older`
  - outfit.type: `knit`, `shirt`, `blazer`, `apron`, `hoodie` / `glasses`, `earrings` / skin: `light`, `medium`, `tan`
  - 표정: brow `neutral|sulky|worried|raised`, mouth `neutral|smile|pout|o|worried` (말할 때 입 모양은 자동)
- 목소리(Gemini 기본 음성): 여 `Kore`(기본), 남 `Charon`(기본). 대화에 맞게 다른 음성도 가능.
- 장면(`studio/scenes.py`): 현재 `cafe`. 새 장면이 필요하면 같은 방식(뒤 배경 흐림 + 앞 전경)으로 추가.
- 대화에 맞게 매번 다른 인물(나이·옷·머리)을 구성한다.

## 업로드 절차 (승인 후)
1. `gh release create <id> project_en/renders/*.mp4 project_vi/renders/*.mp4 --repo immitance-stack/korean-shorts` 로 공개 주소를 만든다(파일 이름은 `<id>_en.mp4`, `<id>_vi.mp4`로 바꿔서).
2. Zapier YouTube `upload_video`로 en, vi를 각각 올린다. 제목·설명은 episode.json의 값. 언어 코드: en / vi, 오디오 언어 ko.
   YouTube 설명 끝에 AI 음성·일러스트 사용 사실을 한 줄 적는다.
3. vi 영상 파일과 `tiktok_vi.caption`을 사용자에게 보내 TikTok에 직접 올리도록 안내한다.
4. 링크를 `uploads`에 기록, `status: "uploaded"`, 커밋·푸시.

## 비용 원칙
무료 위주. Gemini TTS 무료 한도, Zapier 무료(월 100회 작업, 업로드 1번에 약 2회), HyperFrames(오픈소스)만 사용.
유료가 필요한 일이 생기면 먼저 사용자에게 묻는다.
