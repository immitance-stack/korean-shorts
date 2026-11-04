"""Gemini API 키 목록. GOOGLE_API_KEY가 하루 무료 한도(429)에 걸리면 GOOGLE_API_KEY_2(다른 계정)로 넘어가려고 쓴다."""
import os
KEYS = [k for k in (os.environ.get("GOOGLE_API_KEY"), os.environ.get("GOOGLE_API_KEY_2")) if k]
