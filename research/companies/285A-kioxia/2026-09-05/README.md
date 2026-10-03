# キオクシア（285A）｜2026-09-05

- [投資判断レポート](report.md)
- [評価モデル](valuation.mjs)
- [全調査の一覧](../../../../README.md)

## 調査の前提と引き継ぎ

ユーザーの質問は「今、割安か／買うべきか」「NAND価格がどうなるかをファクトで調べてほしい」。保有期間の回答は「特に想定してない」。この版の結論は、2026年9月4日終値54,460円に対し、ほぼ適正〜やや割安だが新規購入は急がない、というもの。移行時点で内容は再評価していない。

独自モデルの基本評価は約58,000円。モデルのキャッシュフロー・割引率は仮定で、会社予想ではない。すべて2026年10月1日の1対3株式分割前の基準。更新時はこの分割に特に注意する。

Appleの「価格上限なしLTA」に関するCiti原本・個別契約条件は未確認。TrendForceの一部資料は公開要旨のみ。未確認情報を確定利益に加えない。X APIは300円上限の指示後に追加利用を停止し、既使用額は未確認。

## 保存済み原資料

| ローカル資料 | 内容・原典 |
|---|---|
| [q1-release-en.pdf](sources/q1-release-en.pdf) | 2026-07-31 決算短信英訳：[会社開示](https://ssl4.eir-parts.net/doc/285A/tdnet/2859908/00.pdf) |
| [q1-deck-script-en.pdf](sources/q1-deck-script-en.pdf) | 2026-07-31 決算説明・スクリプト：[会社開示](https://ssl4.eir-parts.net/doc/285A/ir_material_for_fiscal_ym4/209425/00.pdf) |
| [q1-qa-en.pdf](sources/q1-qa-en.pdf) | 2026-07-31 決算説明会Q&A：[会社開示](https://ssl4.eir-parts.net/doc/285A/ir_material_for_fiscal_ym4/209428/00.pdf) |
| [buyback-completion-en.pdf](sources/buyback-completion-en.pdf) | 2026-08-10 自社株取得完了：[会社開示](https://ssl4.eir-parts.net/doc/285A/tdnet/2870703/00.pdf) |
| [capex-en.pdf](sources/capex-en.pdf) | 2026-08-27 共同投資計画：[会社開示](https://ssl4.eir-parts.net/doc/285A/tdnet/2878650/00.pdf) |

オンラインで参照したその他の資料はレポート内の出典リンクを参照。全文をローカル保存していない資料もある。

## 計算と補助資料

このフォルダで `node valuation.mjs` を実行すると、株数、PER、価格ストレス、割引評価、感応度を再計算できる。外部通信はない。

`working/` に抽出テキスト、公開IRページの保存HTML・JavaScript、PDF表の確認画像を移した。保存JavaScriptは実行用モデルではない。補助資料はGit対象外で、ローカルに保持している。
