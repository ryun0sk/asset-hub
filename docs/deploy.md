# 非公開ダッシュボードのデプロイ（Cloud Run + IAP）

Asset Hub の調査資料を、許可したGoogleアカウントだけが閲覧できるWebダッシュボードとして Cloud Run に置く手順です。構成は pathosion-ops と同じで、読み取り専用（GET/HEADのみ）のPythonサーバーを IAP の背後で動かします。

## 構成

| 要素 | 内容 |
|---|---|
| Cloud Run サービス `asset-hub` | `python -m backend.server`。`web/`・`backend/`・`research/`（`working/`・`qa/`・隠しファイル・`.py`/`.cjs` を除く）をイメージに同梱。256Mi、最小0・最大1インスタンス |
| IAP | `--iap` と `--no-allow-unauthenticated` で有効化。閲覧者は `infra/config.json` の `allowed_emails` のみ |
| GCS `<project>-asset-state` | 費用スナップショット `costs/state.json` と資産スナップショット `assets/state.json`（[docs/assets.md](assets.md)）だけを置く非公開バケット。ダッシュボードが読むのはこの2オブジェクトのみ |
| GCS `<project>-asset-builds` | Cloud Build のソース置き場 |
| Cloud Run Job `asset-cost-sync` | 課金エクスポート（BigQuery）からこのプロジェクト分だけを集計し `costs/state.json` に保存 |
| Cloud Scheduler `asset-cost-sync` | 上記ジョブを毎日 01:00（Asia/Tokyo）に起動。`cost_reporting.schedule` で変更可 |

サービスアカウント:

- `asset-runtime`: ダッシュボード本体。stateバケットの読み取りのみ。BigQuery・請求先アカウントの権限は持たない
- `asset-builder`: Cloud Build 用。builds バケット読み取り、Artifact Registry 書き込み、ログ書き込み
- `asset-cost-sync`: 費用ジョブ用。課金エクスポートのデータセット読み取り、`bigquery.jobUser`、`costs/state.json` のみ書き込み（IAM条件付き）
- `asset-scheduler`: Cloud Scheduler がジョブを起動するためだけの ID

## アクセス制限の仕組み

1. Cloud Run は `--no-allow-unauthenticated`。`run.invoker` は IAP のサービスエージェントにだけ付与します。`allUsers`・`allAuthenticatedUsers` は付けません（`verify` で確認）。
2. IAP のアクセス権 `roles/iap.httpsResourceAccessor` は `allowed_emails` から毎回全置換で設定します（手で追加した閲覧者は次回デプロイで消えます）。
3. アプリ自身も全リクエストで IAP の署名付きJWT（`X-Goog-IAP-JWT-Assertion`）を検証します。ES256・発行者 `https://cloud.google.com/iap`・audience `/projects/<番号>/locations/<region>/services/asset-hub`・有効期間・メールアドレスの許可リストを確認し、どれか1つでも失敗すれば 403 です。IAP を誤って外しても中身は返りません。
4. HTTP からの書き込み口はありません（POST等は 405）。`research/` 配下は拡張子の許可リストに一致し、`working/`・`qa/`・`.` で始まるパスを含まないファイルだけを返します。
5. ローカル実行時は `127.0.0.1` にだけバインドし、Host が `localhost`/`127.0.0.1` 以外なら 403 です。

## 0. 事前準備（手作業）

1. Google Cloud プロジェクトを新規作成し、請求先アカウントをリンクする。
2. `gcloud auth login` で、プロジェクトのオーナー権限を持つアカウントにログインする。
3. `infra/config.json` の `TBD` をすべて埋める。`TBD` が残っている、または `allowed_emails` が空の間は `deploy.py` と `setup_costs.py --apply` は何も実行せずに停止します。

| キー | 値 |
|---|---|
| `project` / `project_number` | プロジェクトID／プロジェクト番号（`gcloud projects describe <ID> --format='value(projectNumber)'`） |
| `account` | gcloud でログインしているアカウント（誤ったアカウントでの操作を防ぐため全コマンドに付与） |
| `allowed_emails` | 閲覧を許可するGoogleアカウント |
| `cost_reporting.billing_table` | 課金エクスポートのテーブル `<project>.<dataset>.gcp_billing_export_v1_<請求先ID>`。まだ用意しない場合は空文字 `""`（費用表示は「未設定」になります） |
| `cost_control.billing_account` | 予算アラートを作るときの請求先アカウントID（任意） |

## 1. 課金データの BigQuery エクスポート（コンソールで手作業）

費用表示を使う場合のみ必要です。

1. 課金エクスポートは**請求先アカウント単位**です。同じ請求先アカウントで既に「標準の使用料金」エクスポートが有効なら（例: 別プロジェクトのダッシュボード用）、新しく作らずそのテーブルを `billing_table` に指定してください。クエリは `project.id` でこのプロジェクト分だけに絞ります。
2. 未設定なら: コンソール「お支払い → 課金データのエクスポート → BigQuery エクスポート」で「標準の使用料金」を有効化し、保存先データセット（例: `billing_export`、ロケーション `US`）を作成・指定する。
3. `cost_reporting.location` をデータセットのロケーションに合わせる。
4. 初回データが届くまで数時間〜1日かかります。テーブル作成前に設定したい場合は `allow_pending_export: true` にすると、請求先アカウントとデータセットの状態を確認したうえで待機状態として設定します。
5. データセットが別プロジェクトにある場合、`setup_costs.py --apply` を実行するアカウントにそのデータセットのアクセス権を変更する権限が必要です。

## 2. 初期構築

```sh
python3 infra/deploy.py bootstrap
```

API有効化（Cloud Run / Artifact Registry / Cloud Build / IAP / Storage / IAM）、サービスアカウント、バケット、Artifact Registry、IAPサービスエージェントを作成します。既存のものは作り直しません。

## 3. デプロイ

```sh
python3 infra/setup_costs.py          # 費用ジョブの計画（dry-run。gcloud コマンドを表示するだけ）
python3 infra/deploy.py deploy
```

`deploy` は次を順に行います。

1. 許可リストのファイルだけを一時フォルダへ集めて Cloud Build でイメージを作成（`research/` は約68MB）
2. `setup_costs.py --apply`（費用ジョブ・スケジューラ・権限。`billing_table` が空なら既存ジョブを停止）
3. Cloud Run へ IAP 付き・非公開でデプロイし、IAP の閲覧者を `allowed_emails` に置き換え

オプション: `--existing-image`（ビルドを省略）、`--skip-costs`（費用ジョブを触らない）。

資料を追加・更新したら、カタログ生成のあとに `deploy` を再実行すると反映されます（資料はイメージに同梱）。

> ローカルの Python に `requests` などが無い場合は `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt` を実行し、`.venv/bin/python infra/deploy.py ...` で実行します。資産スナップショットの `python3 -m backend.assets push` も `requests` を使うため、同じく `.venv/bin/python -m backend.assets push` で実行します（`validate`・`build`・`template` は `python3` のままで動きます）。

### 個人（組織なし）プロジェクトでの IAP 用 OAuth クライアント（初回のみ・手作業）

組織に属さない Gmail アカウントのプロジェクトでは、IAP が Google 管理の OAuth クライアントを使えず「Empty Google Account OAuth client ID(s)/secret(s).」になります。2026-10-03 に次の手順で設定済みです。

1. Google Auth Platform で同意画面を作成（アプリ名 Asset Hub、対象「外部」・テスト中、テストユーザーに閲覧者のメールを追加）。
2. OAuth クライアント（ウェブアプリケーション）を作成し、承認済みリダイレクト URI に `https://iap.googleapis.com/v1/oauth/clientIds/<クライアントID>:handleRedirect` を追加。
3. `bash infra/set_iap_oauth.sh <クライアントID>` を実行し、シークレットを非表示入力で登録（ファイルには保存しない）。

閲覧者を増やすときは `allowed_emails` に加え、同意画面のテストユーザーにも追加してください。

## 4. 確認

```sh
python3 infra/deploy.py verify
```

IAP が有効か、閲覧者が `allowed_emails` と一致するか、公開の invoker がないかを確認し、URLを表示します。ブラウザで URL を開き、許可したアカウントでログインできること、別アカウントでは拒否されることも確認してください。

## 5. 費用ジョブ

- `python3 infra/setup_costs.py`（既定は dry-run）で実行予定のコマンドを確認し、`--apply` で反映します。
- ジョブは BigQuery の `maximumBytesBilled` を 100MB に制限し、日本時間の当月を含む6か月分を日次・サービス別に集計します。
- 直近1時間以内に成功している場合は再クエリしません。失敗時は前回のスナップショットを残し、状態を `error` にします。
- 手動実行: `gcloud run jobs execute asset-cost-sync --region=asia-northeast1 --project=<ID> --wait`
- 頻度の変更: `cost_reporting.schedule`（cron 形式）を変えて `setup_costs.py --apply`。
- 費用表示をやめる: `billing_table` を `""` にして `setup_costs.py --apply`（スケジューラを一時停止し、ジョブからテーブル設定を外します）。
- 予算アラート（任意・初回のみ手動）: dry-run の最後に表示される `gcloud billing budgets create ...` を実行します（月500円、50%/80%/100%）。再実行すると重複するため自動化していません。

## ローカル実行

```sh
python3 -m backend.server --port 4330   # http://localhost:4330/
python3 -m unittest discover -s tests
```

ローカルでは IAP 検証を行わず、費用は `data/private/costs.json`（`ASSET_COST_LOCAL_PATH` で変更可、Git 対象外）を、資産は `data/private/assets/state.json`（`python3 -m backend.assets build` の出力。`ASSET_ASSETS_DIR` / `ASSET_ASSETS_LOCAL_PATH` で変更可、Git 対象外）を読みます。Cloud Run では同じ内容を state バケットの `costs/state.json` と `assets/state.json` から読みます。

## 環境変数（Cloud Run に deploy.py が設定）

| 変数 | 用途 |
|---|---|
| `ASSET_IAP_AUDIENCE` | IAP JWT の audience |
| `ASSET_ALLOWED_EMAILS` | 閲覧を許可するメール（カンマ区切り） |
| `ASSET_STATE_BUCKET` | `costs/state.json`・`assets/state.json` を置くバケット（`backend.assets push` の既定の書き込み先でもある） |
| `ASSET_PROJECT_ID` | 費用を絞り込むプロジェクトID |
| `ASSET_COST_CURRENCY` / `ASSET_COST_PROJECT_BUDGET` | 予算表示（JPY / 500） |
| `ASSET_COST_BILLING_TABLE` / `ASSET_COST_BILLING_LOCATION` | 費用ジョブのみ。課金エクスポートのテーブルとロケーション |
| `ASSET_COST_LOCAL_PATH` | ローカル実行時の費用ファイル（既定 `data/private/costs.json`） |
| `ASSET_ASSETS_DIR` | ローカル・CLI のみ。資産ソース（`accounts.json`・`snapshots/`）の置き場（既定 `data/private/assets`） |
| `ASSET_ASSETS_LOCAL_PATH` | ローカル・CLI のみ。`build` の出力とローカルサーバーの読み取り先（既定 `<ASSET_ASSETS_DIR>/state.json`） |
| `ASSET_ASSETS_MIRROR` | CLI のみ・任意。`build` が資産ソースと state を複製するフォルダ（例: iCloud 配下） |
