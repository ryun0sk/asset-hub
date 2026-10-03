#!/usr/bin/env bash
# IAP に独自 OAuth クライアントを登録する（組織に属さない個人プロジェクトで必要）。
# 対象は infra/config.json の project / account / region / service。
# シークレットは画面に表示せず入力させ、一時ファイルは終了時に削除する。リポジトリには保存しない。
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
CLIENT_ID=${1:?usage: infra/set_iap_oauth.sh <OAuth client ID>}
CONFIG_VALUES=$(python3 -c '
import json, sys
c = json.load(open(sys.argv[1]))
print(c["project"], c["account"], c["region"], c["service"])' "$ROOT/infra/config.json" 2>/dev/null) || {
  echo "infra/config.json を読み込めません（project / account / region / service を確認してください）" >&2; exit 1; }
read -r PROJECT ACCOUNT REGION SERVICE <<<"$CONFIG_VALUES"
for value in "$PROJECT" "$ACCOUNT" "$REGION" "$SERVICE"; do
  [ -n "$value" ] && [ "$value" != TBD ] || { echo "infra/config.json を確定させてから実行してください" >&2; exit 1; }
done

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
echo "IAP の OAuth クライアントを設定しました: $CLIENT_ID ($PROJECT/$SERVICE)"
