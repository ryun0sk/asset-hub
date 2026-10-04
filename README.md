# Asset Hub

企業・投資テーマの調査レポート、評価モデル、根拠資料をまとめる作業拠点です。2026年9月5日にCodexの既存タスクから移行しました。今後の資料作成・更新はこのリポジトリに集約します。

## 調査の入口

| 対象 | 最新の調査日 | 内容（最新版） | アーカイブ（過去の調査） |
|---|---|---|---|
| AI関連銘柄 ビジネスモデルの強さと目標達成の条件 | 2026-10-04 | [評価レポート（22銘柄の採点・15か月で2倍の条件、推奨ではない）](research/themes/ai-business-quality/2026-10-04/report.md) · [調査範囲・前提](research/themes/ai-business-quality/2026-10-04/README.md) | — |
| AI関連銘柄 年末までの比較材料 | 2026-10-03 | [比較レポート（日本12・海外10銘柄、推奨ではない）](research/themes/ai-year-end-comparison/2026-10-03/report.md) · [許容損失別の組み合わせ一覧](research/themes/ai-year-end-comparison/2026-10-03/screen.md) · [調査範囲・前提](research/themes/ai-year-end-comparison/2026-10-03/README.md) | — |
| キオクシア（285A） | 2026-10-03 | [投資判断レポート](research/companies/285A-kioxia/2026-10-03/report.md) · [株価の変動要因](research/companies/285A-kioxia/2026-10-03/stock-drivers.md) · [評価モデル](research/companies/285A-kioxia/2026-10-03/valuation.mjs) · [資料・引き継ぎ](research/companies/285A-kioxia/2026-10-03/README.md) | [2026-09-05](research/companies/285A-kioxia/2026-09-05/report.md) |
| AI関連銘柄・サプライチェーン | 2026-10-03 | [調達の流れ・機能整理・43社の株価・PER・EPS比較](research/themes/ai-supply-chain/2026-10-03/index.html) · [工程別レポート（前回からの変化・考察）](research/themes/ai-supply-chain/2026-10-03/report.md) · [調査範囲・出典方針](research/themes/ai-supply-chain/2026-10-03/README.md) | [2026-09-05](research/themes/ai-supply-chain/2026-09-05/README.md) |
| 光半導体・光インターコネクト | 2026-10-03 | [考察レポート](research/themes/photonics/2026-10-03/report.md) · [株価比較チャート](research/themes/photonics/2026-10-03/index.html) · [説明・再現方法](research/themes/photonics/2026-10-03/README.md) | [2026-09-05](research/themes/photonics/2026-09-05/README.md) |
| アドバンテスト（6857） | 2026-10-03 | [株価の変動要因](research/companies/6857-advantest/2026-10-03/stock-drivers.md) · [調査の前提・資料](research/companies/6857-advantest/2026-10-03/README.md) | — |
| イビデン（4062） | 2026-10-03 | [株価の変動要因](research/companies/4062-ibiden/2026-10-03/stock-drivers.md) · [調査の前提・資料](research/companies/4062-ibiden/2026-10-03/README.md) | — |
| セイワホールディングス（523A） | 2026-09-05 | [決算資料・調査素材](research/companies/523A-seiwa/2026-09-05/README.md) | — |

すべて調査日時点のスナップショットです。記載の株価・予想・投資判断は各調査日の見解で、現在の判断ではありません。2026-10-03版はキオクシア・AIサプライチェーン・光半導体を最新情報で再調査し、各レポート冒頭に「前回からの変化」を置いています。2026-09-05版は移行時のまま変更していません。

## アーカイブ（過去の調査）の扱い

- 再調査は新しい日付フォルダに作り、古い日付フォルダは**アーカイブとしてそのまま残す**。ダッシュボードは対象ごとに最も新しい日付を最新版として左メニューとホームに出し、過去の版は資料上部の「調査の版」とホームの「アーカイブ」欄から開ける。URL（`#r/<slug>-<日付>/…`）は版ごとに固定で、新しい版が増えても変わらない。
- アーカイブの全ファイル（`working/`・`qa/` を除く）のサイズとSHA-256を [research/archive-manifest.json](research/archive-manifest.json) に記録し、CIで改変・削除・追加を検出する。

```sh
python3 scripts/archive_snapshots.py --check    # アーカイブが記録どおりか確認
python3 scripts/archive_snapshots.py --restore  # 変更・削除されたファイルをGit履歴から記録どおりに戻す
python3 scripts/archive_snapshots.py --write    # 新しくアーカイブになった版を記録（既存の記録は書き換えない）
```

新しい版を追加したら、`python3 scripts/build_catalog.py` と `python3 scripts/archive_snapshots.py --write` を実行してcommitする。

## ダッシュボードアプリ

上の調査を左タブから閲覧できるWebアプリです。全資産の週次推移は「保有・推移」タブ1つにまとめ、チェックボックスでグラフに出す資産クラス・銘柄を選べます。デザインは pathosion-ops に準拠し、Cloud Run + IAP（許可したGoogleアカウントのみ）で公開します。最下部の「コスト」タブで、このシステムのGCP利用料金（BigQuery請求エクスポート由来）を確認できます。

資産の残高は Git には入れません。週末に `/weekly-assets` スキル（[.claude/skills/weekly-assets/SKILL.md](.claude/skills/weekly-assets/SKILL.md)）の手順で `data/private/assets/`（Git 対象外）に記録し、`python3 -m backend.assets build` → `push` で非公開バケットへ反映します。仕組みとスキーマは [docs/assets.md](docs/assets.md)。

| 対象 | 内容 |
|---|---|
| [web/](web/) | 画面（素のHTML/CSS/JS、ビルド不要） |
| [backend/](backend/) | 配信サーバー・IAP検証・コスト集計（Python標準ライブラリ） |
| [infra/](infra/) | デプロイ設定・スクリプト |
| [docs/design-system.md](docs/design-system.md) | デザインシステム（トークン・コンポーネント） |
| [docs/deploy.md](docs/deploy.md) | デプロイ・コスト集計の手順 |
| [docs/assets.md](docs/assets.md) | 資産スナップショットのスキーマ・CLI・週次運用 |
| [.claude/skills/weekly-assets/SKILL.md](.claude/skills/weekly-assets/SKILL.md) | 週末に資産を記録する手順（Claude 用スキル） |
| [research/catalog.json](research/catalog.json) | 左タブの一覧（全版）。調査を追加したら `python3 scripts/build_catalog.py` で再生成 |
| [research/archive-manifest.json](research/archive-manifest.json) | アーカイブの改変検出・復元用のハッシュ記録 |

ローカル確認: `python3 -m backend.server --port 4330` → http://localhost:4330

## 整理ルール

```text
research/
  companies/<証券コード-企業名>/<調査日>/
    report.md          調査結果
    valuation.mjs      再現可能な計算モデル（ある場合）
    sources/           保存済みの原資料
    working/           抽出テキスト・取得補助・検証画像
  themes/<テーマ名>/<調査日>/
    index.html         閲覧用の成果物（ある場合）
  crypto/<ティッカー-銘柄名>/<調査日>/   仮想通貨の調査（例 BTC-bitcoin。ダッシュボードでは「仮想通貨」に表示）
migrations/            移行元・移行先・ファイルのハッシュ記録
```

新しい調査は新しい日付フォルダに置き、この一覧の最新版を差し替えて古い版をアーカイブ欄へ移します。元資料と自分の予測・計算を分け、価格の基準日・通貨・株式分割基準を明記します。`working/` と `qa/` はローカルの補助資料として保存し、Gitの対象外にしています。

## 計算を再現する

Node.jsが利用できる環境で、リポジトリのルートから実行します。

```sh
node research/companies/285A-kioxia/2026-10-03/valuation.mjs   # 最新版（分割後基準）
node research/companies/285A-kioxia/2026-09-05/valuation.mjs   # アーカイブ（分割前基準）
```

このモデルは外部API・追加パッケージを使わず、計算結果を標準出力に出します。

## 移行メモ

レポート・モデル・HTML・PDF・補助資料の計34ファイル（約10.2 MiB）を移動し、全ファイルのSHA-256一致を確認しました。レポートのモデル参照だけ、移動後に同じフォルダの相対リンクへ変更しました。[移行記録](migrations/2026-09-05-codex-import.json)

旧タスク内の主要4ファイルのパスにはシンボリックリンクを残しており、内容の正本はこのリポジトリにあります。Gitのcommit・pushや資料の外部公開は行っていません。保存された他社資料を外部公開する場合は、公開範囲・利用条件を別途確認してください。
