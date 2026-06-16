#!/usr/bin/env bash
#
# cachedContents の動作確認スクリプト。
#
# ダミーテキストでキャッシュを作成し、それを参照して generateContent を呼び、
# レスポンスの usageMetadata.cachedContentTokenCount を確認することで
# 「実際にキャッシュが効いているか」を検証する。最後にキャッシュを削除する。
#
# 前提:
#   - ゲートウェイが起動済み (デフォルト http://localhost:12080)
#   - jq, curl がインストール済み
#
# 使い方:
#   ./tests/cache_smoke.sh
#   BASE_URL=http://localhost:8080 MODEL=models/gemini-2.5-flash ./tests/cache_smoke.sh

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:12080}"
MODEL="${MODEL:-models/gemini-2.5-flash}"
TTL="${TTL:-600s}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DUMMY_FILE="${DUMMY_FILE:-$SCRIPT_DIR/fixtures/cache_dummy.txt}"

command -v jq >/dev/null || { echo "jq が必要です" >&2; exit 1; }
[[ -f "$DUMMY_FILE" ]] || { echo "ダミーテキストが見つかりません: $DUMMY_FILE" >&2; exit 1; }

echo "==> ダミーテキスト: $DUMMY_FILE ($(wc -m < "$DUMMY_FILE" | tr -d ' ') 文字)"

# --- 1. キャッシュ作成 -------------------------------------------------------
# --rawfile でテキストを安全に JSON 文字列へ埋め込む。
create_payload=$(jq -n \
  --arg model "$MODEL" \
  --arg ttl "$TTL" \
  --rawfile text "$DUMMY_FILE" \
  '{
    model: $model,
    ttl: $ttl,
    displayName: "cache-smoke-test",
    contents: [ { role: "user", parts: [ { text: $text } ] } ]
  }')

echo "==> キャッシュを作成中..."
create_resp=$(curl -sS -X POST "$BASE_URL/v1beta/cachedContents" \
  -H "Content-Type: application/json" \
  -d "$create_payload")

cache_name=$(echo "$create_resp" | jq -r '.name // empty')
if [[ -z "$cache_name" ]]; then
  echo "キャッシュ作成に失敗しました:" >&2
  echo "$create_resp" | jq . >&2 || echo "$create_resp" >&2
  exit 1
fi

cached_tokens=$(echo "$create_resp" | jq -r '.usageMetadata.totalTokenCount // "?"')
echo "    name=$cache_name (totalTokenCount=$cached_tokens)"

# キャッシュ ID 部分を取り出す。Vertex はフルパス
# (projects/.../cachedContents/xxxx) を返すため、末尾セグメントを使う。
cache_id="${cache_name##*/}"

# スクリプト終了時に必ずキャッシュを削除。
cleanup() {
  echo "==> キャッシュを削除中: $cache_name"
  curl -sS -X DELETE "$BASE_URL/v1beta/cachedContents/$cache_id" >/dev/null || true
}
trap cleanup EXIT

# --- 2. キャッシュを参照して生成 -------------------------------------------
gen_payload=$(jq -n \
  --arg cache "$cache_name" \
  '{
    cachedContent: $cache,
    contents: [ { role: "user", parts: [ { text: "このテキストは何のために用意されたものか、一文で答えて。" } ] } ]
  }')

echo "==> キャッシュを参照して generateContent を呼び出し中..."
gen_resp=$(curl -sS -X POST "$BASE_URL/v1beta/$MODEL:generateContent" \
  -H "Content-Type: application/json" \
  -d "$gen_payload")

echo "--- レスポンス本文 ---"
echo "$gen_resp" | jq -r '.candidates[0].content.parts[0].text // "(本文なし)"'
echo "--- usageMetadata ---"
echo "$gen_resp" | jq '.usageMetadata'

# --- 3. キャッシュ命中を検証 ------------------------------------------------
cached_count=$(echo "$gen_resp" | jq -r '.usageMetadata.cachedContentTokenCount // 0')
if [[ "$cached_count" -gt 0 ]]; then
  echo "==> ✅ キャッシュ命中: cachedContentTokenCount=$cached_count"
else
  echo "==> ❌ キャッシュが効いていません (cachedContentTokenCount=0)" >&2
  exit 1
fi
