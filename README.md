# Asset Hub

企業・投資テーマの調査レポート、評価モデル、根拠資料をまとめる作業拠点です。2026年9月5日にCodexの既存タスクから移行しました。今後の資料作成・更新はこのリポジトリに集約します。

## 調査の入口

| 対象 | 調査日 | 内容 |
|---|---|---|
| AI関連銘柄・サプライチェーン | 2026-09-05 | [AI時代の機能整理・調達の流れ・43社の株価・PER・EPS比較](research/themes/ai-supply-chain/2026-09-05/index.html) · [工程別の日本・海外企業比較／キオクシアの競合](research/themes/ai-supply-chain/2026-09-05/report.md) · [調査範囲・出典方針](research/themes/ai-supply-chain/2026-09-05/README.md) |
| キオクシア（285A） | 2026-09-05 | [投資判断レポート](research/companies/285A-kioxia/2026-09-05/report.md) · [評価モデル](research/companies/285A-kioxia/2026-09-05/valuation.mjs) · [資料・引き継ぎ](research/companies/285A-kioxia/2026-09-05/README.md) |
| 光半導体・光インターコネクト | 2026-09-05 | [株価比較チャート](research/themes/photonics/2026-09-05/index.html) · [説明・編集元](research/themes/photonics/2026-09-05/README.md) |
| セイワホールディングス（523A） | 2026-09-05 | [決算資料・調査素材](research/companies/523A-seiwa/2026-09-05/README.md) |

すべて調査日時点のスナップショットです。既存資料の移行に伴う株価の再取得や投資判断の更新は行っていません。新規調査の範囲は各フォルダのREADMEに記載しています。

## ダッシュボードアプリ

上の調査を左タブから閲覧できるWebアプリです。デザインは pathosion-ops に準拠し、Cloud Run + IAP（許可したGoogleアカウントのみ）で公開します。最下部の「コスト」タブで、このシステムのGCP利用料金（BigQuery請求エクスポート由来）を確認できます。

| 対象 | 内容 |
|---|---|
| [web/](web/) | 画面（素のHTML/CSS/JS、ビルド不要） |
| [backend/](backend/) | 配信サーバー・IAP検証・コスト集計（Python標準ライブラリ） |
| [infra/](infra/) | デプロイ設定・スクリプト |
| [docs/design-system.md](docs/design-system.md) | デザインシステム（トークン・コンポーネント） |
| [docs/deploy.md](docs/deploy.md) | デプロイ・コスト集計の手順 |
| [research/catalog.json](research/catalog.json) | 左タブの一覧。調査を追加したら `python3 scripts/build_catalog.py` で再生成 |

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
migrations/            移行元・移行先・ファイルのハッシュ記録
```

新しい調査は新しい日付フォルダに置き、この一覧に追記します。元資料と自分の予測・計算を分け、価格の基準日・通貨・株式分割基準を明記します。`working/` と `qa/` はローカルの補助資料として保存し、Gitの対象外にしています。

## 計算を再現する

Node.jsが利用できる環境で、リポジトリのルートから実行します。

```sh
node research/companies/285A-kioxia/2026-09-05/valuation.mjs
```

このモデルは外部API・追加パッケージを使わず、計算結果を標準出力に出します。

## 移行メモ

レポート・モデル・HTML・PDF・補助資料の計34ファイル（約10.2 MiB）を移動し、全ファイルのSHA-256一致を確認しました。レポートのモデル参照だけ、移動後に同じフォルダの相対リンクへ変更しました。[移行記録](migrations/2026-09-05-codex-import.json)

旧タスク内の主要4ファイルのパスにはシンボリックリンクを残しており、内容の正本はこのリポジトリにあります。Gitのcommit・pushや資料の外部公開は行っていません。保存された他社資料を外部公開する場合は、公開範囲・利用条件を別途確認してください。
