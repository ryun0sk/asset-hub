# Tesla（TSLA）の日次株価履歴｜取得・検証記録

2026年10月5日（日本時間）取得。対象は **2025年10月3日〜2026年10月2日の米国通常取引終値、USD、251取引日**。10月5日の取引中価格・時間外価格は取り込まない。予想値・補間値ではなく、Yahoo Finance が提供する実測の日次価格スナップショットである。

- [チャート用 JSON](price-history.json)：`rows: [{date, close}]`。日付は America/New_York、価格は USD/株、小数第2位。
- [確認・ダウンロード用 CSV](price-history.csv)：`date,close,currency,symbol`。
- 正規化・検査スクリプト：`../normalize_price_history.py`（ローカル用）。保存済み原文からの再生成用。自動更新・ネットワーク取得は行わない。

## 取得元と方法

Python 標準ライブラリ `urllib.request` による公開 API の GET。API キー・認証・有料データ・個人の口座データは使っていない。以下の資料はすべて2026年10月5日に取得・確認した。

1. [Yahoo Finance Chart API](https://query1.finance.yahoo.com/v8/finance/chart/TSLA?period1=1759449600&period2=1791072000&interval=1d&events=div,splits)：`interval=1d`、`indicators.quote[0].close` を採用。`period1` は2025年10月3日 UTC、`period2` は2026年10月4日 UTCで、実際の最終行は10月2日。取得原文は Git 対象外の `../working/raw/yahoo-chart-TSLA.json` に保存。JSON の `fetchedAt` は原文保存時刻（UTC）。API の浮動小数点誤差を価格桁数 `priceHint=2` に合わせて丸めた。
2. [Tesla IR・IPO価格決定](https://ir.tesla.com/press-release/tesla-announces-pricing-initial-public-offering)（2010年6月発表）、[Tesla IR・投資家FAQ](https://ir.tesla.com/node/16)：上場ティッカー TSLA、Nasdaq、初回取引日2010年6月29日を照合。API メタデータも会社名 `Tesla, Inc.`、証券区分 `EQUITY`、取引所 `NasdaqGS`、初回取引日2010年6月29日と一致した。
3. [Nasdaq・2025年取引カレンダー](https://www.nasdaqtrader.com/content/technicalsupport/2025tradingcalendar.pdf)、[Nasdaq・2026年取引カレンダー](https://www.nasdaq.com/market-activity/stock-market-holiday-schedule)：期間内の休場・短縮取引日を確認。2025年11月・12月の休場と短縮取引は [Nasdaq Trader Alert（2025年11月12日）](https://m.nasdaqtrader.com/TraderNews.aspx?id=ETA2025-92) と [Nasdaq Trader Alert（2025年12月12日）](https://www.nasdaqtrader.com/TraderNews.aspx?id=ETA2025-99) でも確認した。
4. [Nasdaq Dorsey Wright・TSLA](https://dorseywright.nasdaq.com/chart/performance/symbol/TSLA)：2026年10月2日までの表示で終値 **370.59ドル**を照合した。Yahoo の HTML 履歴・銘柄ページは HTTP 429 等で取得できなかったため、同社の公開チャート API を使った。

全251行を別ベンダーの日次価格表と照合したものではない。全行には以下の内部整合・取引日検査を行い、最終終値を上記の別系列表示と照合した。

## 検証結果と価格の定義

- 261平日のうち下表の10休場日を除く251取引日と完全一致。欠落・重複・NULL は0件。休日に価格を補間していない。
- 全251行で始値・終値が日中高安の範囲内、価格は正、出来高は非負。全行を検査した。
- `close` は通常取引の終値。取得時点の `regularMarketPrice` や時間外の `fulldayPrice` を時系列に混ぜていない。API メタデータは10月5日の取引中価格を含むが、採用した日次配列は10月2日までに固定した。
- タイムスタンプから `America/New_York` で取引日へ変換し、米国夏時間・標準時間の切り替えを適用した。日本のカレンダー日や固定の UTC オフセットで日付を振っていない。通常取引は原則9:30〜16:00 ET。2025年11月28日・12月24日は13:00 ETの短縮取引日の終値を含む。
- 全行で `close` と `adjclose` が一致し、取得期間内の分割・配当イベントは空。今回の表示は配当再投資を含む総収益ではない。
- [2020年の1対5分割](https://ir.tesla.com/press-release/tesla-announces-five-one-stock-split)（2020年8月31日から分割後取引）、[2022年の1対3分割](https://ir.tesla.com/press-release/tesla-announces-three-one-stock-split)（2022年8月25日から分割後取引）は取得期間より前。今回の価格は両分割後の実際の通常終値で、独自に5や3で割る二重調整を加えない。
- 最初の終値は2025年10月3日 **429.83ドル**、最終は2026年10月2日 **370.59ドル**。期間内の最高終値は2025年12月16日 **489.88ドル**、最低終値は2026年7月29日 **298.32ドル**。日中高安・APIメタデータの52週高安とは区別する。
- 最大の前日比上昇は2026年6月29日約8.46%、最大下落は7月23日約14.52%。急変を欠損として扱わず、取得値をそのまま残した。

| 期間内の除外日 | 休場理由 |
|---|---|
| 2025-11-27 | Thanksgiving Day |
| 2025-12-25 | Christmas Day |
| 2026-01-01 | New Year's Day |
| 2026-01-19 | Martin Luther King, Jr. Day |
| 2026-02-16 | Presidents Day |
| 2026-04-03 | Good Friday |
| 2026-05-25 | Memorial Day |
| 2026-06-19 | Juneteenth |
| 2026-07-03 | Independence Day の振替休場 |
| 2026-09-07 | Labor Day |

## 再現方法

原文を保持したローカル環境で、リポジトリルートから以下を実行する。公開済み JSON/CSV は保存したスナップショットで、自動更新されない。

```sh
python3 research/companies/TSLA-tesla/2026-10-05/normalize_price_history.py
```
