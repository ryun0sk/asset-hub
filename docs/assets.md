# 資産スナップショット（週次の全資産記録）

全資産（個別株・投資信託・仮想通貨・預金・未上場株）を**週末に1回、口座ごと・銘柄ごと**に記録し、ダッシュボードで推移を見るための仕組みです。残高は各サイトの画面表示をそのまま転記します（為替換算・推定は行いません）。

- 正本はローカルの `data/private/assets/`（Git 対象外）。`accounts.json`（口座マスタ）と `snapshots/YYYY-MM-DD.json`（週ごとの記録）。
- `python3 -m backend.assets build` が検証して `data/private/assets/state.json` を生成し、ローカルサーバーは `/api/assets` でそれを返します。
- `.venv/bin/python -m backend.assets push` が同じ state を非公開バケット `gs://<project>-asset-state/assets/state.json` に書き、Cloud Run はそれだけを読みます。Web サーバーは GET/HEAD のみで、ブラウザから書き込む経路はありません。
- 集計（クラス別・口座別・前週比）はフロントの純関数で行い、サーバーは生データをそのまま配信します（費用画面と同じ分担）。

例ファイルは二重に持たず、テスト用フィクスチャ [`tests/fixtures/assets/`](../tests/fixtures/assets/) を参照してください（口座構成は実際と同じ、数値はすべてダミー。各ファイルの `_note` が目印で、検証では未知キーとして無視されます）。

## ファイル配置

```
data/private/assets/            # git-ignored。ここ以外に残高を書かない
  accounts.json                 # 口座マスタ
  snapshots/2026-10-04.json     # 週ごとのスナップショット（ファイル名 = date）
  state.json                    # build の出力（ローカルサーバーが読む）
```

環境変数（すべて任意）:

| 変数 | 用途 | 既定 |
|---|---|---|
| `ASSET_ASSETS_DIR` | ソースの置き場（相対ならリポジトリルート基準） | `data/private/assets` |
| `ASSET_ASSETS_LOCAL_PATH` | ローカル state の出力先・サーバーの読み取り先 | `<ASSET_ASSETS_DIR>/state.json` |
| `ASSET_ASSETS_MIRROR` | 指定すると `build` が `accounts.json`・`snapshots/*.json`・`state.json` をこのフォルダへ複製する（例: iCloud 配下のバックアップ） | なし |
| `ASSET_STATE_BUCKET` | `push` 先バケット（`--bucket` が無いとき） | `infra/config.json` から `<project>-asset-state` |

## スキーマ

### `accounts.json`

```json
{"version": 1, "accounts": [
  {"id": "sbi-nisa", "institution": "SBI証券", "label": "SBI証券 NISA", "defaultClass": "stock", "currency": "JPY",
   "readGuide": "口座管理 > 保有証券の NISA 欄で銘柄・投資信託ごとの評価額と取得金額を読む"}
]}
```

| フィールド | 規則 |
|---|---|
| `id` | `^[a-z0-9][a-z0-9-]{1,39}$`、一意。スナップショットの `account` から参照する |
| `institution` / `label` | 空でない文字列。`label` は画面の表示名（同じ金融機関の口座を区別する） |
| `defaultClass` | 下の資産クラスのいずれか。`template` が初回の雛形に使う |
| `currency` | サイトの表示通貨。`^[A-Z]{3}$` |
| `readGuide` | 任意。「どの画面のどの数値を読むか」の文章。URL・ID・パスワードは書かない |

### `snapshots/YYYY-MM-DD.json`

```json
{"version": 1, "date": "2026-10-04", "recordedAt": "2026-10-04T10:05:00+09:00", "source": "screenshot",
 "positions": [
  {"account": "sbi-tokutei", "class": "stock", "market": "JP", "symbol": "285A", "name": "キオクシア",
   "quantity": 100, "valueJpy": 650000, "costJpy": 400000},
  {"account": "sbi-tokutei", "class": "stock", "market": "US", "symbol": "AAPL", "name": "Apple",
   "quantity": 10, "currency": "USD", "nativeAmount": 2345.67, "valueJpy": 350000, "costJpy": 300000},
  {"account": "bitflyer", "class": "crypto", "symbol": "BTC", "name": "ビットコイン", "quantity": 0.0123, "valueJpy": 210000},
  {"account": "mizuho", "class": "cash", "symbol": "JPY", "name": "普通預金", "valueJpy": 1234567},
  {"account": "private-equity", "class": "private", "symbol": "PRIVATE-A", "name": "A社への出資",
   "valueJpy": 1000000, "costJpy": 1000000, "carryForward": true}
 ],
 "notes": ["523A は売却"]}
```

資産クラス（`class`）: `stock` 個別株 / `fund` 投資信託・ETF / `crypto` 仮想通貨 / `cash` 現金・預金 / `private` 未上場株 / `bond` 債券 / `other` その他。
証券口座の預り金・MRF、取引所の日本円残高は `cash` として記録します。ETF は `fund`。

| フィールド | 規則 |
|---|---|
| `version` | `1` |
| `date` | `YYYY-MM-DD`。ファイル名と一致し、日本時間の今日より後は不可 |
| `recordedAt` | 任意。ISO 8601 の日時（画面を読んだ時刻） |
| `source` | 任意の文字列。通常 `"screenshot"` |
| `positions[].account` | `accounts.json` の `id` |
| `positions[].class` | 上の資産クラス |
| `positions[].market` | 任意。`JP` / `US` / `other` |
| `positions[].symbol` | `^[A-Za-z0-9._-]{1,32}$`。日本株は証券コード（`285A`）、米国株はティッカー、コインはシンボル、預金は通貨コード（`JPY`） |
| `positions[].name` | 画面上の名称（空不可） |
| `positions[].valueJpy` | **必須**。0 以上の整数（円）。サイト表示の円換算評価額。売却直後で 0 なら 0 と書く（`null` は不可） |
| `positions[].costJpy` | 任意。0 以上の整数（取得金額、円）。ある行だけ評価損益を表示する |
| `positions[].quantity` | 任意。0 より大きい数（株数・口数・コイン数量） |
| `positions[].currency` / `nativeAmount` | 任意。外貨建て表示の参考値（`^[A-Z0-9]{3,10}$` と有限の数値）。為替計算には使わない |
| `positions[].carryForward` | 任意の真偽値。`private` クラスだけで使える。前回値をそのまま引き継いだ印 |
| `notes` | 任意。文字列の配列（照合結果や売買のメモ） |

その他の検証規則:

- `(account, class, symbol)` の重複は不可。売却した銘柄は行ごと省く（0 で残しても良い）。
- 評価額の合計が 0 のスナップショットは不可。
- `date` が土日以外なら**警告のみ**（標準エラー出力）。処理は続行する。
- 未知のキーは無視され、state には含まれない。任意フィールドの `null` は「なし」として落とされる。
- `private` 以外のクラスで `carryForward` を付けるとエラー。毎週画面から読み取る前提。

### state 文書（`state.json` / GCS `assets/state.json`）

```json
{"state": {"version": 1, "builtAt": "...", "accounts": [...],
           "snapshots": [{"date": "2026-09-27", "recordedAt": "...", "positions": [...], "notes": [...]}, ...],
           "latestDate": "2026-10-04"},
 "pushedAt": "2026-10-04T01:00:00+00:00"}
```

スナップショットは日付昇順、同じ日付が2つあればエラー。ローカルの `build` では `pushedAt` は `null`、`push` が書く GCS 側には書き込み時刻が入ります。`/api/assets` は `{"state": ..., "status": {"status": "ok" | "not_configured", "pushedAt": ...}}` を返します。

## CLI

```sh
python3 -m backend.assets validate                    # accounts.json と snapshots/*.json を検証（警告は stderr）
python3 -m backend.assets template --date 2026-10-11  # 前回分を基に雛形を snapshots/<date>.json に作る（--force で上書き）
python3 -m backend.assets build                       # 検証して state.json を書く（ASSET_ASSETS_MIRROR があれば複製）
.venv/bin/python -m backend.assets push [--bucket B] [--account A]   # 検証・build 相当のうえ GCS へ書き込む
```

- 終了コード: 検証エラーは 1（メッセージはファイル名とフィールドを含む日本語）。成功時は1行の JSON（`{"assetsBuild": "ok", "latestDate": "...", "snapshots": 3}` など）。
- `template` は前回の positions を複写し、`valueJpy`・`quantity`・`nativeAmount` を `null` にします。`null` のままでは `validate` が通らないので「読まずに流用」はできません。`costJpy`・`currency`・`market` は引き継ぎます。`private` クラスの行だけは値を残して `carryForward: true` を付けます。前回分が無ければ口座ごとに1行の例（`defaultClass`）を出します。
- `push` のバケットは `--bucket` > `ASSET_STATE_BUCKET` > `infra/config.json`（`<project>-asset-state`）、アカウントは `--account` > `infra/config.json` の `account`。トークンは `gcloud auth print-access-token --account=<account>` で取り、`requests` を使うため `.venv/bin/python` で実行します（他の infra コマンドと同じ）。書き込みは GCS の generation 一致条件付きで、競合したら読み直して1回だけ再試行します。
- フィクスチャで動作確認: `ASSET_ASSETS_DIR=tests/fixtures/assets python3 -m backend.assets validate`。`build` もできますが、その場合は `ASSET_ASSETS_LOCAL_PATH` を一時ファイルに向けてください（フィクスチャフォルダに `state.json` を作らない）。

## 週次の流れ（概要）

実際の手順は Claude 用スキル [`.claude/skills/weekly-assets/SKILL.md`](../.claude/skills/weekly-assets/SKILL.md) に書いてあります（`/weekly-assets` で呼び出す）。

1. ユーザーが各サイトにログインして画面を出す。Claude はスクリーンショットを読むだけ（資格情報・URL の入力、クリックはしない。スクリーンショットは保存しない）。
2. `python3 -m backend.assets template --date <土日の日付>` で雛形を作る。
3. `accounts.json` の `readGuide` の順に口座ごとの画面を見せてもらい、銘柄ごとの `valueJpy`（必要なら `quantity`・`nativeAmount`）を転記する。新規取得は行を足し、売却は行を消す。
4. 口座合計をサイト表示の合計と照合し、差があれば `notes` に書く。
5. `validate` → `build` → ローカルの `#home` と `/api/assets` の `latestDate` を確認 → `.venv/bin/python -m backend.assets push`。
6. やらないこと: 為替換算、推定値での補完、過去スナップショットの書き換え、`commit`。

## プライバシー

- 残高は `data/private/`（`.gitignore` 済み）と非公開の state バケットにだけ置く。Git、Docker イメージ（`infra/deploy.py` のステージ対象は `backend/`・`web/`・`research/` の許可リストのみ）、デプロイ設定には入らない。`tests/test_deploy.py` が `data/private/assets/**` をステージしないことを確認している。
- `readGuide` や `notes` にログイン情報・URL・口座番号を書かない。
- `/api/assets` は IAP の検証を通ったリクエストにだけ返し、読み込み失敗時は内部エラー文を出さず `資産データを読み込めませんでした。` とだけ返す。
- `push` はユーザーの gcloud アカウントで行う。Cloud Run の実行用サービスアカウントは state バケットの読み取り権限しか持たない。

## サイズと将来の整理

1スナップショットは数 KB（15 行で約 3KB）。週次なら年 150〜300KB 程度で、state 全体を毎回配信しても問題ありません。保有行が増えて数年分で肥大化したら、`build` に「直近 N 週以外は月末のスナップショットだけ残す」オプションを足す余地があります（正本の `snapshots/*.json` は残し、配信する state だけ間引く）。
