---
name: weekly-assets
description: 週末の資産スナップショット記録。ユーザーが各サイトにログインして画面を出し、Claude がスクリーンショットから残高を読み取って data/private/assets/snapshots/ に記録し、検証・build・GCS への push まで行う。「今週の資産を記録」「資産を更新」「週次更新」で使う。
---

# 週次の資産スナップショット記録

目的: 各口座の評価額を銘柄・商品単位で `data/private/assets/snapshots/YYYY-MM-DD.json` に記録し、ダッシュボードの「保有・推移」タブ（全資産を1ページに表示）に反映する。スキーマと検証ルールは `docs/assets.md`。

## 前提と禁止事項（必ず守る）

- ログインはユーザーが自分で行う。Claude はブラウザの read 階層（スクリーンショット）で数値を読むだけ。資格情報・口座番号・URL の入力、ページ内のクリック、取引・振替は一切しない。
- 残高の数値を書く場所は `data/private/assets/` 配下だけ。リポジトリ内の md、`working/`、メモリ、スクリーンショットの保存は禁止。会話内での読み合わせは可。
- 為替換算はしない。各サイトが表示する円換算評価額をそのまま `valueJpy` に入れる。円表示が無い口座（Binance 等）だけ、ユーザーが読み上げたレートで換算し `notes` にレートを残す。
- 推定値で埋めない。読めない口座はその行を `valueJpy: null` のまま残さず、ユーザーに確認して値を得るか、行を削除して `notes` に理由を書く。
- `git commit` / `push` / デプロイは、ユーザーが明示的に依頼したときだけ。

## 手順

1. 記録日を決める（原則その週の土曜または日曜。`YYYY-MM-DD`）。
2. 雛形を作る。前回スナップショットの銘柄構成が値 `null` で複写される（未上場株 `private` クラスだけは前回値を引き継ぎ `carryForward: true`）。
   ```bash
   python3 -m backend.assets template --date YYYY-MM-DD
   ```
3. `data/private/assets/accounts.json` の `accounts` を順に回る。各口座について `readGuide` をユーザーに伝え、該当画面を表示してもらい、スクリーンショットから次を転記する。
   - 銘柄・商品ごとに `valueJpy`（整数円）。あれば `quantity`、`costJpy`（取得金額）、`nativeAmount`/`currency`。
   - 新しい銘柄は行を追加（`account`, `class`, `symbol`, `name`, 任意で `market`）。売却済みは行を削除し `notes` に「YYYY-MM-DD 売却: 銘柄名」を残す。
   - 証券口座の預り金・MRF、取引所の日本円残高は `class: "cash"` の別行。投資信託・ETF は `class: "fund"`。
   - 口座ごとに行の合計をサイト表示の合計と照合し、`notes` に「<口座> サイト表示合計 ¥X と一致」を残す。一致しないときは原因を確認してから進む。
4. 検証する。エラーはメッセージの指す項目を直す。警告（平日の日付など）は内容を伝えて続行可。
   ```bash
   python3 -m backend.assets validate
   ```
5. ローカルの state を生成する（`data/private/assets/state.json`。`ASSET_ASSETS_MIRROR` が設定されていれば複製も行われる）。
   ```bash
   python3 -m backend.assets build
   ```
6. ローカルで確認する。`.claude/launch.json` の `asset-hub` を `preview_start` で起動し、`#a/all`（保有・推移）の総資産・最終記録日・各資産クラスの内訳、`/api/assets` の `latestDate` が今回の日付になっていることを見る。
7. GCS へ push する（Cloud Run のダッシュボードが読む。`requests` が必要なので venv の python を使う）。
   ```bash
   .venv/bin/python -m backend.assets push
   ```
   出力の `latestDate` が今回の日付であることを確認し、ユーザーに結果を報告する。Cloud Run 側の表示確認はユーザーがブラウザでログインして行う。

## 完了報告に含めること

- 記録日、口座ごとの照合結果、追加・削除した銘柄、残した警告。
- `build` と `push` の出力（`latestDate`、スナップショット数）。
- 数値そのものは会話で読み合わせた範囲にとどめ、要約文に総資産額を書く必要はない。
