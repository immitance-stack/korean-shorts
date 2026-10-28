# 한국어 학습 쇼츠 제작 — 작업 설명서

이 저장소는 한국어 선생님(사용자)이 준 짧은 대화 대본으로 학습용 쇼츠를 만들어 올리는 시스템이다.
매 세션은 이 문서의 절차를 따른다. 사용자는 컴퓨터에 익숙하지 않으므로 **쉬운 한국어로, 단계별로** 안내한다.
시간은 항상 **한국 시간(KST)** 으로 말한다.

## 영상 형식
- 9:16 세로(1080×1920), 길이는 대화에 따라 30~60초.
- 구성: 인트로(주제) → ① 대화 듣기(보통 속도) → "천천히 한 번 더 / 따라 말해 보세요" 카드 → ② 천천히 한 번 더(문장 사이 쉼) → 끝.
- 언어 버전 2개: `en`(한국어+영어 자막), `vi`(한국어+베트남어 자막). 그림·음성은 같고 자막만 다르다.
- 그림체: **실사풍 AI 사진**(`"style": "photo"`). 편마다 사진 3장 — ① 두 사람이 함께 나온 장면, ② 남자 클로즈업, ③ 여자 클로즈업. 대사마다 해당 사진을 천천히 확대하며 보여 준다.
  (예전 일러스트 방식 `characters.py`·`scenes.py`는 예비로 남겨 둠)
- 다음 화 예고 없음. 매 편이 독립된 대화.

## 업로드 대상
| 플랫폼 | 버전 | 방법 |
|---|---|---|
| YouTube | en, vi 둘 다 (**한 채널**에 같은 날 2편) | Zapier `upload_video` (영상 파일은 GitHub Release의 공개 주소로 전달) |
| TikTok | vi | 사용자가 직접 업로드. 영상 파일 + 설명/해시태그를 SendUserFile로 전달 |
| Instagram 릴스 | — | 사용하지 않음 |

**사용자가 승인하기 전에는 절대 업로드하지 않는다.** 승인은 매번 받는다.

## 주간 흐름
1. **월·화요일 – 대본 받기 (사용자가 같은 대화에 대본을 붙여넣음)**
   - 대본: 여자와 남자가 2번 정도 주고받는 대화.
   - 그 상황의 **앞뒤 이야기를 조금 덧붙여 3~4편**으로 나눈다. 각 편은 4~6문장, 자연스러운 구어체, 학습자 수준에 맞는 표현.
   - 편마다 `episodes/<YYYY-Www>/<NN>/episode.json`을 만든다(아래 형식). 번역은 **DeepL**(`translate-text`, EN-US·VI)로 하고, 베트남어 호칭(anh/em, chị/em, bạn 등)은 관계에 맞게 다듬는다.
   - **베트남어는 사용자가 읽지 못한다.** 그래서 베트남어 문장마다 DeepL로 **한국어 역번역**(VI→KO)을 해서 `vi_back_ko`에 적고, 원문과 뜻이 다르면 고친다.
     호칭: 존댓말(해요체) 대화는 기본 `tôi`(저)·`chúng ta`(우리)·`anh/chị`(상대) 를 쓴다. `anh/em`처럼 '나/너'가 헷갈리는 표현은 역번역으로 꼭 확인.
   - 편별 줄거리·대사·영어·**베트남어 역번역(한국어)**을 표로 보여 주고 **대본 승인**을 받는다. 승인되면 `status: "script_approved"`, 업로드 예정일(`publish_date`, 다음 날부터 하루 1편)을 적고 커밋·푸시한다.
2. **화~토요일 – 매일 제작 (루틴 `trig_01TUd5wvgp6Xct7f8pbXaQiN`이 매일 16:43 KST에 같은 대화로 작업을 보낸다)**
   - `status == "script_approved"`이고 `publish_date`가 오늘 이전인 편 중 가장 이른 것 1편을 만든다. 없으면 아무것도 하지 않고 끝낸다.
   - 제작 → 검사 → 사용자에게 영상 2개(en, vi)와 YouTube 제목·설명, TikTok 설명을 보내고 **승인 요청**. `status: "awaiting_approval"`.
   - 사용자가 "승인" → 업로드(아래) → `status: "uploaded"`, 링크 기록 → 커밋·푸시.
   - "수정: ..." → 고쳐서 다시 보여 준다.

## 사진 만들기 (ElevenLabs, 실사풍)
- ElevenLabs 무료 요금제: **하루 이미지 3장까지**(편당 3장 = 하루 1편). 장당 2K 세로 약 612 크레딧. 한도(429 `free_tier_image_limit_reached`)에 걸리면 다음 날 다시 한다.
- 순서
  1. `creative_generate_image`(model `gemini-3.1-flash-image`, `estimate_only: true`)로 ① 두 사람 장면 노드를 만들고 `creative_update_node`로 `{"aspect_ratio":"9:16","resolution":"2K"}` 설정 → `creative_run_flow_nodes`(generations_count 1).
  2. ②③은 `connect_from: [①노드]`로 같은 인물을 기준 삼아 같은 방법으로 만든다(프롬프트에 "Using the reference image ... same man/woman").
  3. `creative_get_flow_run_status`의 `content_url`(2시간 유효)을 curl로 받아 `episodes/<주>/<NN>/shotA.png`, `shotB.png`, `shotC.png`로 저장.
- 프롬프트 요령: "A photorealistic film still, vertical 9:16" + 인물(나이·머리·옷) + 장소·시간 + 얼굴은 화면 가운데(아래 30%는 자막 카드가 가림) + "Shot on 35mm/85mm lens, natural skin texture, subtle film grain. No text, no watermark."
- episode.json의 각 대사에 `"shot": "shotA.png"` 지정. 사진이 1장뿐이면 `"focus": {"x":0.66,"y":0.47,"zoom":1.9}`로 얼굴 확대(가상 클로즈업).

## 제작 명령
```bash
cd studio
python3 build.py ../episodes/<주>/<NN>/episode.json        # en, vi 두 프로젝트 생성 (TTS 자동 생성·캐시)
cd ../episodes/<주>/<NN>/project_en
HYPERFRAMES_SKIP_SKILLS=1 npx -y hyperframes@0.8.191 check     # 오류 0개여야 함
HYPERFRAMES_SKIP_SKILLS=1 npx -y hyperframes@0.8.191 snapshot --at 3,8,15   # 프레임을 직접 보고 확인
HYPERFRAMES_SKIP_SKILLS=1 npx -y hyperframes@0.8.191 render    # renders/*.mp4
# 렌더 결과(약 48MB)를 업로드·전송용으로 압축(약 15MB):
ffmpeg -i renders/X.mp4 -c:v libx264 -crf 21 -preset medium -pix_fmt yuv420p -c:a aac -b:a 160k -movflags +faststart /home/user/<id>_<lang>.mp4
```
- AI 사진에 대본과 다른 글자(이름표 등)가 보이면 ffmpeg `drawbox`로 지운다.
- 같은 주의 2편부터는 1편 ① 사진 노드를 `connect_from`으로 써서 같은 얼굴을 유지한다(1편 episode.json의 `elevenlabs` 기록 참고). 기준 사진을 쓰면 장당 약 918 크레딧.
- 필요 환경: `GOOGLE_API_KEY`(환경 변수), ffmpeg, Node 22, Chromium(클라우드 기본 설치). 폰트·GSAP은 저장소에 포함(외부 CDN은 렌더러에서 막힘).
- 음성: Gemini `gemini-3.8-flash-tts`, 문장마다 따로 생성. **음성에는 한국어만 들어가야 한다**(사용자 요구). 사용자는 감정 지시가 있는 쪽을 더 좋아한다.
  그래서 `make_line`이 ① 지시 없는 기본 음성(`l*.plain.wav`)을 먼저 만들고 ② 영어 감정 태그(`[concerned]`)를 넣은 음성을 만든 뒤,
  기본보다 20%+0.2초 넘게 길거나 `has_english`가 YES/판단 실패면 버리고 다시(최대 3번), 끝까지 실패하면 기본 음성을 쓴다.
  속도 지시("slowly")는 절대 넣지 않는다.
- **감정 지시는 그 순간의 감정만이 아니라 인물의 상태·상황까지 함께 적는다.** (사용자 피드백)
  예: 아픈 사람이 고마워할 때 `[grateful]`만 쓰면 너무 밝아서 꾀병처럼 들린다 → `[grateful but weak and tired, sounding sick]`.
  대본 승인 표에 대사별 감정 지시를 한국어로 함께 보여 주고, 장면 전체 분위기와 어울리는지 확인한다.
- 느린 구간은 보통 음성을 음높이 그대로 0.75배속(`SLOW_TEMPO`)으로 늘려 만든다(TTS 추가 호출 없음).
- 보통 음성의 말 속도가 초당 3음절 미만이면 다른 말이 섞인 것으로 보고 자동으로 다시 만든다(`make_line`).
- 음량은 문장마다 -18dB로 자동 통일.

### 제작 후 검사 (반드시)
1. `python3 studio/transcribe.py episodes/.../tts_normal/*.wav episodes/.../project_en/voice.mp3 episodes/.../project_en/slow.mp3`
   영어가 들리면 ⚠ 표시와 함께 실패(exit 1). 대사와 다르면 그 문장 wav를 지우고 다시 build.
2. `hyperframes check` 통과, snapshot 프레임을 직접 열어 자막 잘림·캐릭터 겹침 확인.
3. 무료 한도(429)나 서버 혼잡(503)이 나면 기다렸다 재시도. 같은 요청을 무한 반복하지 않는다.
   - Gemini 무료 한도는 하루 단위(태평양 시간 자정 = 한국 시간 오후 4~5시 초기화). 그래서 매일 제작은 16:43 KST.
   - 받아쓰기·영어 검사도 같은 무료 한도를 쓴다. 한도가 차서 검사를 못 하면, 길이가 의심스러운(기본 음성보다 긴) 감정 음성은 기본 음성으로 바꾸고 사용자에게 그 사실을 알린다.
4. 받아쓰기 결과가 대사와 다르거나 실행할 때마다 다르게 나오면, 음성 중간에 엉뚱한 소리가 섞였을 수 있다. 그 문장 wav를 지우고 다시 생성한다.

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
1. `bash studio/media_branch.sh put <id> <en.mp4> <vi.mp4>` 로 공개 주소 2개를 만든다.
   (이 세션에서는 GitHub 릴리스 생성·브랜치 삭제가 막혀 있어 `media` 브랜치를 덮어쓰는 방식을 쓴다.)
2. Zapier YouTube `upload_video`(tool_name `youtube_upload_video`, 기본 연결 = 사용자의 채널 "TongTong Korean School")로 en, vi를 각각 올린다.
   - `video`: 1번의 주소 / `title`·`description`: episode.json의 값 / `privacy_status`: `public`
   - `category_id`: `27`(Education) / `default_language`: `en` 또는 `vi` / `default_audio_language`: `ko`
   - `made_for_kids`: `false` / `tags`: Korean, Learn Korean, Korean conversation 등
   - 설명 끝에 AI 음성·일러스트 사용 사실을 한 줄 적는다.
3. `bash studio/media_branch.sh clear` 로 공개 영상을 비운다.
4. vi 영상 파일과 `tiktok_vi.caption`을 사용자에게 보내 TikTok에 직접 올리도록 안내한다.
5. 링크를 `uploads`에 기록, `status: "uploaded"`, 커밋·푸시.

## 비용 원칙
무료 위주. Gemini TTS 무료 한도, Zapier 무료(월 100회 작업, 업로드 1번에 약 2회), HyperFrames(오픈소스)만 사용.
유료가 필요한 일이 생기면 먼저 사용자에게 묻는다.
