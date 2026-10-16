# SpaceX（SPCX）の日次株価履歴｜取得・検証記録

2026年10月5日（日本時間）取得。対象は **2026年6月12日〜10月2日の米国通常取引終値、USD、78取引日**。10月5日以降の取引中価格は取り込まない。予想値・補間値ではなく、Yahoo Finance が提供する実測の日次価格スナップショットである。

- [チャート用 JSON](price-history.json)：`rows: [{date, close}]`。日付は America/New_York、価格は USD/株、小数第2位。
- [確認・ダウンロード用 CSV](price-history.csv)：`date,close,currency,symbol`。
- [正規化・検査スクリプト](../normalize_price_history.py)：保存済み原文からの再生成用。自動更新・ネットワーク取得は行わない。

## 取得元と方法

Python 標準ライブラリ `urllib.request` による公開 API の GET。API キー・認証・有料データ・個人の口座データは使っていない。

1. [Yahoo Finance Chart API](https://query1.finance.yahoo.com/v8/finance/chart/SPCX?period1=1781222400&period2=1791072000&interval=1d&events=div,splits)：`interval=1d`、`indicators.quote[0].close` を採用。`period1` は6月12日 UTC、`period2` は10月4日 UTCで、実際の最終行は10月2日。取得原文は Git 対象外の `../working/raw/yahoo-chart-SPCX.json` に保存。JSON の `fetchedAt` は原文保存時刻（UTC）。API の浮動小数点誤差を価格桁数 `priceHint=2` に合わせて丸めた。
2. [Nasdaq の SPCX 履歴ページ](https://www.nasdaq.com/market-activity/stocks/spcx/historical)：見出しは Space Exploration Technologies Corp. Class A Common Stock。価格表は静的取得時に表示されなかったため、日次価格の出所には使っていない。
3. [Nasdaq 2026年取引カレンダー](https://www.nasdaq.com/market-activity/stock-market-holiday-schedule)：期間内の6月19日、7月3日、9月7日の休場を確認。

Yahoo の HTML 履歴ページは HTTP 429 等で取得できなかったため、同社の公開チャート API を使った。Nasdaq の価格 API は補助照合に利用できず、全78行を別ベンダーの日次表と照合したものではない。10月2日終値158.96ドルは今回のレポートで確認済みの市場データと一致する。

## 検証結果と価格の定義

- API メタデータの会社名は `Space Exploration Technologies Corp.`、証券区分は `EQUITY`、取引所は `NasdaqGS`、初回取引日は2026年6月12日。以前の SPCX ETF の履歴は含めていない。
- 81平日のうち上記3休場日を除く78取引日と完全一致。欠落・重複・NULL は0件。休日に価格を補間していない。
- 全78行で始値・終値が日中高安の範囲内、価格は正、出来高は非負。全行を検査した。
- `close` は通常取引の終値。時間外の `fulldayPrice` や取得時点の `regularMarketPrice` を時系列に混ぜていない。全行の `adjclose` と一致し、取得期間内の分割・配当イベントは空。5月の1対5分割は上場前のため、取得期間の株価に独自の分割調整を加えない。
- 最初の終値は6月12日 **160.95ドル**、最終は10月2日 **158.96ドル**。期間内の最高終値は **211.39ドル**、最低終値は **108.27ドル**。日中高安とは区別する。
- 最大の前日比上昇は6月15日約19.60%、最大下落は6月22日約16.43%。急変を欠損として扱わず、取得値をそのまま残す。

Starlink は SpaceX 内の事業で独立した上場株式ではない。Starlink ページからこの系列を使う場合は、**親会社 SpaceX（SPCX）の参考株価**と明示し、Starlink 単独の株価とは表示しない。
