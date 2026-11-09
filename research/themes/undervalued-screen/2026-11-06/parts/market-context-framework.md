# 市場バリュエーションの全体像（2026-11-06時点）と「割安かつ利益が持続する」銘柄の判定フレームワーク

基準日: 2026-11-06（金）。各データ点に取得時点を付記。実績・会社予想・外部予想・独自推定（「推定」と明記）を区別する。
重要な注記: 11/5（木）米国市場でAI関連株が急落（NASDAQ -5.5%、S&P500時価総額約3兆ドル減）、11/6（金）寄り付きで日経平均 -7%、韓国・台湾 -8%超（後に下げ幅縮小）。以下の指数PER・PBRの多くは10/29〜11/5終値ベースであり、11/6の実勢は概ね5〜7%低い水準にあると推定される（出所: [Reuters via Yahoo Finance 2026-11-06](https://finance.yahoo.com/markets/world-indices/articles/asia-stocks-drop-ai-rout-235808955.html)）。

---

## A1. 主要指数のバリュエーション水準と長期平均との比較

### Takeaway
米国は「予想PERは平均並み（18.7倍、10年平均19.1倍）だが、実績PER（25.9倍）とCAPE（38.8倍、長期平均17.5倍）は歴史的高水準」という、利益成長率30%超に支えられた相場。日本は予想PER15〜16倍・PBR1.5〜1.8倍で長期平均（予想PER約14倍）をやや上回る。欧州14倍、中国9倍、新興国10倍、韓国（半導体除く）10倍は長期平均並み〜割安。

### Cited Findings
**米国（S&P 500）**
- 予想12カ月PER 18.7倍（10/29終値7,720.39）。5年平均19.8倍、10年平均19.1倍を下回る。9/30の19.0倍から低下（株価+0.9%に対し予想EPS+2.5%） — [FactSet Earnings Insight 2026-10-30](https://advantage.factset.com/hubfs/Website/Resources%20Section/Research%20Desk/Earnings%20Insight/EarningsInsight_103026.pdf)
- 実績12カ月PER 25.9倍。5年平均24.4倍、10年平均23.7倍を上回る — [FactSet 2026-10-30](https://advantage.factset.com/hubfs/Website/Resources%20Section/Research%20Desk/Earnings%20Insight/EarningsInsight_103026.pdf)
- 実績PER 25.06倍（11/5終値、前日比-4.51%）。長期平均16.24倍、中央値15.08倍 — [multpl.com](https://www.multpl.com/s-p-500-pe-ratio)
- Shiller CAPE 38.79倍（11/5終値）。長期平均17.45倍、中央値16.14倍、最高44.19倍（1999年12月） — [multpl.com Shiller PE](https://www.multpl.com/shiller-pe)。8月時点のCAPEは41.2倍で「2000年以来の高さ」 — [thetrading.tools 2026-08-13](https://www.thetrading.tools/chart-of-the-day/2026-08-13-shiller-cape-highest-since-2000)
- JPMorgan Guide to the Markets: S&P500予想PER 19.0倍（9/30）、30年平均17.2倍 — [JPM GTM US](https://am.jpmorgan.com/content/dam/jpm-am-aem/global/en/insights/market-insights/guide-to-the-markets/mi-guide-to-the-markets-us.pdf)
- 均等加重S&P500の予想PER 16.0倍 vs 時価総額加重19.0倍（9月下旬データ） — [Citadel Securities "October: The Q4 Reload"](https://www.citadelsecurities.com/news-and-insights/global-market-intelligence/october-the-q4-reload/)。別推計では均等加重15.2倍（日付不明） — [Parallax Chicago](https://parallax.chicago.global/blog/equal-weight-sp-divergence-cta-unwind-factor-attribution)
- セクター別予想PER（10/29）: 最高は一般消費財23.8倍、生活必需品22.9倍、資本財22.8倍。最低はエネルギー13.2倍、金融14.9倍 — [FactSet 2026-10-30](https://advantage.factset.com/hubfs/Website/Resources%20Section/Research%20Desk/Earnings%20Insight/EarningsInsight_103026.pdf)

**日本（日経平均・TOPIX/プライム）**
- 日経平均（11/5）: 終値61,077.90円、予想PER 15.80倍、前期基準PER 19.37倍、PBR 1.80倍、予想配当利回り1.93% — [日経電子版 国内株式指標](https://www.nikkei.com/markets/kabu/japanidx/)
- 日経平均（11/4）: 加重平均PER 15.74倍、指数ベース19.49倍、加重PBR 1.78倍 — [日経平均プロフィル 日次サマリー](https://indexes.nikkei.co.jp/nkave/archives/summary)
- 東証プライム全銘柄（11/5）: 予想PER 15.55倍、前期基準18.86倍、PBR 1.67倍、予想配当利回り2.62%、予想株式益回り6.42%。スタンダード全銘柄: 予想PER 13.37倍、PBR 1.08倍。グロース全銘柄: 予想PER 33.53倍、PBR 3.43倍 — [日経電子版 国内株式指標](https://www.nikkei.com/markets/kabu/japanidx/)
- 東証プライム（10/30、いちよし経済研究所集計、予想は日経）: PER 17.4倍、PBR 1.8倍、配当利回り2.3%、ROE 9.5% — [いちよし経済研究所 TOPIXバリュエーション](https://www.ichiyoshi-research.co.jp/market/topix)
- TOPIX（プライム）PBR月次（JPX速報）: 2026年1月1.5→2月1.7→8月1.6→9月1.5→10月1.5倍。2025年10〜12月は1.4倍 — [stock-marketdata.com](https://stock-marketdata.com/pbr-1st2nd.html/)
- TOPIX予想PERの長期平均（2011年以降週次）は約14倍、2026年5月時点で約17倍 — [Asset Management One Japan Outlook 2026-06](https://www.am-one.co.jp/pdf/english/186/JapanOutlook_202606.pdf)
- 別サイトのTOPIX予想PER 14.75倍、PBR 1.34倍（11/5更新。他出所と乖離あり、算出基準不明） — [japanmarket.org](https://www.japanmarket.org/topix)
- 野村證券（夏時点）: 日経平均の予想PER 22.1倍はTOPIX（16.9倍）より高い（指数ベース算出） — [野村證券 2026年末見通し](https://www.nomura.co.jp/wealthstyle/article/0724/)

**欧州・新興国・中国・韓国**
- MSCI Europe（10/30）: 予想PER 14.08倍、実績PER 16.79倍、PBR 2.50倍、配当利回り2.86% — [MSCI Europe Index](https://www.msci.com/indexes/index/990500/msci-europe-index)
- MSCI China（10/30）: 予想PER 9.32倍、実績PER 11.96倍、PBR 1.29倍、配当利回り2.63% — [MSCI China Index](https://www.msci.com/indexes/index/302400/msci-china-index)。JPMorgan（8/31）: MSCI China予想PER 10.8倍 vs 20年平均11.4倍、PBR 1.5倍 vs 20年平均1.8倍 — [JPM Guide to Investing in Asia 2026-08-31](https://cdn.jpmorganfunds.com/content/dam/jpm-am-aem/global/en/insights/market-insights/mi-gtia.pdf)
- MSCI EM 予想PER 9.81倍（2026年9月） — [Siblis Research EM](https://siblisresearch.com/data/emerging-markets-valuations/)
- KOSPI（10/20、FnGuide集計）: 12カ月予想PER 4.41倍（10月初の5.43倍から低下）。半導体セクターは3倍未満。半導体除くKOSPIは10.3倍で、過去20年平均10.4倍を下回り、2026年高値14.5倍から大幅低下 — [Money Today 2026-10-20](https://www.mt.co.kr/index.php/en/stock/2026/10/20/2026102015013299958)
- KOSPI PBRは2026年4月23〜24日に2.07倍と過去最高（年初1.38倍）、ただし上場企業の約60%はPBR1倍未満 — [이투데이 2026-04](https://www.etoday.co.kr/news/view/2579169)
- 11/6: 韓国・台湾の指数は8%超下落、Samsung -10%、SK hynix -12%、Kioxia -14% — [Reuters via Yahoo 2026-11-06](https://finance.yahoo.com/markets/world-indices/articles/asia-stocks-drop-ai-rout-235808955.html)

### Inferences
- （推定）11/5の米株急落（S&P500 約-4.5%）を10/29基準の18.7倍に当てると、S&P500予想PERは約17.9倍、実績PERは約25倍、CAPEは38.8倍。「予想PERは平均以下」は、2026年+32.9%、2027年+16.3%という高い増益予想を前提にしており、AI投資の失速で予想EPSが切り下がれば平均以下ではなくなる。CAPE 38.8倍は1929年（32.6倍）超・1999年（44.2倍）未満。
- 日本は予想PER 15.5〜15.8倍で長期平均（約14倍）を約10%上回るが、実績PER 19倍との乖離（約20%の増益予想）と、11/6の-7%を考慮すると、実勢の予想PERは14.5〜15倍と推定され、ほぼ長期平均に戻る。PBR 1.5〜1.7倍はアベノミクス以降では高めだが、ROE 9.5%なら正当化範囲内。
- 国別の「割安度」順（予想PER）: 韓国（半導体除く10.3倍）≈ 中国9.3倍 ≈ EM 9.8倍 < 欧州14.1倍 < 日本15.5倍 < 米国18.7倍。ただし韓国4.4倍はピーク半導体利益で割ったもので、サイクル正常化が必須（B3参照）。

### Gaps
- JPX公式「規模別・業種別PER・PBR」ページはアクセス拒否（403）で、TOPIX公式の10〜20年中央値を直接取得できず。TOPIX長期平均は運用会社資料（AM One）に依拠。
- MSCI EMのPBR・配当利回り（10月末）、MSCI Japan/Koreaのページは取得失敗。KOSPIの10〜11月時点PBRは未取得。
- 11/6終値ベースの各国指数PER・PBRは本稿執筆時点で未公表。

---

## A2. バリュー vs グロースのスプレッドと「バリュー」の業種集中

### Takeaway
2026年はバリューがグロースを大幅にアウトパフォームしたが、バリュエーション格差はなお大きい（予想PERでグロースはバリューの約1.46〜1.48倍、PBRでは2.7倍）。日本ではグロース/バリュー相対株価が長期平均を下回り、小型バリューが最も強い。バリューは米国ではエネルギー・金融、日本では銀行・商社・自動車・公益・鉄鋼・証券・海運に集中。

### Cited Findings
- Russell 1000 Growth: 実績PER 33.53倍、予想PER 23.61倍、CAPE 53.89倍。Russell 1000 Value: 実績20.49倍、予想16.15倍、CAPE 24.69倍（2026年9月） — [Siblis Research Growth vs Value](https://siblisresearch.com/data/growth-value-pe-cape/)
- MSCI World Growth（10/30）: 予想PER 21.72倍、実績28.45倍、PBR 7.69倍、配当利回り0.74% — [MSCI World Growth](https://www.msci.com/indexes/index/105867/msci-world-growth-index)。MSCI World Value（10/30）: 予想PER 14.64倍、実績18.53倍、PBR 2.82倍、配当利回り2.28%、構成816銘柄 — [MSCI World Value](https://www.msci.com/indexes/index/105868/msci-world-value-index)
- 2026年の年初来（12/31/25〜7/17/26）: Russell 1000 Value +17.7% vs Growth +0.9% — [SSGA Mind on the Market 2026-07-27](https://www.ssga.com/us/en/intermediary/insights/mind-on-the-market-27-july-2026)。7月下旬時点でValue +18.3%、Growth -3.6%だが、2022年10月安値からはGrowthが37ポイント優位 — [Bespoke](https://www.bespokepremium.com/interactive/posts/think-big-blog/russell-1000-value-closes-the-gap)
- SSGA: Value指数のテクノロジー比率が3.7%から約18.6%に上昇（金融に次ぐ2位）。2026年6月再構成でApple・Microsoftが一部Valueへ、Alphabet・AMDはValueから外れた — [SSGA](https://www.ssga.com/us/en/intermediary/insights/mind-on-the-market-27-july-2026); [LSEG/FTSE Russell 再構成](https://www.lseg.com/en/insights/ftse-russell/growth-value-or-both-key-style-shifts-in-the-june-2026-russell-reconstitution)
- 日本: TOPIXグロース÷TOPIXバリュー相対株価 0.85（2026-09-11）、長期平均1.12 — [stock-marketdata.com](https://stock-marketdata.com/japan-topix-growth-value-relative-valuation)
- 2025年末比（10/16時点）: TOPIX Small Value +22.4%、TOPIX500 Value +19.8%、TOPIX500 Growth +18.9%、TOPIX Small Growth +13.1% — [マネクリ 2026-10](https://media.monex.co.jp/articles/-/30329)
- TOPIXバリュー指数（2026-05-29）: PER 16.99倍、PBR 1.31倍。上位構成は三菱UFJ FG 6.41%、三井住友FG、みずほFG、三菱商事、住友商事など銀行・商社 — [JPX TOPIX Value ファクトシート](https://www.jpx.co.jp/markets/indices/factsheets/files/004_01_fac2_style_TOPIX%20Value.pdf)
- 東証プライム業種別（10/30）: PER最低は証券9.2倍、鉱業9.9倍、海運10.5倍、不動産12.4倍、輸送用機器13.8倍（PBR1.0倍）、銀行14.6倍（PBR1.5倍）、卸売15.6倍（PBR1.8倍）。PBR0.7倍は電気・ガス、鉄鋼、パルプ・紙。PER最高はサービス27.8倍、小売26.1倍、精密25.8倍。PBR最高は電気機器・精密3.1倍 — [いちよし経済研究所](https://www.ichiyoshi-research.co.jp/market/topix)
- 米国: 予想PER最低はエネルギー13.2倍、金融14.9倍（10/29） — [FactSet](https://advantage.factset.com/hubfs/Website/Resources%20Section/Research%20Desk/Earnings%20Insight/EarningsInsight_103026.pdf)
- 楽天証券（2026-02）: 金利上昇・インフレ局面はバリュー優位、金融・資源・製造業を「三大バリュー株」と位置づけ、2021年以降5年以上バリュー優位 — [楽天証券資料](https://www.rakuten-sec.co.jp/web/learn/seminar/20260221-01/pdf/05.pdf)

### Inferences
- （推定）Growth/Value予想PER比率は1.46（Russell、9月）〜1.48（MSCI World、10月末）。GMOは2022年5月に「グロースはバリューに対し2.3標準偏差割高」としたが（A4/B4参照）、2026年のバリュー優位でも倍率比は依然1.5倍近く、歴史的中央値（概ね1.3倍前後）より高いと推定。11/5〜6のAI株急落は格差をさらに縮める方向。
- 「バリュー」が銀行・商社・エネルギーに偏る現状では、単純な低PERスクリーンはこれら景気・金利・資源価格感応度の高い業種を大量に拾う。金利低下局面（米10年4.84%へ低下、JGB1.8%へ低下）では銀行株の利益持続性に逆風。利益持続性スコアで業種分散を強制する必要あり。

### Gaps
- Russell 1000 Value/Growthの10〜20年の予想PER比率中央値を定量的に示す一次資料は未取得（「歴史的中央値約1.3倍」は推定）。
- TOPIX Value/Growthの最新（10〜11月）PER/PBRはJPXファクトシート（5月）以降未取得。

---

## A3. 金利・為替・政策と円建て投資家への含意

### Takeaway
米FRBは9月に利上げ（2023年7月以来初）後10月は3.75〜4.00%で据え置き（12月再利上げ観測）、日銀は1.25%で据え置き（12月1.5%観測）と、両国とも引き締め方向。米10年4.84〜4.90%、JGB10年1.80%、ドル円157〜158円。円建て投資家の2026年年初来の外国株リターンのうち為替寄与は約+1%（推定）と小さく、7月の162円からは円高方向で逆風。ヘッジコストは年2.5〜2.7%（推定）。

### Cited Findings
- FOMC（10/27-28）: FF金利目標3.75〜4.00%で据え置き、10対2（Cook理事・Hammack総裁が25bp利上げを主張して反対）。9月に25bp利上げ（2023年7月以来初の利上げ） — [CNBC 2026-10-28](https://www.cnbc.com/2026/10/28/fed-interest-rate-decision-october-2026.html); [TD Economics](https://economics.td.com/us-fomc-statement)
- 12月（12/9）25bp利上げ確率82.6%（CME FedWatch、二次情報） — [BYDFi 2026-10](https://www.bydfi.com/market-intelligence/article/fomc-october-2026-results-1/1356)
- 日銀（10/29-30）: 政策金利1.25%で据え置き、8対1（高田委員が1.50%を提案）。基調的物価上昇率が2%と整合的な水準に到達と認定。ETF売却ペースを2027年1月から年約3,300億円→約8,600億円（簿価）に加速 — [大和総研 2026-10-30](https://www.dir.co.jp/report/research/economics/japan/20261030_026168.html); [第一生命経済研究所 2026-10](https://www.dlri.co.jp/report/macro/672292.html); [外為どっとコム 2026-10-30](https://www.gaitame.com/media/entry/2026/10/30/165152)
- 大和総研予想: 2026年12月に1.5%、2027年3月に1.75%へ利上げ後休止、条件次第で2027年6月に2.0% — [大和総研](https://www.dir.co.jp/report/research/economics/japan/20261030_026168.html)
- 米10年債利回り: 約4.90%（11/5）、4.95%（11/3） — [Trading Economics](https://tradingeconomics.com/united-states/government-bond-yield)。11/6アジア時間4.838%（9/9以来の低水準） — [Reuters via Yahoo](https://finance.yahoo.com/markets/world-indices/articles/asia-stocks-drop-ai-rout-235808955.html)
- JGB10年: 11/6に最大9bp低下し1.795%（6/30以来の低水準） — [Reuters via Yahoo](https://finance.yahoo.com/markets/world-indices/articles/asia-stocks-drop-ai-rout-235808955.html)。※別の二次情報が「11/3に2.77%」としているが他出所と大きく矛盾し、誤りの可能性が高い — [TradingNews](https://www.tradingnews.com/news/usdjpy-158-12-reverses-from-a-3-week-high-as-yields-fall-and-tokyo-guards-160)
- ドル円: 11/4〜5に158.12→157.39円（民主党の議会制圧を受けた米金利低下で円高） — [TradingNews](https://www.tradingnews.com/news/usdjpy-158-12-reverses-from-a-3-week-high-as-yields-fall-and-tokyo-guards-160); 11/5頃157.5〜157.7円 — [TraderFactor](https://traderfactor.com/forex-market-today-nfp-in-focus-as-dollar-weakens); 日銀会合後157円台半ば — [お金の学び場 2026-11](https://moneyokane.com/fx/news/2026/11/boj-2026-10/)
- ドル円月平均（FRED）: 2026年7月162.33、8月158.85、9月156.42 — [FRED EXJPUS](https://fred.stlouisfed.org/graph/?g=OzDs)
- 2025年12月30日 NY終値156.06円 — [OANDA Japan](https://www.oanda.jp/lab-education/market_news/mn_992213_202512300806/)。2026年1月2日始値156.35円 — [みんなのFX 2026-01-02](https://min-fx.jp/market/report/2026-1-2/)
- 11/6: ドルは円・スイスフランなど安全通貨に対して下落 — [Reuters via Yahoo](https://finance.yahoo.com/markets/world-indices/articles/asia-stocks-drop-ai-rout-235808955.html)

### Inferences
- （推定）年初来の為替寄与: 156.06円→157.5円で約+0.9%。米株の円換算リターンはほぼ現地通貨リターンに等しい。一方、7月（162円）に買った外国株は為替で約-3%の逆風。
- （推定）為替ヘッジコスト ≈ 米短期金利3.875% − 日本1.25% ≈ 年2.6%。両国とも12月に25bp利上げ観測で差は概ね維持。配当利回り2〜3%の米バリュー株をヘッジすると配当がほぼ相殺される水準。日米金利差縮小（日銀利上げ継続・FRBは「AI失速なら利下げ」シナリオ）は構造的に円高方向で、円建て投資家が海外割安株を買うなら「現地通貨ベースの割安度に、為替で年2〜3%のマージンを要求」するか、国内割安株を優先する根拠になる。
- 日銀利上げは銀行株（NIM拡大）に順風、不動産・公益など高レバレッジ低PBR業種には逆風。11/6のJGB利回り急低下は、11/5〜6の株安がリスクオフで利上げ観測を後退させたことを示唆。

### Gaps
- 11/5・11/6のドル円・米10年・JGB10年の公式終値は未取得（各社レポートの速報値に依拠）。
- 2025年11月上旬のドル円水準（1年前比の為替寄与）は未取得。
- 「外国株投信の円換算リターンのうち為替寄与」の運用会社集計は見つからず、上記は年初・直近レートからの単純推定。

---

## A4. AI資本支出集中とS&P 493のバリュエーション

### Takeaway
Mag 7はS&P500時価総額の33〜35%を占めるが、2026年Q3は利益成長率でMag 7（+22.6%）が他493社（+32.6%）を2022年Q4以来初めて下回り、Q4も同様の予想。均等加重S&P500の予想PERは約16倍（時価総額加重19倍）で、「S&P 493」は概ね16〜17倍（推定）と長期平均並み。AI巡る懸念は11/5〜6の急落で現実化し始めた。

### Cited Findings
- Mag 7のSPY構成比33.2%（10/29、Alphabet 2クラス合算） — [Opening Bell Daily](https://www.openingbelldailynews.com/p/magnificent-7-stocks)。他推計で34.6〜34.9%（10月） — [historyofmarket.com](https://historyofmarket.com/articles/magnificent-7-sp500-weight)
- Yardeni（2025-12-18）: Mag 7の時価総額は2年で約10兆→20兆ドル、S&P500時価総額の31.7%、予想売上と予想利益のシェアはそれぞれ12.7%・24.4%と読み取れる（取得結果で両者の順序が入れ替わっている可能性あり） — [Yardeni QuickTakes](https://www.yardeniquicktakes.com/s-p-500-with-without-the-magnificent-7/)
- Q3 2026ブレンド増益率: Mag 7 +22.6%（9/30時点予想33.6%から低下、5社中2社のみEPS上振れ、合計で予想を14.7%下回る）vs 他493社 +32.6%（27.8%から上昇）。確定すれば2022年Q4以来初めてMag 7が493社を下回る。Q4予想もMag 7 +22.6% vs 493社 +30.8% — [FactSet 2026-10-30](https://advantage.factset.com/hubfs/Website/Resources%20Section/Research%20Desk/Earnings%20Insight/EarningsInsight_103026.pdf)
- 注記: Alphabet（有価証券評価損87億ドル）、Meta（訴訟和解費用98.9億ドル）、Amazon（前年のAnthropic投資益95億ドル）がGAAP EPSベースで下振れ要因 — [FactSet 2026-10-30](https://advantage.factset.com/hubfs/Website/Resources%20Section/Research%20Desk/Earnings%20Insight/EarningsInsight_103026.pdf)
- NVIDIAがMag 7の利益成長の約61%を占め、NVIDIA除くMag 6の成長率は18.7%でS&P493（29.1%）を下回る — [LSEG Lipper Alpha 2026-10](https://lipperalpha.refinitiv.com/2026/10/magnificent-7-earnings-preview-26q3-mag-6-lags-sp-493-for-second-consecutive-quarter/)
- 均等加重S&P500 予想PER 16.0倍（2026年高値から-13%）vs 時価総額加重19.0倍（高値から-15%、10年平均並み）（9月下旬） — [Citadel Securities](https://www.citadelsecurities.com/news-and-insights/global-market-intelligence/october-the-q4-reload/)
- 11/5米国: NASDAQ -5.5%、フィラデルフィア半導体指数 -12.2%、NASDAQは1カ月前の高値から-12%。要因は中間選挙で民主党が勝利しAI規制強化・AIインフラ投資減速への懸念、AI投資回収への疑念、データセンターへの地元反対、CoreWeave -10%・CDS最大 — [Reuters via Yahoo 2026-11-06](https://finance.yahoo.com/markets/world-indices/articles/asia-stocks-drop-ai-rout-235808955.html)
- IT セクターの純利益率32.4%（5年平均25.9%）、Q3増益率67.5%。S&P500全体の純利益率14.9%は2009年以降2番目（最高は前四半期17.0%） — [FactSet 2026-10-30](https://advantage.factset.com/hubfs/Website/Resources%20Section/Research%20Desk/Earnings%20Insight/EarningsInsight_103026.pdf)

### Inferences
- （推定）Yardeniの時価総額31.7%・利益24.4%のシェアを使うと、Mag 7のPERは指数の約1.3倍、493社は約0.9倍。FactSetの18.7倍に当てればMag 7 ≈ 24倍、493社 ≈ 16.8倍。均等加重16.0倍（Citadel）と整合的。「S&P 493」は10年平均（指数全体で19.1倍）を下回り、割高感は限定的。
- 米国の利益率（IT 32%、全体14.9%）は記録的水準で、「割安」判定でPERを使う際は利益率の平均回帰リスクを織り込む必要がある（B3の正常化ルール適用）。
- AI投資の恩恵を受けた日本・韓国・台湾の半導体関連（Kioxia、SK hynix、Samsung、TSMC）が11/6に10%超下落。低PER（KOSPI 4.4倍）は「ピーク利益での割安」の典型例。

### Gaps
- 2026年10〜11月時点の「S&P 500 ex-Mag 7 予想PER」の公表値（FactSet/Yardeni/Bloomberg）は未取得。上記16.8倍は推定。
- Mag 7のAI関連資本支出総額（2026年計画値）とFCF圧迫度の一次資料は本調査範囲では未取得。

---

## A5. 決算シーズンの状況（米Q3 2026、日本2Q FY2026）

### Takeaway
米Q3は60%消化時点で82%がEPS上振れ（5年平均78%）だが上振れ幅は+1.9%と2022年Q4以来の小ささ、増益率は+30.2%で3四半期連続25%超。Q4ガイダンスはネガティブ比率40%（5年平均60%）と良好。日本は中間決算の集計がまだ出揃っておらず（11/6時点）、事前コンセンサスは2Q経常利益-5%（前年の株式評価益の反動）、AI・半導体は+193%、野村は2Q EPS +10〜15%、年度TOPIX EPS +19.2%を見込む。

### Cited Findings
**米国（FactSet、10/30時点、60%が発表済み）** — すべて [FactSet Earnings Insight 2026-10-30](https://advantage.factset.com/hubfs/Website/Resources%20Section/Research%20Desk/Earnings%20Insight/EarningsInsight_103026.pdf)
- EPS上振れ企業比率82%（1年平均82%、5年78%、10年77%）。EPS上振れ幅+1.9%（1年平均+13.8%、5年+7.5%、10年+8.0%）、確定なら2022年Q4（+1.3%）以来の低さ。
- 売上上振れ比率70%（5年平均70%）、上振れ幅+1.7%（5年+1.8%）。
- Q3ブレンド増益率+30.2%（9/30時点+29.1%）、増収率+13.4%。11セクターすべて増益、エネルギー・IT・素材が牽引。ヘルスケア+5.2%、コミュニケーション・サービスは上振れ幅-21.5%（Meta、Alphabet）。
- 純利益率14.9%（前四半期17.0%、前年13.0%、5年平均12.6%）。
- Q4ガイダンス: ネガティブ19社・ポジティブ28社、ネガティブ比率40%（5年平均60%、10年平均59%）。通期ガイダンス270社中ネガティブ34%。
- Q4のボトムアップEPS予想は10月中に+1.4%上方修正（通常は四半期最初の月に-1.1〜-1.9%低下）。3四半期連続の上方修正。エネルギー+20.3%、生活必需品-4.0%。
- 予想増益率: Q4 2026 +28.4%、CY2026 +32.9%（増収+13.0%）、Q1 2027 +19.2%、Q2 2027 +2.8%、CY2027 +16.3%（増収+9.6%）。
- ボトムアップ目標株価9,327.80（10/29終値比+20.8%）。Buy格付け比率59.9%。
- 市場反応: EPS上振れ企業は平均+1.6%（5年平均+0.9%）、下振れ企業は-2.1%（5年平均-3.1%）。

**日本（2027年3月期 中間決算）**
- 野村（10/7、QUICKコンセンサス10/2時点、3月決算571社）: 2Q経常利益は前年同期比約-5%（1Qは+64%）。主因は前年に大きな保有株式評価益があった情報・通信。電気機器・その他金融・非鉄・海運が相殺。AI・半導体関連は約+193%。野村の2Q EPS予想は+10〜15%、トップダウンの2026年度TOPIX EPS成長率+19.2%。8/31→10/2でコンセンサス上方修正: 電気機器・証券・保険・JR/私鉄・通信・サービス。下方修正: 建設・医薬品・石油・鉄鋼・電力 — [野村證券 2026-10-07](https://www.nomura.co.jp/wealthstyle/article/0898/)
- 1Q（4〜6月）決算: 全体の3分の2が増益だが、株価は悪材料へのネガティブ反応が目立った — [野村證券 2026-08](https://www.nomura.co.jp/wealthstyle/article/0804/)
- 日経ヴェリタス（10月中旬）: AI・半導体関連を中心に通期上方修正ラッシュへの期待、市場予想は強含み — [日経ヴェリタス 2026-10](https://www.nikkei.com/prime/veritas/article/DGXZQOUB159TG0V11C26A0000000)
- 野村は日経平均の2026年末見通しを70,000円に上方修正（需給環境を反映） — [野村證券 2026](https://www.nomura.co.jp/wealthstyle/article/0833/)
- 11/6個別例: IIJが中間決算と同時に通期純利益を2%上方修正 — [株探 2026-11-06](https://s.kabutan.jp/news/k202611060018/)
- 参考（前年）: 2026年3月期中間決算では11/7時点で時価総額77%（682社）が出揃い、コンセンサス上振れ・通期上方修正が優勢だった — [野村證券 2025-11](https://www.nomura.co.jp/wealthstyle/article/0496/)

### Inferences
- 米国は「上振れ比率は高いが上振れ幅は小さい」= 予想が十分に引き上げられた後の決算であり、サプライズ余地が縮小。2027年Q2予想+2.8%への急減速は前年比のベース効果で、2027年にかけて増益率の正常化が織り込まれている。利益率の平均回帰が起きれば予想PER18.7倍は実質20倍超。
- 日本の2Q「-5%」は前年の一過性評価益の反動が主因で、実態（事業利益）は増益基調。ただし中間決算の集計は11月中旬以降に出るため、本稿時点では「上振れ優勢か」を確定できない。11/6の株価急落下で発表される中間決算は、良好な内容でも株価反応が鈍い可能性がある（1Qのネガティブ反応傾向の延長）。

### Gaps
- 日本の2Q決算の集計値（上振れ社数比率、通期上方修正比率、時価総額カバー率）は11/6時点で未公表・未取得。11月中旬の野村・SMBC日興・日経の集計を待つ必要がある。
- FactSetの11/6版（翌週号）は未発行。NVIDIA（11/17発表）はQ3未反映。

---

## B1. どの割安指標が将来リターンを予測し、バリュートラップを避けるか

### Takeaway
長期の実証では EV/EBIT（EBITDA）が最も頑健な割安指標で、単独PER・PBR・アナリスト予想PERを上回る。割安指標とクオリティ（粗利益率・F-score・QMJ）の組み合わせは、両者が負相関のため単独より改善が大きく、Piotroskiは高BM株の平均リターンを年+7.5%改善。ただし公表後の効果減衰（Piotroski、アクルーアル）も報告されている。

### Cited Findings
- Gray & Vogel "Analyzing Valuation Measures"（1971〜2010、均等加重・年次リバランス）: 最割安グループの年率リターンは EBITDA/TEV 17.66%（3ファクターアルファ2.91%、割安-割高スプレッド9.69%）、E/M（PERの逆数）15.23%（アルファなし、スプレッド5.82%）、B/M 15.03%（アルファなし）。アナリスト予想ベースの予想益回り（FE/M）は「大差で最悪」 — [Greenbackd（Carlisle）enterprise multiple まとめ](https://greenbackd.com/category/strategy/enterprise-multiple)
- Loughran & Wellman（JFQA 2011）: エンタープライズ・マルチプル（EM）のバリュープレミアムは年5.8%、B/Mは4.8%（1926〜2004）。EMは時価総額上位3五分位（市場の約94%）で有意だがB/Mは有意でない（1963〜2008） — [Loughran & Wellman, JFQA](https://cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/new-evidence-on-the-relation-between-the-enterprise-multiple-and-average-stock-returns/5CD22A12A06AFCDC5233E477757FB659); [Greenbackd](https://greenbackd.com/category/strategy/enterprise-multiple)
- Greenblatt マジックフォーミュラ: 原著は年30.8% vs 市場12.3%と主張するが、Gray の再現では「大きな超過はあるが31%には遠く及ばず」。Montier（1993〜2005）: マジックフォーミュラの均等加重指数超過は米3.6%、欧8.8%、英7.3%、日本10.8%。純粋なEBIT/TEVは日本を除く全地域でマジックフォーミュラを上回った — [Greenbackd](https://greenbackd.com/category/strategy/enterprise-multiple)
- 長期平均利益の使用: Anderson & Brooks（英国）は8年平均利益を使うと1年利益比でバリュープレミアムが6%向上。Gray & Vogelは長期平均の一貫した効果を見出さず — [Greenbackd](https://greenbackd.com/category/strategy/enterprise-multiple)
- Novy-Marx（JFE 2013, vol.108, 1-28）: 粗利益/総資産は簿価時価比率と同程度の予測力を持ち、両者は負相関のため組み合わせが有効。粗利益率をコントロールすると多くの利益関連アノマリーが説明できる。NYSE 1963年7月〜2010年12月 — [RePEc](https://econpapers.repec.org/RePEc:eee:jfinec:v:108:y:2013:i:1:p:1-28); [CFA Institute "Quality Control"](https://rpc.cfainstitute.org/research/cfa-magazine/2014/quality-control); [Alpha Architect](https://alphaarchitect.com/profitability-and-future-stock-returns/)
- Piotroski（2000）: 高BM株のうち財務的に強い企業（F-score高）を選ぶと平均リターンを年7.5%以上改善。F-score戦略は1976〜1996年に年23%。同サンプルで割安株のうち2年後に市場を上回ったのは44%未満 — [Validea](https://blog.validea.com/joseph-piotroski-separating-winners-from-losers-in-value-investing/); [Summitward](https://summitward.com/learn/cheap-for-a-reason-value-traps)
- F-scoreの再現性: 米国では「高BM株の勝者・敗者を区別しなくなった」とする研究 — [Creighton University](https://researchworks.creighton.edu/esploro/outputs/journalArticle/Value-Stocks-and-Accounting-Screens-Has/991006117468602656)。国際的には有効とする研究（Walkshäusl 2020） — [Univ. Regensburg](https://epub.uni-regensburg.de/44019/1/Walksh%C3%A4usl2020_Article_PiotroskiSFSCOREInternationalE.pdf)
- Asness, Frazzini & Pedersen "Quality Minus Junk"（RAS 2019）: 安全・収益性・成長・良好な経営（配当政策）で定義したクオリティのロング・ショートは米国と24カ国で有意なリスク調整後リターン。クオリティの価格が低い時ほど将来のQMJリターンが高い — [SSRN](https://papers.ssrn.com/abstract=2312432)
- 「最も割安かつ最も収益性が低い」五分位は1963〜2026年で年13.1% vs 市場10.9%だが5ファクターアルファはなし（出所の一次データ未確認） — [Summitward](https://summitward.com/learn/cheap-for-a-reason-value-traps)
- アクルーアル・アノマリー（Sloan 1996）: 低アクルーアル十分位ロング／高アクルーアル・ショートで翌年に有意な超過リターン。ただし米国では減衰し「平均的にもはや有意にプラスではない」 — [Green, Hand & Soliman "Going, Going, Gone?" Management Science](https://pubsonline.informs.org/doi/fpi/10.1287/mnsc.1110.1320)
- Penman: 低マルチプル株は「リスクの高い成長」を買っている場合があり、B/Pはそのリスクを示す指標。バリューは平均では高リターンだが個別では裏目に出る — [Penman "The Value Trap"](https://business.columbia.edu/sites/default/files-efs/pubfiles/18184/Penman_value_trap.pdf)

### Inferences
- ルーブリックの割安度ではEV/EBITを最大ウェイト（2.5/10）に置き、PERは補助、PBRは「ROEが一定以上のときのみ加点」とするのが実証に整合する。アナリスト予想ベースの予想PERは単独では最弱なので、実績PER・正常化PERと併用する。
- 株主還元利回り（配当+自社株買い）は、Gray & Vogelの直接の検証対象外だが、Novy-Marx/QMJの「ペイアウト」要素とFCFの裏付けとして機能する。純希薄化はトラップ兆候として減点。
- 「割安×クオリティ」の二軸は、2026年の日本市場のように銀行・商社など景気敏感業種にバリューが集中する局面で、業種偏りを緩和する効果が期待できる。

### Gaps
- FCF利回り・株主利回り単独の長期実証（Gray & Vogelの表は画像のため未取得）。
- Fama-French（HML）やKen Frenchデータライブラリからの直接の数値は本調査では取得せず。
- Gray & Carlisle『Quantitative Value』の原典の数値（Greenbackd経由の要約に依拠）。

---

## B2. 利益持続性（モート・安定性・財務・キャッシュ転換）をどう採点するか

### Takeaway
実証と実務の双方が指す持続性の構成要素は、(1) 10年のROE/ROICの水準と安定性、(2) 粗利益率の安定（価格決定力の代理）、(3) 低レバレッジ・高インタレストカバレッジ、(4) FCF/純利益と低アクルーアル、(5) 売上トレンド、(6) 景気循環・資本集約度。日本では「低PBR×低ROE」象限から脱出した企業群がROE 8%を境に二極化しており、ROEの絶対水準が持続性の第一関門になる。

### Cited Findings
- QMJのクオリティ定義: 収益性（粗利益/資産、ROE、ROA、CFOA、粗利益率、低アクルーアル）、成長、安全性（低ベータ、低レバレッジ、低倒産リスク、低利益変動）、ペイアウト（純発行株数の少なさ） — [SSRN QMJ](https://papers.ssrn.com/abstract=2312432)
- Novy-Marx: 粗利益（売上-売上原価）/総資産が収益性の「最もクリーン」な指標で、純利益より予測力が高い — [RePEc](https://econpapers.repec.org/RePEc:eee:jfinec:v:108:y:2013:i:1:p:1-28); [CFA Institute](https://rpc.cfainstitute.org/research/cfa-magazine/2014/quality-control)
- Piotroski F-score 9項目: ROA>0、CFO>0、ΔROA>0、CFO>純利益（アクルーアル）、Δレバレッジ<0、Δ流動比率>0、新株発行なし、Δ粗利益率>0、Δ資産回転率>0 — [Validea](https://blog.validea.com/joseph-piotroski-separating-winners-from-losers-in-value-investing/); [Stockopedia](https://stockopedia.com/content/the-piotroski-f-score-a-fundamental-screen-for-value-stocks-55711)
- 第一生命経済研究所（2026-04-01、プライム1,508社、2023年2月→2026年2月）: PBR1倍・ROE8%の4象限で、「高PBR・高ROE」552社(36.6%)→780社(51.7%)、「低PBR・低ROE」506→312社、「低PBR・高ROE」249→93社。低PBR・低ROE企業506社のうち227社は3年後も同象限に残留。ROEとPBRの関係は2026年の方が明確 — [第一生命経済研究所](https://www.dlri.co.jp/report/ld/588240.html)
- GMO/Inker の「トラップ」定義: 過去12カ月の売上が予想未達かつ将来の売上見通しを引き下げた銘柄。MSCI USA Valueで毎年約3分の1が該当し、指数を平均9%アンダーパフォーム — [Retirement Income Journal](https://retirementincomejournal.com/article/growth-traps-outnumber-value-traps-gmo/); [AdvisorAnalyst (Inker)](https://advisoranalyst.com/2022/05/26/growth-traps-snap-shut-more-pain-to-come.html/)
- 米国Q3 2026: 7セクターで純利益率が前年比上昇（エネルギー15.6% vs 8.1%、IT 32.4% vs 27.5%）、金融・一般消費財は低下 — [FactSet](https://advantage.factset.com/hubfs/Website/Resources%20Section/Research%20Desk/Earnings%20Insight/EarningsInsight_103026.pdf)

### Inferences
- 持続性の各要素は、F-score（1年の方向性）ではなく10年の水準・安定性で測るのが本件（1〜3年保有の割安株選別）の目的に合う。F-scoreは「直近1年で悪化していないか」のゲートとして補助的に使う。
- 日本では「ROE 8%未満が3年続いた低PBR企業の約45%（227/506）は3年後も同象限」が示す通り、ROEが資本コストを下回り続ける企業の再評価確率は低い。持続性スコアでROE/ROICの水準に最大の配点を置く根拠。
- 粗利益率の10年安定性（標準偏差/平均）は価格決定力の定量代理として使える。売上-原価の構造が安定している企業は、インフレ下でも転嫁できていると解釈できる。
- 業種補正: 金融（銀行・保険・証券）はEV/EBIT・ネットデット/EBITDAが定義できないため、ROE・PBR・CET1比率・与信費用率で代替する必要がある。

### Gaps
- 「10年ROIC変動係数」や「粗利益率の安定性」が将来リターンを予測するという直接の学術的実証は本調査では取得できず（QMJの「低利益変動」要素から類推）。
- 日本株の持続性指標（ROE安定性・ネットキャッシュ比率）の将来リターン予測力に関する国内実証は未取得。

---

## B3. バリュートラップ診断と循環利益の正常化

### Takeaway
トラップの実証的シグナルは「売上の予想未達＋見通し引き下げ」（GMO：バリュー株の約1/3が毎年該当、-9%）、ROIC低下、レバレッジ上昇、希薄化、配当減、低ROEの固定化（日本：低PBR・低ROE残留45%）。「ピーク利益での割安」は10年平均利益またはミッドサイクル利益率で正常化して判定する（Anderson & Brooks: 8年平均利益でバリュープレミアム+6%）。2026年11月はKOSPI予想PER 4.4倍、米IT純利益率32%など、正常化が必須の局面。

### Cited Findings
- GMO: バリュートラップ（売上未達+見通し引き下げ）はMSCI USA Valueの約1/3/年、指数比-9%。グローストラップは約37%、-13%。「市場が高いマルチプルを与えた銘柄は、見通し悪化時にほぼ必ず急落」 — [Retirement Income Journal](https://retirementincomejournal.com/article/growth-traps-outnumber-value-traps-gmo/); [AdvisorAnalyst](https://advisoranalyst.com/2022/05/26/growth-traps-snap-shut-more-pain-to-come.html/)
- Piotroski: 割安株（高BM）のうち2年で市場を上回るのは44%未満 — [Summitward](https://summitward.com/learn/cheap-for-a-reason-value-traps)
- Anderson & Brooks: 8年平均利益によるPERは1年利益のPERよりバリュープレミアムが6%高い（英国） — [Greenbackd](https://greenbackd.com/category/strategy/enterprise-multiple)
- KOSPI 12カ月予想PER 4.41倍（半導体<3倍）、半導体除く10.3倍（20年平均10.4倍） — [Money Today 2026-10-20](https://www.mt.co.kr/index.php/en/stock/2026/10/20/2026102015013299958)。11/6にSamsung -10%、SK hynix -12%、Kioxia -14% — [Reuters via Yahoo](https://finance.yahoo.com/markets/world-indices/articles/asia-stocks-drop-ai-rout-235808955.html)
- S&P500純利益率14.9%は2009年以降2番目の高さ、IT 32.4%（5年平均25.9%）、エネルギー15.6%（5年平均10.1%） — [FactSet](https://advantage.factset.com/hubfs/Website/Resources%20Section/Research%20Desk/Earnings%20Insight/EarningsInsight_103026.pdf)
- Shiller CAPE（10年平均実質利益ベース）38.79倍 vs 実績PER 25.06倍（11/5） — [multpl CAPE](https://www.multpl.com/shiller-pe); [multpl PE](https://www.multpl.com/s-p-500-pe-ratio)
- 第一生命経済研究所（2025-07-10、2023年3月→2025年4月）: 東証要請への開示を「アップデート」した企業の株価上昇は、低い出発PBRによるもので、「開示のアップデート自体は株価推移に影響を与えていない」。開示企業でもPBR1倍割れが5割以上 — [第一生命経済研究所](https://www.dlri.co.jp/report/ld/477251.html)
- 日経ヴェリタス（2025-03）: 東証要請2年でPBR改善は踊り場、「稼ぐ力」が物足りない — [日経ヴェリタス](https://www.nikkei.com/prime/veritas/article/DGXZQOUB2566I0V20C25A3000000)
- Penman: 低マルチプルは「リスクの高い成長」を買うことになりうる — [Penman](https://business.columbia.edu/sites/default/files-efs/pubfiles/18184/Penman_value_trap.pdf)

### Inferences
- 正常化の実務ルール（提案）: ①直近営業利益率が10年平均+1σを超える企業は、10年平均利益率×直近売上で「正常化利益」を作り、PER・EV/EBITを再計算する。②10年平均利益（Graham/Shiller型）と直近利益の両方でPERを計算し、高い方を採用する。③資源・半導体・海運・鉄鋼・化学・証券は無条件で正常化対象。これにより、KOSPI半導体（PER 3倍未満）や米エネルギー（純利益率が5年平均の1.5倍）の「見かけの割安」を除外できる。
- 日本の低PBR株については、「開示・還元強化」のカタリスト自体ではなく、ROE改善（8%超）と出発PBRの低さが再評価を説明する。したがってスクリーンでは「経営計画の開示有無」を加点せず、ROEの実績推移を見る。
- トラップ診断は減点ではなく「ゲート」として運用する方が機械的に適用しやすい（B5の失格条件）。

### Gaps
- 「10年平均利益で見た低PERの1〜3年リターン」の日本株での実証は未取得。
- ROIC低下・レバレッジ上昇・配当減それぞれの、低PER株における将来リターンへの寄与度（定量）は一次資料未取得。

---

## B4. ベースレート（低PER株の勝率、日本低PBR株の2023〜2026年）

### Takeaway
個別の割安株が1〜3年で市場を上回る確率は半分以下（Piotroski: 44%未満/2年）で、約1/3は売上未達＋見通し引き下げの「トラップ」になる（GMO）。一方、分散ポートフォリオとしての割安株は長期で年5〜10%のプレミアム（EV/EBITDAスプレッド9.7%、EMプレミアム5.8%）。日本では東証要請以降3年で低PBR・低ROE企業の時価総額指数は227（2023年2月=100）と高PBR・高ROE群（171）を上回ったが、企業数の約45%は同象限に残留し、PBR1倍割れ比率は50%→27%に低下。

### Cited Findings
- Piotroski（1976〜1996）: 割安株のうち2年後に市場を上回ったのは44%未満、ただしグループ全体ではバリュープレミアムを獲得 — [Summitward](https://summitward.com/learn/cheap-for-a-reason-value-traps)
- GMO: バリュー株の約1/3/年がトラップ、-9%/年 — [Retirement Income Journal](https://retirementincomejournal.com/article/growth-traps-outnumber-value-traps-gmo/)
- Gray & Vogel: EBITDA/TEV最割安 17.66%/年 vs 最割高7.97%、スプレッド9.69%（1971〜2010）。E/M（低PER）最割安15.23% vs 最割高9.41% — [Greenbackd](https://greenbackd.com/category/strategy/enterprise-multiple)
- Loughran & Wellman: EMプレミアム年5.8%（1963〜2008は大型株でも有意） — [JFQA](https://cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/new-evidence-on-the-relation-between-the-enterprise-multiple-and-average-stock-returns/5CD22A12A06AFCDC5233E477757FB659)
- 日本（第一生命経済研究所、2023年2月→2026年2月、プライム1,508社）: PBR1倍割れ企業は755社(50.1%)→405社(26.9%)（象限合計から算出）。時価総額指数（2023年2月=100）: 高PBR高ROE 171、高PBR低ROE 143、低PBR低ROE 227、低PBR高ROE 224。レポートは「出発バリュエーションの低さが上昇率を膨らませた」と注記。低PBR低ROE 506社中、高PBR高ROEへ121社、高PBR低ROEへ109社、同象限残留227社 — [第一生命経済研究所 2026-04-01](https://www.dlri.co.jp/report/ld/588240.html)
- 日本（同、2025-07-10）: 開示アップデート企業の平均PBR 1.34倍（2025年4月）、PBR1倍割れが5割以上。「未開示」131社の約半数はPBR2倍以上（開示が不要なほど高評価） — [第一生命経済研究所 2025-07-10](https://www.dlri.co.jp/report/ld/477251.html)
- 日本2026年: TOPIX Small Value +22.4%（年初来10/16）が全スタイルで最高 — [マネクリ](https://media.monex.co.jp/articles/-/30329)。TOPIXグロース/バリュー比0.85（長期平均1.12） — [stock-marketdata.com](https://stock-marketdata.com/japan-topix-growth-value-relative-valuation)
- 韓国: KOSPI PBR 2.07倍（2026年4月、過去最高）でも上場企業の60%はPBR1倍未満 — [이투데이](https://www.etoday.co.kr/news/view/2579169)
- 米国2026年: Russell 1000 Value +17.7% vs Growth +0.9%（〜7/17） — [SSGA](https://www.ssga.com/us/en/intermediary/insights/mind-on-the-market-27-july-2026)

### Inferences
- ベースレートからの含意: 個別銘柄の勝率は5割未満なので、(a) 10銘柄以上の分散、(b) 勝率を上げるためのクオリティゲート（Piotroskiは高BM内でF-score高群の勝率を改善）、(c) 1〜3年の保有を前提とする。
- 日本の低PBR群の2023〜26年のリターンは「低PBR×ROE改善」組（121+109社の象限移動）が牽引し、ROE改善なく残留した227社は時価総額指数に寄与していないと推定（レポートは象限別の内訳を示していない）。低PBR単独ではなく「低PBR×ROE 8%以上 or 改善トレンド」が実効的な条件。
- 2026年はバリューの強い年であり、11/6時点で割安株の相対的な出発点は2023〜25年より有利ではない。ただし11/5〜6のAI株急落でグロースとの格差は縮小方向。

### Gaps
- 「PER10倍未満の銘柄が1〜3年で市場を上回った頻度」を直接示す日本株・米国株の最新データ（2010年代以降）は未取得。Piotroski（1976〜96）とGMO（1997〜2022）に依拠。
- 日本の低PBR群のうち「残留227社」のリターンの個別集計は資料に含まれず。
- Verdad・Alpha Architectのヒット率研究は検索で特定できず。

---

## B5. 提案ルーブリック：利益持続性スコア（0〜10）と割安度スコア（0〜10）

### Takeaway
以下の表は、コーディネーターが入力項目（PER実績/予想、EV/EBIT、FCF利回り、PBR×ROE、株主還元利回り、10年ROE/ROIC安定性、ネットデット/EBITDA、売上トレンド、モート、景気循環、ガバナンス）だけで機械的に採点できるよう設計した。実証（B1〜B4）に基づき、割安度ではEV/EBITを最大配点、持続性ではROE/ROIC水準・安定性とモートを最大配点とし、トラップ診断は「失格ゲート」として独立させる。

### Cited Findings
- 配点の根拠: EV/EBIT(DA)が最強の割安指標 — [Greenbackd / Gray & Vogel](https://greenbackd.com/category/strategy/enterprise-multiple); [Loughran & Wellman](https://cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/new-evidence-on-the-relation-between-the-enterprise-multiple-and-average-stock-returns/5CD22A12A06AFCDC5233E477757FB659)。予想PER単独は最弱 — [Greenbackd](https://greenbackd.com/category/strategy/enterprise-multiple)。収益性×割安の組み合わせ — [Novy-Marx](https://econpapers.repec.org/RePEc:eee:jfinec:v:108:y:2013:i:1:p:1-28)。F-score — [Validea](https://blog.validea.com/joseph-piotroski-separating-winners-from-losers-in-value-investing/)。トラップ定義（売上未達+見通し引き下げ） — [GMO/Inker](https://advisoranalyst.com/2022/05/26/growth-traps-snap-shut-more-pain-to-come.html/)。ROE 8%閾値と低PBR低ROE残留 — [第一生命経済研究所](https://www.dlri.co.jp/report/ld/588240.html)。長期平均利益での正常化 — [Anderson & Brooks via Greenbackd](https://greenbackd.com/category/strategy/enterprise-multiple)。
- 日本の基準値: 東証プライム予想株式益回り6.42%（=予想PER 15.55倍）、予想配当利回り2.62%、PBR 1.67倍（11/5） — [日経電子版](https://www.nikkei.com/markets/kabu/japanidx/)。ROE 9.5% — [いちよし経済研究所](https://www.ichiyoshi-research.co.jp/market/topix)。米国: 予想PER 18.7倍、エネルギー13.2倍・金融14.9倍 — [FactSet](https://advantage.factset.com/hubfs/Website/Resources%20Section/Research%20Desk/Earnings%20Insight/EarningsInsight_103026.pdf)

### Inferences（提案ルーブリック本体）

**事前処理（全候補に共通）**
1. 利益の正常化: 直近営業利益率が10年平均+1σ超、または業種が資源・半導体・海運・鉄鋼・化学・証券・不動産販売の場合、「正常化利益 = 10年平均営業利益率 × 直近売上」を算出し、PER・EV/EBITは「直近利益ベース」と「正常化ベース」の高い方（保守的）で採点する。
2. 通貨・分割基準をそろえ、EPS・BPSは最新の株式数で統一。金融株はEV/EBIT・ネットデット/EBITDAを「該当なし」とし、代替指標（後述）で採点。
3. 予想PERは実績PERとの乖離が25%超（予想EPS増益率25%超）の場合、予想値ではなく実績値を採点に使う（予想益回りの予測力が最弱であることによる）。

**表1: 利益持続性スコア（0〜10、小計の合算）**

| # | 項目 | 入力 | 2点 / 満点 | 1点 / 中間 | 0点 | 配点 |
|---|---|---|---|---|---|---|
| S1 | ROE/ROIC水準と安定性（10年） | 10年のROE（金融）またはROIC（非金融） | 10年中9年以上でROIC≥8%（ROE≥8%）かつ変動係数<0.35 → 2.0 | 10年中7〜8年で≥8%、または全年≥8%だが変動係数0.35〜0.6 → 1.0 | 6年以下、または直近3年平均<6% → 0 | 2.0 |
| S2 | 財務健全性 | ネットデット/EBITDA、インタレストカバレッジ | ネットキャッシュ、または<1.0倍かつカバレッジ>10倍 → 2.0 | 1.0〜2.5倍かつカバレッジ4〜10倍 → 1.0 | >2.5倍、またはカバレッジ<4倍 → 0 | 2.0 |
| S3 | キャッシュ転換・アクルーアル | 5年累計FCF/純利益、(純利益−営業CF)/総資産 | FCF/NI≥0.8かつアクルーアル<5% → 1.5 | FCF/NI 0.5〜0.8、またはアクルーアル5〜10% → 0.75 | FCF/NI<0.5、5年累計FCF赤字、またはアクルーアル>10% → 0 | 1.5 |
| S4 | 売上トレンド | 5年売上CAGR、直近2年の増減 | CAGR≥名目GDP成長（日本≥3%、米国≥5%）かつ2年連続減収なし → 1.5 | CAGR −1%〜閾値未満で2年連続減収なし → 0.75 | CAGR<−1%、または2年連続減収、または直近12カ月で売上予想未達＋見通し引き下げ → 0 | 1.5 |
| S5 | モート（定性） | 価格決定力（10年粗利益率の標準偏差/平均<0.10かつ低下トレンドなし）、スイッチングコスト（更新率・長期契約・規制免許）、規模（主要市場でシェア1〜2位） | 3要素のうち2つ以上に明確な証拠 → 2.0 | 1つ → 1.0 | なし／コモディティ的 → 0 | 2.0 |
| S6 | 景気循環・ピーク利益露出 | 直近営業利益率 vs 10年平均と標準偏差 | 平均+1σ以内、かつ非景気敏感業種 → 1.0 | 平均+1σ〜+2σ、または景気敏感業種だが利益率は平均以内 → 0.5 | 平均+2σ超、または直近利益が10年最高で業種が資源・半導体・海運等 → 0 | 1.0 |
| 合計 | | | | | | 10.0 |

**ガバナンス調整（S合計から減点、下限0）**: 以下各−1.0。(a) 過去5年に合理的な方針変更以外の減配、(b) 直近3年の年率希薄化>2%（新株・転換社債）、(c) 親子上場・支配株主との利益相反、不適切会計・監査法人の突然の交代・金商法/取引所からの処分、(d) 社外取締役比率<1/3または買収防衛策の継続。

**表2: 割安度スコア（0〜10、小計の合算）**

| # | 項目 | 入力 | 満点 | 中間 | 0点 | 配点 |
|---|---|---|---|---|---|---|
| V1 | EV/EBIT（正常化後） | EV ÷ 正常化EBIT（直近EBITと比較し低い方の利益を採用） | <6倍 → 2.5 | 6〜8倍 → 2.0、8〜10倍 → 1.5、10〜13倍 → 1.0、13〜16倍 → 0.5 | >16倍、またはEBIT赤字 → 0 | 2.5 |
| V2 | PER（実績・予想・正常化の高い方） | 事前処理3を適用 | <10倍 → 2.0 | 10〜13倍 → 1.5、13〜16倍 → 1.0、16〜20倍 → 0.5 | >20倍 → 0 | 2.0 |
| V3 | FCF利回り | 5年平均FCF ÷ 時価総額（直近FCFが5年平均の2倍超なら平均を採用） | >10% → 2.0 | 7〜10% → 1.5、5〜7% → 1.0、3〜5% → 0.5 | <3%、またはFCF赤字 → 0 | 2.0 |
| V4 | PBR × ROEゲート | PBR、直近3年平均ROE | ROE≥8%かつPBR<0.8倍 → 1.5 | ROE≥8%かつPBR 0.8〜1.0倍 → 1.0、ROE≥10%かつPBR 1.0〜1.5倍 → 0.5、ROE 5〜8%かつPBR<0.8倍 → 0.5 | ROE<5%（低PBRでも0）、またはPBR>1.5倍 → 0 | 1.5 |
| V5 | 株主還元利回り | （配当+純自社株買い−新株発行）÷ 時価総額、直近12カ月 | >6% → 2.0 | 4〜6% → 1.5、2.5〜4% → 1.0、1〜2.5% → 0.5 | <1%、または純希薄化 → 0 | 2.0 |
| 合計 | | | | | | 10.0 |

**金融株（銀行・保険・証券）の代替**: V1は「PER（正常化）」を2.5点で再利用（配点をV2と合わせ4.5点をPERに集中させず、V1をPBR×ROEに差し替え、V4を「CET1/ソルベンシー・マージン・与信費用率の5年安定性」に置換）。S2は「CET1比率（銀行）≥11%、ソルベンシー・マージン（保険）≥700%」で2点。

**失格ゲート（スコアに関係なく候補から除外）**
- G1: 直近12カ月に売上が市場予想未達かつ会社が売上見通しを引き下げ（GMOのトラップ定義）。
- G2: 継続企業の前提に疑義、債務超過、3期連続営業赤字。
- G3: 正常化PERが20倍超（見かけの低PERがピーク利益による）。
- G4: 直近3年の年率希薄化>5%。
- G5: 不適切会計・重大な法令違反の公表から2年以内。

判定時は、独自正常化ケースのレンジ全体が20倍超（下限>20倍）の場合と、上端・追加の深いストレスだけが20倍超の場合を区別する。後者はG3要確認で、前者と同じ確定除外にはしない。G4の年率は分割等を調整した3年間の株数から `(期末株数/3年前株数)^(1/3)-1` で計算し、単年の前年比だけでは確定しない。系列不足による暫定除外は、ゲート該当が確認できた不適格と表示上も分ける。

**合成と順位付け（提案）**
- 適格条件: 持続性スコア≥6.0かつ割安度スコア≥5.0かつ失格ゲートなし。
- 順位付け: 総合 = 0.5×持続性 + 0.5×割安度。同点時は持続性優先（個別割安株の勝率が5割未満というベースレートに対し、クオリティが勝率を上げる実証に基づく）。
- 業種上限: 上位候補のうち同一業種は最大30%（2026年11月のバリューが銀行・商社・資源に集中していることへの対処）。
- 円建て投資家の海外銘柄: 割安度に為替ヘッジコスト相当（年約2.6%、推定）のマージンを要求し、海外銘柄は割安度≥6.0を適格条件とする（国内は≥5.0）。

**2026-11-06時点の目安（市場平均が何点になるか）**: 東証プライム平均（予想PER 15.6倍、PBR 1.67倍、ROE 9.5%、配当利回り2.6%）はV2=1.0、V4=0、V5≈1.0で、EV/EBIT・FCF利回りを平均的な10〜12倍・5%とすると割安度≈4〜4.5点。S&P500平均（予想PER 18.7倍、PBR推定5倍前後）は割安度≈2〜3点。したがって「割安度≥5.0」は市場平均より明確に割安な水準を要求する閾値になる。

### Gaps
- 閾値（EV/EBIT 6/8/10倍、FCF利回り5/7/10%等）は実証文献の十分位・五分位境界を直接参照したものではなく、2026年11月の市場水準（A1）と実務慣行から設定した提案値。バックテストは未実施。
- 金融株の代替指標の配点は実証に基づかない実務提案。
- 日本株・米国株それぞれで、本ルーブリックの上位群の過去リターンを検証したデータはない（コーディネーターがスクリーン結果に適用後、事後検証を推奨）。
