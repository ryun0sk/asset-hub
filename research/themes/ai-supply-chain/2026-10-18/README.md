# AI関連銘柄・サプライチェーン｜2026-10-18

- [46社の株価・EPS・PERと18工程の比較](index.html)
- [今回の追加と数値の読み方](report.md)
- [基準日・出所を含む表示データ](valuation.json) · [株価](prices.json) · [EPS入力](fundamentals.json)
- [7銘柄の実績月次比較](../../ai-actual-valuation/2026-10-18/report.md)
- [前回の43社版](../2026-10-03/README.md) · [全調査の一覧](../../../../README.md)

## 今回の追加

ユーザーの依頼で三菱重工（7011.T）、GE Vernova（GEV）、Siemens Energy（ENR.DE）を追加した。新しい「発電・ガスタービン」工程から3社の株価・PER・EPSを比較できる。掲載企業は43社から46社、工程は17から18。

既存43社の株価・実績EPS・予想は2026-10-03版の保存値をそのまま引き継ぎ、更新していない。追加3社だけ2026-10-16終値まで取得した。各行に株価基準日を示す。旧データの空白期間を新しい価格で埋めていない。既存43社との値動き比較は全社の価格が存在する共通終了日までで計算する。

## EPSとPER

- 三菱重工はJPY、GE VernovaはUSD、Siemens EnergyはEUR。株価とEPSを同じ現地通貨・普通株1株・株式分割基準で計算し、円換算しない。
- 追加3社は公式決算の希薄化後EPSを保存。累計EPSの差引または四半期EPSの合算によるTTM概算であり、株数変化・丸め・希薄化の扱いにより公式通期EPSと小差がある。公式通期値は別に表示する。
- 日次PERは、その日までに公表されているTTM EPSで日次終値を割る。公表時刻を確認し、発表前の価格に新しい利益を遡及適用しない。EPSが0以下・未取得ならPERは算出不能。
- 半年年換算は直近2四半期EPSの合計×2。将来予想ではない。
- 三菱重工の2027年3月期会社予想は基本EPS113.09円（2026-08-04公表）。実績の希薄化後EPSとは基準を区別する。海外2社は通期EPS会社予想を確認できず、外部予想も今回取得していないため欠損のまま表示する。
- GE Vernovaの実績には2025Q4の税便益約29億ドルと2026Q1のProlec再評価益約39.92億ドル（税前）が含まれる。実績PERの低さを本業利益の持続性と同一視しない。
- 既存43社の期末＋45日仮定、外部予想・為替換算等の前提は[前回README](../2026-10-03/README.md)を引き継ぐ。

## 出典

- [三菱重工の公式EPS・公表日・出所](../../../companies/7011-mitsubishi-heavy-industries/2026-10-18/README.md)
- [GE Vernovaの公式EPS・公表日・出所](../../../companies/GEV-ge-vernova/2026-10-18/README.md)
- [Siemens Energyの公式EPS・公表日・出所](../../../companies/ENR-siemens-energy/2026-10-18/README.md)
- 株価は認証不要のYahoo Finance chart endpoint。追加3社の取得URL・取得時刻・生データSHA-256は[addition-prices.json](addition-prices.json)に保存。生レスポンスはworking/prices/（Git対象外）。

## 再生成

```sh
python3 research/themes/ai-supply-chain/2026-10-18/build_additions.py
python3 research/themes/ai-supply-chain/2026-10-18/build_dashboard.py
```

既存保存値と公式EPS入力、addition-prices.jsonだけから再生成する。外部通信なし。価格を取り直す場合はfetch_additions.py（公開データの外部通信あり）を使うが、後日の再調査はさらに新しい日付フォルダを作る。旧フォルダのファイルは変更していない。X API・有料API・秘密情報・売買・commit・pushは使っていない。
