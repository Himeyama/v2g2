#!/usr/bin/env bash
#
# モデル一覧取得の動作確認スクリプト。
#
# ゲートウェイの GET /v1beta/models を叩き、Vertex AI から動的に取得した
# モデル一覧を表示する。nextPageToken が返る場合は全ページを辿る。
#
# 前提:
#   - ゲートウェイが起動済み (デフォルト http://localhost:12080)
#   - jq, curl がインストール済み
#
# 使い方:
#   ./tests/list_models.sh
#   BASE_URL=http://localhost:8080 PAGE_SIZE=50 ./tests/list_models.sh

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:12080}"
PAGE_SIZE="${PAGE_SIZE:-100}"

command -v jq >/dev/null || { echo "jq が必要です" >&2; exit 1; }
command -v curl >/dev/null || { echo "curl が必要です" >&2; exit 1; }

page_token=""
total=0

echo "==> モデル一覧を取得中... ($BASE_URL)"
while :; do
  url="$BASE_URL/v1beta/models?pageSize=$PAGE_SIZE"
  [[ -n "$page_token" ]] && url="$url&pageToken=$page_token"

  resp=$(curl -sS "$url")

  # エラーレスポンス (.error) を検知して中断する。
  if echo "$resp" | jq -e '.error' >/dev/null 2>&1; then
    echo "モデル一覧の取得に失敗しました:" >&2
    echo "$resp" | jq . >&2 || echo "$resp" >&2
    exit 1
  fi

  count=$(echo "$resp" | jq '.models | length')
  echo "$resp" | jq -r '.models[].name'
  total=$((total + count))

  page_token=$(echo "$resp" | jq -r '.nextPageToken // empty')
  [[ -z "$page_token" ]] && break
done

echo "==> 合計 $total 件"
