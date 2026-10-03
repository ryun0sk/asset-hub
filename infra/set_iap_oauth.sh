#!/usr/bin/env bash
# IAP に独自 OAuth クライアントを登録する（組織に属さない個人プロジェクトで必要）。
# シークレットは画面に表示せず入力させ、一時ファイルは終了時に削除する。リポジトリには保存しない。
set -euo pipefail

PROJECT=ryun0sk-asset-hub
ACCOUNT=ryun0sk.takagishi@gmail.com
REGION=asia-northeast1
SERVICE=asset-hub
CLIENT_ID=${1:?usage: infra/set_iap_oauth.sh <OAuth client ID>}

read -r -s -p "OAuth クライアント シークレットを貼り付けて Enter: " CLIENT_SECRET
echo
[ -n "$CLIENT_SECRET" ] || { echo "シークレットが空です" >&2; exit 1; }

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
chmod 700 "$TMP"
cat > "$TMP/iap.yaml" <<EOF
access_settings:
  oauth_settings:
    client_id: "$CLIENT_ID"
    client_secret: "$CLIENT_SECRET"
EOF

gcloud iap settings set "$TMP/iap.yaml" --resource-type=cloud-run --service="$SERVICE" \
  --region="$REGION" --project="$PROJECT" --account="$ACCOUNT" --quiet >/dev/null
echo "IAP の OAuth クライアントを設定しました: $CLIENT_ID"
