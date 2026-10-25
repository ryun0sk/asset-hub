# AI関連7銘柄 実績EPS・PERの推移｜2026-10-18

- [7社の比較と計算基準](report.md)
- [表示用JSON](valuation-history.json) · [CSV](valuation-history.csv)
- [追加3社の日次結合結果](addition-daily.json)
- [再生成方法と公式EPS出所](../../ai-supply-chain/2026-10-18/README.md)
- [前回4銘柄版](../2026-10-16/README.md) · [全調査の一覧](../../../../README.md)

既存のキオクシア・アドバンテスト・イビデン・ディスコの4銘柄と、イビデンの株式売却益除外推計は、2026-10-16保存版から同じ値で引き継いだ（株価は10月15日まで）。追加した三菱重工・GE Vernova・Siemens Energyは10月16日終値まで。株価の基準日と通貨を各行に示す。

追加3社は各市場の年初営業日、各月最終営業日、10月16日の終値に、その時点までの公表済み四半期EPSを結合した。TTMは直近4四半期合算、半年年換算は直近2四半期合算×2の概算。正式通期EPS・予想EPSとは区別する。

JSONの従来4社は円建ての既存フィールドをそのまま残し、追加3社はcurrencyと通貨中立のclose/ttmDilutedEPS/halfYearAnnualizedDilutedEPSを使う。画面は両形式を読み、海外株を円建てと表示しない。CSVは全7社を通貨中立列へ統一する。

GE Vernovaには税便益・Prolec再評価益が含まれ、半年年換算は特に一時利益を増幅する。各社の注記と出典を確認する。再生成はai-supply-chain/2026-10-18/build_additions.pyで実行。既存の過去フォルダは変更していない。
