# AI関連46社の最新決算・利益持続性と株価評価

同日の追加判断：[キオクシアを含めた「今買いたい順」上位10社](buy-ranking.md)。株価を13:42取得の別ファイルへ更新し、利益の持続性・価格・資金回収を合わせて順位を付けた。以下の13:07時点の調査・数値は保持する。

調査日：2026年11月6日。株価取得の固定基準は13:07 JST、アジア株の実際の観測値は主に11:46〜12:52現地時間（配信遅延あり）。米国・欧州は11月5日の通常取引観測値。回答時のリアルタイム価格や約定可能価格ではない。各社の正確な時刻は保存データに記載した。

**私の優先候補は、事業の強さと現在利益からの成長を重視するNVIDIA、メモリの価格循環を受け入れるならSK hynix・Micron・Sandisk、日本株では東京エレクトロン・フジクラ。冷却・電源ではVertivを追加候補とする。** Broadcomは引き続き有力だが、当面の利益と顧客の資金負担を重く見る今回はNVIDIAを先に置く。これは主観的な検討優先度で、期待収益率を確率加重した順位ではない。

対象46社のうち、最新公表資料を再確認した会社35社、次回決算待ち10社、原本ホストの確認が限定的な会社1社。決算待ちも既公表の最新資料・日程・取得範囲を確認した区分であり、未発表利益を補完していない。14社について独自の近い年度利益ケースを計算した。旧2028〜29年の276ケースのモデルや本番画面は更新していない。

## 1. 前回から何が変わったか

株価下落が大きい一方、アドバンテスト・Vertiv・Arista・AMD・SMCI等の新決算では売上・利益の伸びが確認できた。すべての企業で足元の需要が崩れたという見方には根拠が不足する。ただし、投資評価損益、納税、増産投資、顧客への信用供与、優先株・CBによる一株利益の違いが重要になっている。

市場全体ではAI投資の資金負担や規制への警戒が株価を押している。報道にある規制懸念を、成立済み政策や個別企業の発注取消と同一視しない。[Reuters配信・11月5日](https://www.investing.com/news/stock-market-news/techstock-rout-accelerates-retreat-from-the-ai-trade-5005205)

- **NVIDIA / Broadcom**：前回から新しい四半期決算はない。株価下落によって当面の利益に対する評価が改善した。NVIDIAの投資評価益を除いた代理利益、BroadcomのSBC・買収償却・顧客信用支援を改めて確認。
- **メモリ**：SK、Samsung、Sandiskの新決算を反映。SKは営業利益と純利益に大差があり、営業外投資損益を見分ける必要がある。Micronの次四半期会社予想とNAND企業のキャッシュ創出は強いが、高利益率を長期固定しない。
- **日本装置・テスト**：東京エレクトロンの通期予想、アドバンテストの上方修正を確認。アドバンテストの金融収益、ASMLの投資評価益をそのまま長期利益へ延長しない。
- **インフラ**：Vertiv・Aristaは実需が強い。フジクラは下落率が大きく現行会社予想との倍率が低下したが、新Q2は未確認。Alphabet / Amazonは利益の伸びだけでなく設備投資後の現金収支を見る。
- **個別事情**：LumentumはMarvell株4.5株への固定交換比率の取引合意があり、単独PERだけで評価しない。Quanta / Wiwynn等はQ3利益・CB分母の確認待ち。SMCIは利益増と営業CF赤字が同時に起きている。

## 2. 公表済みの会社予想で測れる倍率の例

|会社|観測株価|会社通期EPS|株価÷EPS|注意|
|---|---:|---:|---:|---|
|東京エレクトロン|8,217 JPY|381.69 JPY|21.5倍|FY2027/3、10/30会社予想。10/1の1対5分割後|
|フジクラ|2,898 JPY|196.88 JPY|14.7倍|FY2027/3、8/7会社予想。Q2未確認|
|アドバンテスト|27,945 JPY|1,027.08 JPY|27.2倍|FY2027/3、10/28会社予想。評価益を調整した慎重代理EPS969.44なら28.8倍|
|Vertiv|176.73 USD|6.29 USD|28.1倍|CY2026 GAAP会社予想中点。調整EPS7.15との混用を避ける|

出典は各社の[日本装置・材料調査](parts/japan.md)と[インフラ調査](parts/infrastructure.md)。上の比率は会社通期予想の参考値で、下の独自の翌期シナリオ倍率と定義が異なる。ADVの金融収益57bn JPYを全額除外・税率27%で調整した値は、会社の正常EPSでも正確な評価益除外EPSでもない慎重代理。Yahooの会社EPS表示1,025.35円との差は未解消で、ここでは公式会社資料1,027.08円を使う。

## 3. 有力候補14社の利益ケースと株価

**以下は独自の条件付きシナリオで、会社予想・アナリストコンセンサスではない。** 年度が異なるので期間列を確認する。倍率は現在株価を将来の独自EPSで割った値で、現在のTTM PER、正式な予想PER、割引後の適正価格ではない。成長が実現して初めて成立し、発生確率・上下限を示すものでもない。

利益・株数の単位はそれぞれ「10億・現地通貨」「10億株」。SBC・通常の減価償却を費用に残し、主な投資評価益を延長しない。株式分割、ADR、優先株・CBの基準は[各社入力](candidate-inputs.json)と[詳細資料](README.md)に記録。

|会社|対象年度|株価・通貨|独自年間利益（10億）|将来EPSに対する倍率|主な条件・確認点|
|---|---|---:|---:|---:|---|
|NVIDIA|FY2028（暦年2027に近い）|181.60 USD|280.0〜360.0|12.1〜15.9倍|高い成長を要する。既存の利益・製品統合を評価。投資評価益除外|
|Broadcom|FY2027|291.53 USD|60.0〜85.0|17.1〜25.3倍|ASIC・通信とソフト。顧客の信用支援・集中リスク|
|SK hynix|CY2027|1,159,000.00 KRW|200,000.0〜300,000.0|2.7〜4.1倍|HBMとメモリ単価。投資損益を平準化した代理、分母は独自|
|Micron|FY2027|656.39 USD|160.0〜190.0|4.0〜4.8倍|会社Q1ガイド起点。正常化70〜120bnは利益ストレス|
|Sandisk|FY2027|806.43 USD|32.0〜36.0|3.4〜3.9倍|分割前基準。評価益除外後、JV・顧客前受金もCFで点検|
|キオクシアHD|FY2027/3|8,483.00 JPY|5,000.0〜5,400.0|2.5〜2.7倍|先の詳細調査を参照。将来正常化中心3,000bn JPY|
|フジクラ|FY2028/3|2,898.00 JPY|306.8〜425.6|11.3〜15.7倍|ICT高利益率維持。Q2未確認のため決算確認を優先|
|東京エレクトロン|FY2028/3|8,217.00 JPY|794.0〜1,084.2|17.2〜23.5倍|先端ロジック・メモリ投資と営業率29〜33%の仮定|
|アドバンテスト|FY2028/3|27,945.00 JPY|652.8〜881.3|23.0〜31.0倍|評価益を延長しない。テスト需要と営業率48〜54%|
|Vertiv|CY2027|176.73 USD|3.0〜3.8|18.4〜23.5倍|受注の売上化・生産能力増、GAAP費用を残す|
|Arista Networks|CY2027|159.16 USD|5.7〜7.2|28.9〜36.3倍|事業は強いが、この利益幅でも要求成長・倍率が高め|
|TSMC|CY2027|2,140.00 TWD|3,145.0〜3,896.0|14.3〜17.7倍|台湾普通株。先端工程・実装、海外工場費用と地政学|
|Alphabet|CY2027|282.57 USD|132.8〜157.4|23.0〜27.2倍|投資損益を平準化。純利益とFCFの差に注意|
|Super Micro Computer|FY2027|27.08 USD|5.0〜6.5|3.7〜5.4倍|全転換経済分母。営業CF赤字・暫定決算で上位に置かない|

### NVIDIAを先に検討する理由

NVIDIAの直近Q2はGAAP純利益59.688bn USDだが、投資有価証券益7.771bnを含む。GAAP営業利益に通常利息を加え税率18%を置くと、正常化代理の四半期純利益は約52.48bn、単純年換算約209.93bn。直近希薄化株数での代理EPS年率は約8.64ドル、現値181.60ドルに対して約21倍。翌期の280〜360bnと12〜16倍にはさらに増益が必要だが、遠い将来の市場シェア上昇だけへ依存する評価を避けられる。中国規制・ASIC競争・顧客集中・データセンター建設の遅れは残る。[NVIDIA公式決算](https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Announces-Financial-Results-for-Second-Quarter-Fiscal-2027/)

Broadcomもキャッシュ創出とソフト事業が強いが、独自の近年利益60〜85bnでは17〜25倍、慎重利益45〜65bnでは22〜34倍程度。前回2029年モデルが見込むASICの取り分拡大だけで安さを判断せず、当面の利益と顧客の資金負担を重く見るため、今回はNVIDIAを先にする。[Broadcom公式決算](https://investors.broadcom.com/news-releases/news-release-details/broadcom-inc-announces-third-quarter-fiscal-year-2026-financial)

### メモリは最も低倍率だが、価格正常化が共通の論点

SK hynixのQ3営業利益は83.334兆KRW、親会社純利益は39.534兆KRW。差のうち営業外純損失は32.625兆KRWで、内訳の全額をキオクシア投資損と断定しない。投資損益を平準化した近い年の利益代理200〜300兆、将来の慎重ケース100〜170兆を置くと、後者でも参考倍率約4.8〜8.3倍。ただし営業率65〜78%を置く近年ケースは高収益の継続を要する。[SK公式](https://news.skhynix.com/en/q3-2026-business-results/)、[SEC財務](https://www.sec.gov/Archives/edgar/data/2120882/000119312526434994/d162547d6k.htm)

SandiskのQ1は純利益8.101bn USD、投資益を平準化しSBCを残す独自代理7.485bn。会社調整FCF5.696bnはJV資金と顧客前受金等の調整も確認した。今後の利益32〜36bn、価格正常化後15〜23bnの仮定では後者でも約5.3〜8.3倍。11/20の分割後取引開始より前なので、今回806.43ドルとEPS・株数はすべて分割前。[Sandisk公式](https://investor.sandisk.com/news-releases/news-release-details/sandisk-reports-fiscal-first-quarter-2027-financial-results)

Micronも会社Q1 EPSと現金創出は強く、慎重利益70〜120bnで参考倍率約6.3〜10.9倍。ただしこの利益幅は高い足元利益の何割が残るかを置くストレスで、独立したメモリ価格予測ではない。キオクシア・SK・Micron・Sandiskに分けても、メモリ価格循環への偏りは残る。個々の低倍率を独立した四つの安全余裕として加算しない。

### 日本株では東京エレクトロンとフジクラを優先

東京エレクトロンは10/30に通期純利益865bn JPY、EPS381.69円を公表。現行会社予想で約21.5倍、翌期独自794〜1,084bnで約17〜23倍。全社利益の伸びと価格評価の釣合いを評価する。アドバンテストも上方修正は強いが、評価益を除いた代理利益と慎重な循環ケースでは依然高めの倍率となり、会社予想PERだけを比べない。[東京エレクトロン公式](https://www.tel.com/ir/library/report/i61j9u00000000gf-att/fy27q2tanshin-e.pdf)

フジクラは10/16から約36%下落し、Q1公表時点の通期EPSに対して約14.7倍。独自の正常化利益242〜328bn JPYでも約14.6〜19.9倍となる。ICTの高利益率、増産費用・償却、為替が重要で、新しいQ2を未確認のため確認優先度が高い。下落率の大きさだけで買い判断を強めない。[会社Q1説明資料](https://ssl4.eir-parts.net/doc/5803/ir_material_for_fiscal_ym/210022/00.pdf)

### インフラではVertiv、Aristaは価格との釣合いを慎重に

VertivはQ3増収61%、GAAP EPS1.95、通期GAAP EPS予想中点6.29へ上方。独自CY2027純利益3.0〜3.8bn USDで約18〜23倍になる。AristaはQ3増収58.5%と強いが、投資益を延長しない独自翌年利益で約29〜36倍。事業の良さだけでは両社を同じ価格魅力と評価しない。[インフラの根拠資料](parts/infrastructure.md)

### 安く見えても確認を待つ会社

QuantaはQ3月次売上の伸びを確認したが利益決算前。独自CY2026純利益120〜160bn TWD、CY2027 150〜220bnは条件付きで、最新CB残高と転換を照合できるまで新たな厳密EPS順位は保留する。Wiwynnも同様にQ3利益・回収・分母が確認点。

SMCIのQ1は連結純利益1.594bn USDに対し、希薄化普通株EPSの分子は1.308bn。全転換を仮定した経済分母0.90〜1.0bnで独自利益5〜6.5bnを割ると低い倍率になるが、営業CFは−0.434bn、在庫15.05bn、売掛9.69bn。利益が現金に変わるかを優先し、現時点で上位に置かない。将来の優先株参加配分と全転換分母を二重に減額せず、現行GAAP EPSと定義を分けた。[計算・資金収支の確認](parts/compute.md)

LumentumはMarvell株4.5株への固定交換比率、完了見込み2028年上半期の条件付き取引。MRVL価格と完了リスクを確認せず単独利益倍率で順位を付けない。GE Vernovaの持分売却益、Alphabetの投資評価損、Siemens Energyの非支配利益も、見出し純利益だけの比較から外す。

## 4. 46社の確認一覧

価格の変化は今回取得した分割調整後10/16日次Closeから各観測価格まで。配当込み収益ではない。時刻の+09:00/+08:00等は現地時間帯。決算欄のリンクは確認した原資料、要点の全文・数値・単位・会計基準は[全社JSON](review.json)と[CSV](review.csv)、各分担資料で参照できる。

|会社・コード|株価・通貨|価格観測（現地）|10/16比|最新決算公表日・状態|今回の要点|
|---|---:|---|---:|---|---|
|信越化学（4063.T）|5,319.00 JPY|11-06T12:52 +09:00|-11.0%|[2026-10-27](https://www.shinetsu.co.jp/wp-content/uploads/2026/07/20261027_con_E.pdf)・公表資料確認|H1営業利益+15.6%、電子材料OP+28%。7月の通期純利益525bn/EPS286円は据置。AI材料好調をPVC全体へ延長しない。|
|SUMCO（3436.T）|1,782.50 JPY|11-06T12:52 +09:00|-34.1%|[2026-08-06](https://ssl4.eir-parts.net/doc/3436/tdnet/2864809/00.pdf)・次回決算待ち|11/6時点でQ3未公表。会社8/6予想はQ3単独営業損益ほぼ均衡、9M純損失12.8bn。11/11予定を外部カレンダーで確認。|
|GlobalWafers（6488.TWO）|508.00 TWD|11-06T11:46 +08:00|-43.7%|[2026-11-03](https://www.sas-globalwafers.com/en/globalwafers-reports-q3-2026-results/)・公表資料確認|Q3利益/EPS公表へ更新。Q2投資評価益の高い比較基準と伊8インチ工場火災の影響。11/3にMicron向け最大US$500m・10年CB案（年0.5%）を承認。|
|Siltronic（WAF.DE）|50.20 EUR|11-05T17:35 +01:00|-23.8%|[2026-11-04](https://www.siltronic.com/en/press/press-releases/siltronic-slightly-raises-sales-guidance-for-2026-higher-demand-drives-volume-development-in-q3-2026.html)・公表資料確認|売上見通しを前年並みへ上方、EBITDA率22〜24%へ絞る。数量は回復したが新設償却で9M EBIT赤字。|
|東京エレクトロン（8035.T）|8,217.00 JPY|11-06T12:52 +09:00|-22.7%|[2026-10-30](https://www.tel.com/ir/library/report/i61j9u00000000gf-att/fy27q2tanshin-e.pdf)・公表資料確認|前回はH1予想のみ。10/30に通期NI865bn/EPS381.69円を公表、H1も7月予想349bnを上回る。|
|Lam Research（LRCX）|185.20 USD|11-05T16:00 -05:00|-29.8%|[2026-10-21](https://investor.lamresearch.com/2026-10-21-Lam-Research-Corporation-Reports-Financial-Results-for-the-Quarter-Ended-September-27%2C-2026)・公表資料確認|9月期売上+22%QoQ、GAAP EPS2.19、12月期売上中心8.6bn/EPS2.33へ。AI装置需要が強い。|
|ASML（ASML）|1,356.65 USD|11-05T16:00 -05:00|-17.4%|[2026-10-14](https://www.investor.asml.com/news-releases/news-release-details/asml-reports-eu11.7-billion-total-net-sales-and-eu5.0-billion-net-income-q3-2026)・公表資料確認|10/18以降の新決算ではなく10/14Q3を再確認。2027〜28供給不足見込み、28年能力増検討。Q3純利益に税前EUR509.7m評価益が含まれる。|
|NVIDIA（NVDA）|181.60 USD|11-05T16:00 -05:00|-15.2%|[2026-08-26](https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Announces-Financial-Results-for-Second-Quarter-Fiscal-2027/)・公表資料確認|前回以降の新四半期は未確認。Q2 GAAP利益を押し上げた株式評価益を除き、Q3会社ガイドで本業を再評価する。|
|AMD（AMD）|404.40 USD|11-05T16:00 -05:00|-23.5%|[2026-11-03](https://ir.amd.com/news-events/press-releases/detail/1303/amd-reports-third-quarter-2026-financial-results)・公表資料確認|Q2売上11.536→Q3 13.377、Q4売上会社予想17。DC伸長が加速した一方、GAAPと調整後EPSに大きな差。|
|Broadcom（AVGO）|291.53 USD|11-05T16:00 -05:00|-11.3%|[2026-09-02](https://investors.broadcom.com/news-releases/news-release-details/broadcom-inc-announces-third-quarter-fiscal-year-2026-financial)・公表資料確認|新四半期は未確認。AI ASIC/ネットワークの急成長とソフトウェアの高利益を維持する会社見通しを再確認。|
|TSMC（2330.TW）|2,140.00 TWD|11-06T11:46 +08:00|-11.6%|[2026-10-15](https://www.sec.gov/Archives/edgar/data/1046179/000104617926000726/a3q26e_withguidancexfinal.htm)・公表資料確認|10/18以降の新四半期決算はない。10月月次売上は11/10予定。Q3とQ4会社見通しを再確認し、株価下落を評価へ反映。|
|ASE Technology（3711.TW）|522.00 TWD|11-06T11:47 +08:00|-22.2%|[2026-10-29](https://www.sec.gov/Archives/edgar/data/1122411/000095010326016324/dp255760_6k.htm)・公表資料確認|前回はQ3売上速報のみ。正式利益はNI26.996bn、OP33.142bnと強い。ATM営業利益率20.0%（Q2 15.7%）、営業外差引は損失で前四半期の為替・投資益依存が低下。|
|味の素（2802.T）|4,292.00 JPY|11-06T12:51 +09:00|-18.7%|[2026-08-06](https://www.ajinomoto.co.jp/company/en/ir/event/presentation/main/011111113/teaserItems1/01/linkList/0/link/FY26Q1_Tanshin_E.pdf)・次回決算待ち|11/6時点Q2決算未発表、11/9予定。ABF強いが全社は食品・バイオ等を含む。|
|イビデン（4062.T）|6,068.00 JPY|11-06T12:52 +09:00|-37.9%|[2026-10-29](https://www.ibiden.com/ir/library/statement/items/tannshinn2026Q2.pdf)・公表資料確認|通期NI84→89bn、EPS149.68→157.17円へ上方。10/29の追加150bn投資はFY2029下期立上げ、利益寄与FY2030以降の説明。|
|Unimicron（3037.TW）|726.00 TWD|11-06T11:47 +08:00|-33.4%|[2026-10-27](https://financialfilings.com/filings/unimicron-3037/earnings-release/2026/74787084/)・限定確認|9M会社開示を転載本文で確認。Q3売上速報52.65bnから正式9M利益まで更新。ただし原ホスト財務報告を直接取得できず確認限定。|
|ディスコ（6146.T）|40,330.00 JPY|11-06T12:52 +09:00|-25.1%|[2026-10-22](https://www.disco.co.jp/jp/ir/library/doc/fr/fr20261022.pdf)・公表資料確認|前回の個別出荷速報からH1正式決算へ更新。H1NI+43.7%。通期ではなく9Mまでの会社予想に注意。|
|アドバンテスト（6857.T）|27,945.00 JPY|11-06T12:52 +09:00|-19.1%|[2026-10-28](https://www.advantest.com/document/en/investors/ir-library/result/E_FR_FY2026_2Q.pdf)・公表資料確認|通期NI660→741.5bn/EPS1027.08へ上方。AI半導体数量・テスト複雑化を反映。ただしH1金融収益約57bnは主に投資評価益。|
|Teradyne（TER）|212.74 USD|11-05T16:00 -05:00|-34.5%|[2026-10-27](https://investors.teradyne.com/news-events/press-releases/detail/455/teradyne-reports-third-quarter-2026-results)・公表資料確認|Q3は売上ガイダンス上限を超え、前年比70%増。Q4売上1.25〜1.35bnでQ3付近、GAAP EPS1.88〜2.18。|
|SK hynix（000660.KS）|1,159,000.00 KRW|11-06T12:47 +09:00|-8.9%|[2026-10-28](https://news.skhynix.com/en/q3-2026-business-results/)・公表資料確認|Q2投資益を含むNI93.82兆からQ3親会社NI39.53兆へ低下したが、OPは60.54→83.33兆へ増加。営業外損益が逆方向。|
|Micron（MU）|656.39 USD|11-05T16:00 -05:00|-25.3%|[2026-09-30](https://investors.micron.com/news/press-release/2026/Micron-Technology-Inc--Reports-Record-Fiscal-Fourth-Quarter-and-Full-Year-2026-Results/default.aspx)・公表資料確認|前回から新しい四半期決算を確認せず。前回の高利益・FQ1強気会社見通しを一次資料で再確認。|
|Samsung Electronics（005930.KS）|189,900.00 KRW|11-06T12:47 +09:00|-11.9%|[2026-10-29](https://news.samsung.com/global/samsung-electronics-announces-third-quarter-2026-results)・公表資料確認|10/8概算から10/29確報説明資料へ更新。メモリ主導のOP増、一方DX部門は赤字。|
|キオクシアHD（285A.T）|8,483.00 JPY|11-06T12:52 +09:00|-36.6%|[2026-10-30](https://ssl4.eir-parts.net/doc/285A/tdnet/2902676/00.pdf)・公表資料確認|10/30 Q2とQ3見通しを反映。成長は一服するがQ4数量増を会社は予想。会社通期予想はない。|
|Sandisk（SNDK）|806.43 USD|11-05T16:00 -05:00|-37.9%|[2026-10-29](https://investor.sandisk.com/news-releases/news-release-details/sandisk-reports-fiscal-first-quarter-2027-financial-results)・公表資料確認|Q1確報でDC売上4.802bn(+61%QoQ)、利益・現金創出を確認。調整FCFは前受金とJV投資影響を除いて5.696bn。|
|富士通（6702.T）|3,202.00 JPY|11-06T12:52 +09:00|-27.6%|[2026-10-29](https://resources.global.fujitsu/prir/2026/10/2026Q2-Financial-Results-en.pdf)・公表資料確認|H1 GAAP純利益は前年売却等の反動で減少、調整後利益はほぼ横ばい。通期310bnは据置。|
|NEC（6701.T）|4,393.00 JPY|11-06T12:51 +09:00|-18.5%|[2026-10-28](https://group.nec/assets/global/en/about/ir/library/pdf/202610/2810-01-01.pdf)・公表資料確認|通期売上3540→3740bn、非GAAP利益290→310bnへ上方修正。CSG47社の新規連結を含む。|
|Dell Technologies（DELL）|316.91 USD|11-05T16:04 -05:00|-29.8%|[2026-09-01](https://investors.delltechnologies.com/sec-filings/all-sec-filings/content/0001571996-26-000039/exhibit991earnings8kq2fy27.htm)・次回決算待ち|新四半期は未確認。9/1会社ガイドとAI受注/バックログを再確認。|
|Hewlett Packard Enterprise（HPE）|44.16 USD|11-05T16:04 -05:00|-19.9%|[2026-09-02](https://www.hpe.com/us/en/newsroom/press-release/2026/09/hpe-reports-fiscal-2026-third-quarter-results.html)・次回決算待ち|最新四半期は前回と同じ。IRで11/23のQ4決算予定を確認。|
|Super Micro Computer（SMCI）|27.08 USD|11-05T16:00 -05:00|-14.4%|[2026-11-03](https://ir.supermicro.com/news/news-details/2026/Supermicro-Announces-First-Quarter-of-Fiscal-Year-2027-Financial-Results/default.aspx)・公表資料確認|Q1売上19.946bnで旧予想14.5〜15.5bnを大幅上回り、FY売上65〜72→72〜82bn。利益改善も営業CFは赤字。|
|Lenovo（0992.HK）|18.20 HKD|11-06T11:51 +08:00|-35.1%|[2026-08-13](https://news.lenovo.com/pressroom/press-releases/q1-fy-2026-27/)・次回決算待ち|新決算は未確認。Hybrid AI売上拡大と報告赤字（ワラント評価損）の併存を再点検。|
|Quanta Computer（2382.TW）|290.00 TWD|11-06T11:47 +08:00|-9.9%|[2026-08-13](https://www.quantatw.com/quanta/english/allnews/allnews_open.aspx?CASENO=NEWS003819)・次回決算待ち|公式IRには2Q26まで。Q3売上は大きいが利益率・CB残高の確認待ち。|
|Wiwynn（6669.TW）|1,555.00 TWD|11-06T11:46 +08:00|-15.7%|[2026-08-07](https://www.wiwynn.com/investors)・次回決算待ち|9月/Q3売上が強い。新しい利益確報は未確認、代採購への移行による粗利率表示の押上げにも注意。|
|Hon Hai Precision（2317.TW）|224.00 TWD|11-06T11:47 +08:00|-8.2%|[2026-08-12](https://www.honhai.com/zh-tw/investor-relations/investor-relations-activities/event-calendar)・次回決算待ち|Q3利益公表前。10月月次の増収報道は見つかったが原資料の金額を今回照合できず、利益入力に採用しない。|
|Arista Networks（ANET）|159.16 USD|11-05T16:00 -05:00|-10.1%|[2026-11-03](https://investors.arista.com/Communications/Press-Releases-and-Events/Press-Release-Detail/2026/Arista-Networks-Inc--Reports-Third-Quarter-2026-Financial-Results/default.aspx)・公表資料確認|売上+58.5%/前四半期+20.5%、Q4売上中点3.95bnへ増勢。GAAP EPSが調整EPSを上回るのは投資益/税項目が関係、GAAP単純年換算にも注意。|
|フジクラ（5803.T）|2,898.00 JPY|11-06T12:52 +09:00|-35.6%|[2026-08-07](https://ssl4.eir-parts.net/doc/5803/ir_material_for_fiscal_ym/210022/00.pdf)・公表資料確認|前回10/18の最新Q1入力と業績予想は同じ。今回公式Q1説明資料で再確認。Q2実績は未確認。公式IRカレンダーは画像のため日付を一次資料から抽出できず、11/10予定の二次情報だけでは確定扱いしない。|
|Coherent（COHR）|169.76 USD|11-05T16:00 -05:00|-27.1%|[2026-11-04](https://ir.coherent.com/news-releases/news-release-details/coherent-corp-reports-first-quarter-fiscal-2027-results)・公表資料確認|Q1売上+49.9%、Q2売上ガイド2.55–2.75bnへ増勢。GAAP利益には税便益があり、EPS1.90×4を正常利益扱いしない。|
|Lumentum（LITE）|509.70 USD|11-05T16:00 -05:00|-38.2%|[2026-11-02](https://investor.lumentum.com/financial-news-releases/news-details/2026/Lumentum-Announces-First-Quarter-of-Fiscal-Year-2027-Financial-Results/default.aspx)・公表資料確認|業績急拡大に加え11/2 Marvellとの全株式交換合意。LITE単独利益に基づく割安順位を取引後まで延長しない。|
|日立製作所（6501.T）|4,523.00 JPY|11-06T12:52 +09:00|-21.6%|[2026-10-28](https://www.hitachi.com/content/dam/hitachi/global/en/press/files/2026/10/261028/2026_2Q.pdf)・公表資料確認|売上+300bn・調整EBITA+40bn・親会社純利益+20bnへ上方。上期純利益は前年一時益反動で減益でも、本業調整営業利益は+26.6%。|
|Eaton（ETN）|327.02 USD|11-05T16:00 -05:00|-16.4%|[2026-11-03](https://www.eaton.com/us/en-us/company/news-insights/news-releases/2026/eaton-reports-record-third-quarter-2026-results.html)・公表資料確認|売上28%増（オーガニック19%）、調整EPS中点13.75へ上方。GAAP EPS中点10.44は旧中点10.46からほぼ横ばい。調整値だけで利益上方と断定しない。|
|Vertiv（VRT）|176.73 USD|11-05T16:00 -05:00|-14.4%|[2026-10-28](https://investors.vertiv.com/news/news-details/2026/Vertiv-Reports-Strong-Third-Quarter-2026-with-Net-Sales-Growth-of-61-Organic-Orders-Growth-over-100-and-Diluted-EPS-Growth-of-91-Adjusted-Diluted-EPS-Growth-of-78-Raises-Full-Year-2026-Guidance-Across-All-Key-Metrics/default.aspx)・公表資料確認|売上+61%（有機55%）/有機受注100%超増、通期売上中点14.65bnへ上方、調整EPS中点6.70→7.15。|
|ダイキン工業（6367.T）|21,645.00 JPY|11-06T12:52 +09:00|+1.4%|[2026-11-05](https://www.daikin.co.jp/-/media/Project/Daikin/daikin_co_jp/investor/data/kessan/2027/2Q_brief_report_jp-pdf.pdf?hash=5A9AF697633DD7C4DE197714E92279E1&rev=6249d1ebc5cd4bc4924559edd231cd23)・公表資料確認|売上5.6%・営業利益4.4%・純利益0.7%上方。純利益の増勢はAI専業より緩く、全社空調の需要が支配。EPS修正は株数変化も含む。|
|Amazon（AMZN）|260.21 USD|11-05T16:00 -05:00|+4.1%|[2026-10-29](https://ir.aboutamazon.com/files/doc_earnings/2026/q3/earnings-result/AMZN-Q3-2026-Earnings-Release.pdf)・公表資料確認|AWS成長39.3%・OP17.8bnと加速。Q2純利益62.6bnの投資評価益からQ3純利益20.7bnへ変化、売上増でも利益単純比較は不適切。TTM FCFは−42.4bnへ悪化。|
|Alphabet（GOOGL）|282.57 USD|11-05T16:00 -05:00|-17.0%|[2026-10-28](https://s206.q4cdn.com/479360582/files/doc_news/2026/Oct/28/attachments/2026q3-alphabet-earnings-release.pdf)・公表資料確認|Cloud売上+103%、本業OP+30%。Q3は投資評価損で純益減、9M純益200.855bnは過去評価益の影響が大きい。Q3資金調達は普通株12.37bn・社債約28.7bn、設備投資後FCF赤字。|
|Apple（AAPL）|344.17 USD|11-05T16:00 -05:00|+0.2%|[2026-11-02](https://www.apple.com/newsroom/2026/11/apple-reports-fourth-quarter-results/)・公表資料確認|FY26通期を更新、売上約479bn/純利益132.175bn/EPS8.98。Q4EPSには関税還付0.05押上げ、旧Q3の還付0.11と合わせて恒常利益化しない。|
|三菱重工業（7011.T）|2,852.50 JPY|11-06T12:52 +09:00|-24.9%|[2026-08-04](https://www.mhi.com/finance/library/result)・次回決算待ち|11/6 13:30予定のQ2発表直前。カットオフ時点でQ1/旧通期予想を維持、未公表Q2を織り込まない。|
|GE Vernova（GEV）|770.51 USD|11-05T16:00 -05:00|-16.4%|[2026-10-28](https://www.sec.gov/Archives/edgar/data/1996810/000199681026000162/gevpressrelease3q26.htm)・公表資料確認|受注残197bnへ増、売上/調整EBITDA/FCF予想上方。Trench Group9bn買収合意（2027年後半見込み）。9M純利益は持分取得売却益で大きく膨らむ。|
|Siemens Energy（ENR.DE）|113.84 EUR|11-05T17:39 +01:00|-15.7%|[2026-08-05](https://assets.siemens-energy.com/dam/30018eed-275d-4e73-811e-b49d004cdc3d/2026-08-05-Earnings_Release_Q3_FY26_EN-pdf_Original%20file.pdf)・次回決算待ち|Q4は11/11予定で未発表。9/30 pre-closeを確認したがQ4実績ではない。通期4bnは非支配を含むNet income、親会社EPSへ直接割らない。|

## 5. 調査の限界と再現

- 今回は最新決算・会社見通しを再確認するスクリーニングと、14社の条件付き利益試算。46社すべてを同じ精度のDCFや通期コンセンサスで再評価したものではない。
- 一次情報中心だがUnimicronは原ホスト未取得で転載資料を含む。最新データを取得できない箇所は欠損・限定確認のまま残す。
- 次回決算待ちの10社については、未発表利益を月次売上や報道から確報扱いにしない。三菱重工の11/6 13:30予定発表は今回の固定基準後なので含めない。
- 正常化ケースは企業間で同じ景気の底を意味せず、確率を付けた予想ではない。純利益を配当可能な現金とみなさず、SBC・設備投資・運転資本・税・CBを別に点検する。
- 株価は全46社取得できたが取引時点は一致しない。欧州2社の日次履歴は11/4までだったため、現値には11/5の市場観測値を使う。Yahoo側の履歴を推測で補完しない。
- 通貨・分割・ADR・株数基準を合わせて計算。ASMLの参考的な正常化Q3 EPS年換算47.29EURを1356.65USDと比べる際は、取得EUR/USD1.1198を使い約25.6倍とする。これは会社通期予想PERではなく、株式・為替の観測時刻も異なる。
- 売買、commit、push、外部公開、本番画面の更新は行っていない。X API、有料API、認証情報は使用していない。

保存入力からの再現は[README](README.md)。前回の[10/18ランキング](../../ai-valuation-ranking/2026-10-18/report.md)は当時の見解として保持する。
