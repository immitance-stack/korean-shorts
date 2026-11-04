#!/bin/bash
# Cloudflare Workers AI(FLUX.2 dev)로 1080x1920 세로 사진 1장을 만든다.
# 사용법: bash studio/cf_image.sh OUT.png "PROMPT" [기준사진1 기준사진2 ...]
# 기준 사진은 세로 1024px 이하로 줄여서 넣는다(자동). 얼굴만 자른 사진보다 장면 전체가 잘 된다.
set -e
OUT=$1; PROMPT=$2; shift 2
: "${CF_ACCOUNT_ID:?CF_ACCOUNT_ID 필요}" "${CF_API_TOKEN:?CF_API_TOKEN 필요}"
# 계정이 하나 더 있으면(CF_ACCOUNT_ID_2, CF_API_TOKEN_2) 첫 계정의 하루 무료 한도(code 4006)가 찼을 때 그 계정으로 넘어간다.
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
args=(); i=0
for r in "$@"; do
  ffmpeg -v error -y -i "$r" -vf "scale='min(1024,iw)':'min(1024,ih)':force_original_aspect_ratio=decrease" "$TMP/ref$i.jpg"
  args+=(-F "input_image_$i=@$TMP/ref$i.jpg"); i=$((i+1))
done
accts=("$CF_ACCOUNT_ID|$CF_API_TOKEN")
[ -n "${CF_ACCOUNT_ID_2:-}" ] && [ -n "${CF_API_TOKEN_2:-}" ] && accts+=("$CF_ACCOUNT_ID_2|$CF_API_TOKEN_2")
for a in "${accts[@]}"; do
  code=$(curl -sS -o "$TMP/resp.json" -w "%{http_code}" -X POST \
    "https://api.cloudflare.com/client/v4/accounts/${a%%|*}/ai/run/@cf/black-forest-labs/flux-2-dev" \
    -H "Authorization: Bearer ${a#*|}" -F "prompt=$PROMPT" "${args[@]}" -F width=1080 -F height=1920 -F steps=28)
  [ "$code" != "429" ] && break
  echo "계정 한도 소진(429), 다음 계정으로 시도" >&2
done
python3 - "$TMP/resp.json" "$TMP/img.jpg" "$code" <<'PY'
import json, base64, sys
d = json.load(open(sys.argv[1]))
img = (d.get("result") or {}).get("image")
if not img:
    sys.exit(f"실패 (HTTP {sys.argv[3]}): {d.get('errors')}")
open(sys.argv[2], "wb").write(base64.b64decode(img))
PY
ffmpeg -v error -y -i "$TMP/img.jpg" "$OUT"
echo "saved $OUT"
