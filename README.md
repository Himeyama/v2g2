# Gemini Gateway

Gemini Developer API 互換の HTTP Gateway。Vertex AI Gemini に転送する。

## セットアップ

```bash
uv sync
```

## 設定

```bash
export GOOGLE_CLOUD_PROJECT=my-project
export GOOGLE_CLOUD_LOCATION=asia-northeast1
```

ADC 認証:

```bash
gcloud auth application-default login
```

## 起動（開発）

```bash
uv run uvicorn gateway.main:app --host 0.0.0.0 --port 12080
```

## テスト

```bash
uv run pytest
```

## systemd インストール

```bash
# ユーザー作成
sudo useradd -r -s /sbin/nologin gemini

# アプリ配置
sudo cp -r . /opt/gemini-gateway
sudo chown -R gemini:gemini /opt/gemini-gateway
cd /opt/gemini-gateway && sudo -u gemini uv sync

# 環境変数ファイル
sudo mkdir -p /etc/gemini-gateway
sudo tee /etc/gemini-gateway/env <<EOF
GOOGLE_CLOUD_PROJECT=my-project
GOOGLE_CLOUD_LOCATION=asia-northeast1
EOF

# ADC キーファイルを使う場合
# echo "GOOGLE_APPLICATION_CREDENTIALS=/opt/gemini/key.json" | sudo tee -a /etc/gemini-gateway/env

# サービス登録
sudo cp systemd/gemini-gateway.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now gemini-gateway
```

## 動作確認

```bash
curl -X POST http://localhost:12080/v1beta/models/gemini-2.5-flash:generateContent \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}'
```

## Gemini CLI から使う

### 方法 1: 環境変数

```bash
export GOOGLE_GEMINI_BASE_URL=http://localhost:12080
export GEMINI_API_KEY=dummy
export GEMINI_MODEL=gemini-2.5-flash
gemini
```

`GEMINI_API_KEY` は Gateway 側で認証していないため任意の値でよい。

### 方法 2: settings.json に固定する

`~/.gemini/settings.json` を編集：

```json
{
  "baseUrl": "http://localhost:12080",
  "model": {
    "name": "gemini-2.5-flash"
  },
  "security": {
    "auth": {
      "selectedType": "gemini-api-key"
    }
  }
}
```

設定後はそのまま起動するだけでよい：

```bash
GOOGLE_GEMINI_BASE_URL=http://localhost:12080 GEMINI_API_KEY=dummy gemini --model gemini-2.5-flash
```

モデルを切り替えたい場合は `--model` フラグで上書きできる：

```bash
gemini --model gemini-2.5-pro
```

---

## エンドポイント

| Method | Path | 説明 |
|--------|------|------|
| GET | /v1beta/models | モデル一覧 |
| POST | /v1beta/models/{model}:generateContent | テキスト生成 |
| POST | /v1beta/models/{model}:streamGenerateContent | ストリーミング生成 |
| POST | /v1beta/cachedContents | キャッシュ作成 |
| GET | /v1beta/cachedContents | キャッシュ一覧 |
| GET | /v1beta/cachedContents/{name} | キャッシュ取得 |
| PATCH | /v1beta/cachedContents/{name} | キャッシュ更新 |
| DELETE | /v1beta/cachedContents/{name} | キャッシュ削除 |
