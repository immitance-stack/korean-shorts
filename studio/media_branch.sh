#!/usr/bin/env bash
# 업로드용 영상을 공개 주소로 올리거나(put) 비운다(clear).
# GitHub 릴리스·브랜치 삭제는 이 클라우드 세션에서 막혀 있어서, `media` 브랜치를 매번 새 커밋으로 덮어쓴다(force-push).
#   put:   bash studio/media_branch.sh put <id> <en.mp4> <vi.mp4>   → 공개 주소 2개 출력
#   clear: bash studio/media_branch.sh clear                        → 업로드 후 영상 제거
set -euo pipefail
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REPO="immitance-stack/korean-shorts"
WT="$(mktemp -d)"
cleanup() { git -C "$REPO_DIR" worktree remove --force "$WT" 2>/dev/null || true; git -C "$REPO_DIR" branch -D media-tmp >/dev/null 2>&1 || true; }
trap cleanup EXIT

git -C "$REPO_DIR" branch -D media-tmp >/dev/null 2>&1 || true
git -C "$REPO_DIR" worktree add -q --orphan -b media-tmp "$WT"
echo "업로드용 임시 영상 보관 브랜치. 매 업로드마다 덮어씀." > "$WT/README.md"
if [ "$1" = "put" ]; then
  id="$2"
  cp "$3" "$WT/${id}_en.mp4"
  cp "$4" "$WT/${id}_vi.mp4"
fi
git -C "$WT" add -A
git -C "$WT" -c user.name="immitance-stack" -c user.email="immitance@gmail.com" commit -qm "media: ${1} ${2:-}"
git -C "$WT" push -q -f origin media-tmp:media 2>&1 | grep -v -E "negotiation|acknowledgments|^remote: *$" || true
if [ "$1" = "put" ]; then
  for lang in en vi; do
    url="https://raw.githubusercontent.com/${REPO}/media/${id}_${lang}.mp4"
    for i in 1 2 3 4 5 6; do
      code=$(curl -s -o /dev/null -w "%{http_code}" -I "$url")
      [ "$code" = "200" ] && break
      sleep 10
    done
    echo "$lang $url ($code)"
  done
fi
