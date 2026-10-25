# AIサプライチェーン46社：2028〜2029年利益・EPSと割安度

確認2026-10-18 JST、株価は全46社とも2026-10-16通常取引終値。将来数値はすべて**独自の条件付きシナリオ**であり、会社予想・コンセンサス・発生確率付き予想ではない。[前提・再現方法](README.md)

## 今回の判断

基準ケースの計算価格余地ではSK hynix・Broadcom・Wiwynn・Quanta・SMCIが上位となった。先の8社だけの比較から対象を広げた結果であり、NVIDIAよりこれらの投資確度が高いという意味ではない。台湾ODMは数量・製品構成と薄利の維持、メモリは価格とコスト、Broadcomは取り分拡大、SMCIは営業CF・希薄化・統制リスクが成立条件となる。

**10/18追補訂正：** 初回公開値の台湾2社には既存転換社債の潜在株の織込み不足があった。売上・利益率・純利益・株価を変えず、保守的な経済分母を再設定した。Wiwynnの2029基準EPSは244.00→218.65TWD、Quantaは47.27→45.30TWD。Wiwynnの最新残存元本等を確定できていないため、現在発行株＋両CB全元本潜在株の上限に将来株数増を加える。既転換分の重複を含み得る保守的仮定で、正確な実株数・GAAP希薄化EPSではない。金融費用は加戻さない。[上位5社の詳しい分析・買いたい順](top-five-review.md) · [初回公開値の保存](revisions/initial-published/ranking.json)。

SMCIは最新の監査済み10-Kを確認したうえで、優先株の最大転換と既存CBを含む約8.875億株に将来SBCを加え、2029基準9.8億株へ分母を修正した。EPSは5.50ドル。金融費用は残した保守的経済EPSであり、厳密なGAAP希薄化後EPS予想ではない。低確度の試算として表示する。古い8月速報の「未監査」を現在状態として扱わない。

上位銘柄も弱気ケースでは計算価格が現値を大きく下回る。単一の基準順位だけで安全余裕を断定せず、ケース変更と各社の前提を確認する。NVIDIAの取り分固定・Broadcomの取り分固定による判定変化、キオクシアの途中CF評価の限界も引き継いでいる。

## 比較の方法

先の[8社詳細モデル](../../ai-forward-valuation/2026-10-18/report.md)に、残る38社の事業別モデルを追加した。全46社・2年・3ケースで276ケース。市場/工程需要・事業売上・数量/ASP・シェア/取り分・採算・費用・税・希薄化後普通株数から利益をつなぐ。開示のないAI専用シェアを実測値として作らず、事業売上を起点に校正したケースではその限界を明記する。

広義AIインフラ年間支出は2026年校正1兆ドル、2028年の弱/基準/強が1.0/1.4/1.9兆ドル、2029年が0.95/1.7/2.5兆ドル。全社売上へ同じ倍率を掛けるのではなく、AIに感応する事業や数量・納入能力を通じて反映した。クラウドは利用率・価格、発電は受注の納入、一般消費・非AI事業は別の仮定で計算する。

一時評価益・税便益等を将来に延長せず、SBC（株式報酬）・通常償却・R&Dを費用に残す。2028/2029は暦年相当の年間水準で、会計年度を厳密にそろえた四半期積上げではない。基準ケースは保守的な中立利益とは限らず、企業ごとに仮定の強さも異なる。

```text
将来利益に対する倍率 = 現在株価 ÷ 独自の将来EPS
条件付き計算価格 = 将来EPS × 想定終点PER ÷ 1.12^残存年数
価格余地 = 条件付き計算価格 ÷ 現在株価 − 1
```

年12%は比較用の要求リターンの仮定。配当・税金・将来為替を含まない。完全なDCFや確定した買い価格ではなく、途中の余剰現金・株主還元・投資負担の差を完全に評価していない。特にメモリの高利益から残る現金には別評価が必要。想定PERも独自仮定であり、それを変えれば順位は変わる。

**46社すべてを分析し、順位比較は45社。Eatonだけは残存会社のEPSを試算し、Mobility分離株価値を未評価のため参考扱いとした。** 赤字ケースは計算価格を算出不能とし、価値ゼロとは扱わない。

## 基準ケース：計算上の割安度順

「通常純利益」は一時益等を除いた想定株主利益で、景気循環を通じた中立利益ではない。純利益のbnは各通貨の10億。EPSと株価は各行の同じ通貨・分割後普通株基準。

|順|企業|10/16株価|2028→2029通常純利益（bn）|2028→2029 EPS|現値÷29EPS|29想定PER|12%条件価格|現値比余地|
|---|---|---:|---:|---:|---:|---:|---:|---:|
|1|SK hynix (000660.KS)|1,272,000 KRW|166,349.58→184,734.53 KRW|234,295 KRW→262,035 KRW|4.9倍|11倍|2,003,654 KRW|+58%|
|2|Broadcom (AVGO)|328.75 USD|114.58→145.45 USD|22.69 USD→28.52 USD|11.5倍|25倍|495.63 USD|+51%|
|3|Wiwynn (6669.TW)|1,845.00 TWD|110.83→141.67 TWD|173.11 TWD→218.65 TWD|8.4倍|18倍|2,735.84 TWD|+48%|
|4|Quanta Computer (2382.TW)|322.00 TWD|165.43→201.25 TWD|37.68 TWD→45.30 TWD|7.1倍|15倍|472.32 TWD|+47%|
|5|Super Micro Computer (SMCI)|31.63 USD|4.18→5.39 USD|4.40 USD→5.50 USD|5.7倍|12倍|45.90 USD|+45%|
|6|Samsung Electronics (005930.KS)|215,500 KRW|204,270.47→206,839.68 KRW|30,717 KRW→31,104 KRW|6.9倍|12倍|259,457 KRW|+20%|
|7|NVIDIA (NVDA)|214.13 USD|339.09→353.72 USD|14.07 USD→14.74 USD|14.5倍|25倍|256.13 USD|+20%|
|8|TSMC (2330.TW)|2,420.00 TWD|114.48→134.81 USD|142.78 TWD→168.14 TWD|14.4倍|22倍|2,571.39 TWD|+6%|
|9|フジクラ (5803.T)|4,503 JPY|395.08→467.55 JPY|238 JPY→282 JPY|16.0倍|24倍|4,699 JPY|+4%|
|10|Hon Hai Precision (2317.TW)|244.00 TWD|333.19→401.54 TWD|23.11 TWD→27.52 TWD|8.9倍|13倍|248.73 TWD|+2%|
|11|信越化学 (4063.T)|5,978 JPY|598.59→644.24 JPY|325 JPY→348 JPY|17.2倍|24倍|5,810 JPY|-3%|
|12|ASML (ASML)|1,641.52 USD|21.99→26.84 EUR|64.05 USD→77.96 USD|21.1倍|28倍|1,517.33 USD|-8%|
|13|ディスコ (6146.T)|53,850 JPY|197.65→229.37 JPY|1,813 JPY→2,095 JPY|25.7倍|34倍|49,507 JPY|-8%|
|14|Siemens Energy (ENR.DE)|134.98 EUR|5.27→6.92 EUR|6.16 EUR→8.10 EUR|16.7倍|22倍|123.82 EUR|-8%|
|15|Micron (MU)|878.84 USD|106.13→111.87 USD|89.94 USD→94.01 USD|9.3倍|12倍|784.21 USD|-11%|
|16|ダイキン工業 (6367.T)|21,345 JPY|333.96→374.81 JPY|1,193 JPY→1,339 JPY|15.9倍|20倍|18,610 JPY|-13%|
|17|Amazon (AMZN)|250.00 USD|109.63→134.67 USD|9.86 USD→12.00 USD|20.8倍|26倍|216.93 USD|-13%|
|18|キオクシアHD (285A.T)|13,375 JPY|2,023.79→2,254.91 JPY|1,242 JPY→1,375 JPY|9.7倍|12倍|11,469 JPY|-14%|
|19|東京エレクトロン (8035.T)|10,630 JPY|1,024.58→1,197.92 JPY|449 JPY→523 JPY|20.3倍|25倍|9,091 JPY|-14%|
|20|日立製作所 (6501.T)|5,770 JPY|1,180.26→1,360.91 JPY|267 JPY→311 JPY|18.6倍|22倍|4,752 JPY|-18%|
|21|Dell Technologies (DELL)|451.71 USD|19.08→22.42 USD|29.81 USD→35.58 USD|12.7倍|15倍|371.01 USD|-18%|
|22|Teradyne (TER)|325.00 USD|2.03→2.39 USD|12.68 USD→14.76 USD|22.0倍|26倍|266.69 USD|-18%|
|23|SUMCO (3436.T)|2,703 JPY|56.79→62.32 JPY|161 JPY→176 JPY|15.4倍|18倍|2,196 JPY|-19%|
|24|Hewlett Packard Enterprise (HPE)|55.13 USD|5.72→6.77 USD|3.87 USD→4.51 USD|12.2倍|14倍|43.90 USD|-20%|
|25|Vertiv (VRT)|206.42 USD|3.11→3.75 USD|7.77 USD→9.34 USD|22.1倍|25倍|162.24 USD|-21%|
|26|アドバンテスト (6857.T)|34,530 JPY|843.25→1,036.71 JPY|1,140 JPY→1,392 JPY|24.8倍|28倍|27,085 JPY|-22%|
|27|Lam Research (LRCX)|263.94 USD|12.44→14.70 USD|9.72 USD→11.40 USD|23.2倍|26倍|206.02 USD|-22%|
|28|三菱重工 (7011.T)|3,796 JPY|495.22→605.69 JPY|147 JPY→180 JPY|21.1倍|22倍|2,757 JPY|-27%|
|29|NEC (6701.T)|5,390 JPY|324.44→343.21 JPY|240 JPY→252 JPY|21.4倍|22倍|3,859 JPY|-28%|
|30|富士通 (6702.T)|4,423 JPY|352.55→377.25 JPY|205 JPY→221 JPY|20.0倍|20倍|3,067 JPY|-31%|
|31|Siltronic (WAF.DE)|65.90 EUR|0.12→0.14 EUR|3.71 EUR→4.05 EUR|16.3倍|16倍|45.03 EUR|-32%|
|32|味の素 (2802.T)|5,280 JPY|156.32→172.47 JPY|163 JPY→179 JPY|29.5倍|28倍|3,479 JPY|-34%|
|33|AMD (AMD)|528.75 USD|19.44→31.74 USD|10.51 USD→16.62 USD|31.8倍|30倍|346.57 USD|-34%|
|34|Lenovo Group (0992.HK)|28.06 HKD|4.18→4.92 USD|2.01 HKD→2.35 HKD|11.9倍|11倍|18.00 HKD|-36%|
|35|Coherent (COHR)|232.90 USD|1.43→1.94 USD|6.75 USD→8.93 USD|26.1倍|24倍|148.96 USD|-36%|
|36|Alphabet (GOOGL)|340.59 USD|147.46→172.25 USD|11.75 USD→13.62 USD|25.0倍|23倍|217.70 USD|-36%|
|37|Apple (AAPL)|343.46 USD|141.00→158.15 USD|10.00 USD→11.46 USD|30.0倍|26倍|207.13 USD|-40%|
|38|GE Vernova (GEV)|921.20 USD|6.29→8.23 USD|23.83 USD→31.64 USD|29.1倍|25倍|549.93 USD|-40%|
|39|ASE Technology (3711.TW)|671.00 TWD|120.11→137.46 TWD|26.11 TWD→29.56 TWD|22.7倍|19倍|390.44 TWD|-42%|
|40|Arista Networks (ANET)|176.98 USD|5.91→6.73 USD|4.54 USD→5.14 USD|34.5倍|28倍|99.98 USD|-44%|
|41|Sandisk (SNDK)|1,299.30 USD|12.93→13.86 USD|80.81 USD→85.53 USD|15.2倍|12倍|713.47 USD|-45%|
|42|イビデン (4062.T)|9,764 JPY|132.73→157.08 JPY|221 JPY→259 JPY|37.7倍|24倍|4,325 JPY|-56%|
|43|Unimicron (3037.TW)|1,090.00 TWD|42.58→50.35 TWD|26.61 TWD→30.89 TWD|35.3倍|22倍|472.38 TWD|-57%|
|44|GlobalWafers (6488.TWO)|902.00 TWD|14.98→16.34 TWD|27.99 TWD→30.26 TWD|29.8倍|18倍|378.69 TWD|-58%|
|45|Lumentum (LITE)|824.13 USD|1.62→2.09 USD|14.98 USD→18.52 USD|44.5倍|25倍|321.85 USD|-61%|
|参考|Eaton (ETN)|391.25 USD|5.16→6.27 USD|13.37 USD→16.37 USD|23.9倍|24倍|273.15 USD|比較対象外|

**この数値順は、リスクや予測確率をそろえた投資推奨順位ではない。** 強い取り分拡大や高い利益率を置いた会社が上位になることもある。8社詳細モデルと追加38社では分析の粒度も異なる。UIでは年・ケース・要求年率を変更し、各社の成立条件と出典を確認できる。

## 弱気・基準・強気による幅

市場・取り分・採算・株数が同時に変わる独自ケース。統計的な信頼区間ではない。価格はすべて年12%条件。赤字は利益法で算出不能。

|企業|2029EPS：弱／基準／強|2029計算価格：弱／基準／強|
|---|---:|---:|
|SK hynix|38,360 KRW／262,035 KRW／552,706 KRW|213,323 KRW／2,003,654 KRW／5,763,106 KRW|
|Broadcom|10.20 USD／28.52 USD／48.36 USD|127.65 USD／495.63 USD／1,075.80 USD|
|Wiwynn|56.74 TWD／218.65 TWD／418.81 TWD|473.31 TWD／2,735.84 TWD／6,987.21 TWD|
|Quanta Computer|13.41 TWD／45.30 TWD／82.59 TWD|93.25 TWD／472.32 TWD／1,148.17 TWD|
|Super Micro Computer|0.72 USD／5.50 USD／14.67 USD|4.00 USD／45.90 USD／183.51 USD|
|Samsung Electronics|431 KRW／31,104 KRW／76,843 KRW|2,695 KRW／259,457 KRW／854,665 KRW|
|NVIDIA|4.35 USD／14.74 USD／24.57 USD|54.49 USD／256.13 USD／546.52 USD|
|TSMC|63.55 TWD／168.14 TWD／260.56 TWD|706.81 TWD／2,571.39 TWD／5,071.49 TWD|
|フジクラ|101 JPY／282 JPY／475 JPY|1,258 JPY／4,699 JPY／9,907 JPY|
|Hon Hai Precision|10.27 TWD／27.52 TWD／46.88 TWD|64.24 TWD／248.73 TWD／554.05 TWD|
|信越化学|174 JPY／348 JPY／525 JPY|2,181 JPY／5,810 JPY／10,946 JPY|
|ASML|32.32 USD／77.96 USD／104.72 USD|449.30 USD／1,517.33 USD／2,620.73 USD|
|ディスコ|906 JPY／2,095 JPY／3,445 JPY|15,115 JPY／49,507 JPY／105,369 JPY|
|Siemens Energy|3.62 EUR／8.10 EUR／11.91 EUR|40.32 EUR／123.82 EUR／231.74 EUR|
|Micron|14.35 USD／94.01 USD／199.29 USD|79.82 USD／784.21 USD／2,216.57 USD|
|ダイキン工業|829 JPY／1,339 JPY／1,812 JPY|8,646 JPY／18,610 JPY／31,494 JPY|
|Amazon|5.96 USD／12.00 USD／18.09 USD|82.85 USD／216.93 USD／402.40 USD|
|キオクシアHD|-100 JPY／1,375 JPY／3,461 JPY|算出不能／11,469 JPY／38,490 JPY|
|東京エレクトロン|219 JPY／523 JPY／874 JPY|2,741 JPY／9,091 JPY／19,451 JPY|
|日立製作所|189 JPY／311 JPY／425 JPY|2,097 JPY／4,752 JPY／8,269 JPY|
|Dell Technologies|11.58 USD／35.58 USD／63.94 USD|80.47 USD／371.01 USD／888.88 USD|
|Teradyne|5.27 USD／14.76 USD／25.67 USD|65.88 USD／266.69 USD／606.65 USD|
|SUMCO|-38 JPY／176 JPY／433 JPY|算出不能／2,196 JPY／7,232 JPY|
|Hewlett Packard Enterprise|1.63 USD／4.51 USD／7.50 USD|11.34 USD／43.90 USD／93.82 USD|
|Vertiv|3.53 USD／9.34 USD／17.23 USD|44.23 USD／162.24 USD／383.17 USD|
|アドバンテスト|421 JPY／1,392 JPY／2,635 JPY|5,846 JPY／27,085 JPY／65,941 JPY|
|Lam Research|4.73 USD／11.40 USD／18.54 USD|59.17 USD／206.02 USD／438.27 USD|
|三菱重工|98 JPY／180 JPY／264 JPY|1,088 JPY／2,757 JPY／5,139 JPY|
|NEC|150 JPY／252 JPY／396 JPY|1,669 JPY／3,859 JPY／7,708 JPY|
|富士通|120 JPY／221 JPY／344 JPY|1,169 JPY／3,067 JPY／6,224 JPY|
|Siltronic|-3.54 EUR／4.05 EUR／12.33 EUR|算出不能／45.03 EUR／188.54 EUR|
|味の素|107 JPY／179 JPY／258 JPY|1,484 JPY／3,479 JPY／6,272 JPY|
|AMD|3.12 USD／16.62 USD／28.83 USD|47.73 USD／346.57 USD／761.49 USD|
|Lenovo Group|0.40 HKD／2.35 HKD／4.78 HKD|2.20 HKD／18.00 HKD／49.87 HKD|
|Coherent|1.52 USD／8.93 USD／17.60 USD|18.97 USD／148.96 USD／367.13 USD|
|Alphabet|6.80 USD／13.62 USD／19.86 USD|85.04 USD／217.70 USD／386.52 USD|
|Apple|7.23 USD／11.46 USD／15.49 USD|100.46 USD／207.13 USD／344.63 USD|
|GE Vernova|12.34 USD／31.64 USD／49.67 USD|154.37 USD／549.93 USD／1,104.80 USD|
|ASE Technology|10.16 TWD／29.56 TWD／58.97 TWD|84.79 TWD／390.44 TWD／1,065.83 TWD|
|Arista Networks|2.41 USD／5.14 USD／8.35 USD|33.55 USD／99.98 USD／208.85 USD|
|Sandisk|3.50 USD／85.53 USD／205.30 USD|19.48 USD／713.47 USD／2,283.37 USD|
|イビデン|86 JPY／259 JPY／523 JPY|952 JPY／4,325 JPY／11,633 JPY|
|Unimicron|6.64 TWD／30.89 TWD／68.18 TWD|64.63 TWD／472.38 TWD／1,421.88 TWD|
|GlobalWafers|4.52 TWD／30.26 TWD／62.08 TWD|37.71 TWD／378.69 TWD／1,035.72 TWD|
|Lumentum|4.78 USD／18.52 USD／35.79 USD|59.86 USD／321.85 USD／796.03 USD|
|Eaton|7.35 USD／16.37 USD／24.55 USD|91.97 USD／273.15 USD／511.92 USD|

## 基準の統一と重要な制約

- **TSMCは台湾普通株2330.TW**。先の8社表の米国ADRと異なる。旧ADR EPSを5で割り、10/16 USD/TWDで現地普通株EPSへ換算。現在の台湾株価を使うため、ADRとの価格差で評価が変わる。
- ASMLはEUR利益→米国普通株USD EPSへ換算。LenovoはUSD財務→HKD普通株EPSへ換算。為替は10/16の保存値で固定し、将来為替予想とはしない。
- 東京エレクトロン・イビデン・フジクラ・Wiwynn等の分割/株式配当は現在株価の株数基準とそろえる。株式配当による株数増を利益成長と混同しない。
- イビデン・Unimicron・SK hynix等の株式評価益・営業外益、クラウドの投資評価益、GE Vernovaの税便益・再評価益、Lenovo等の評価損を継続利益と区別する。
- Eatonは将来残存会社だけを評価し、分離株式の価値や負債配賦を評価できていないため順位比較対象外。掲載数には含む。
- メモリでは数量増と単価低下が共存し得る。サーバーODMでは売上の大きさだけで高い株主利益を仮定せず、薄利・SBC・運転資金・転換株式のリスクを残す。
- NVIDIA/Broadcom/AMD等の対象プール内取り分、TSMC等の上流売上、サーバーOEM/ODM売上は工程間で重複する。売上を合計して市場規模の実現を主張しない。
- 掲載46社に限定した横断比較であり、市場全体の網羅や生存者バイアスの除去を保証しない。「詳細モデル」は予測が高確率という意味ではない。

## 各社の方法・反証・一次出典

### 信越化学（4063.T）

電子材料はAIチップの製造面積・工程増へ低めの弾性で接続。PVCはAI支出へ直接接続せず景気と価格。全社EPSをAI材料の成長率で伸ばさない。

**成立条件・反証：** 電子材料のAI感応度50%は独自配分で会社開示のAI売上比率ではない PVC価格、中国供給、エネルギー、為替、ウェーハLTA更改と新能力の償却 金融収益を正常化しても余剰現金の利息が一部含まれ得る。現金価値を別加算する場合は整合が必要



[一次資料 2026-07-24](https://www.shinetsu.co.jp/wp-content/uploads/2026/07/20260724_con_E.pdf)、[一次資料 2026-09-15](https://www.shinetsu.co.jp/wp-content/uploads/2026/09/20260915E2.pdf)

### SUMCO（3436.T）

ウェーハ面積×価格×稼働率回復を売上へ反映。AI装置投資ほど高い弾性を与えず、減価償却込み営業利益率の回復を別仮定。FSTの2026年売却益はゼロ、将来の持分利益はnet_financeに含む少額の正常値。

**成立条件・反証：** FST連結除外後の継続売上がまだ未確定なので390.032bnは粗い校正。正確なTAM×シェアではない 基準OPM16%は足元赤字から大きな稼働率・価格改善を必要とする LTAとスポットの価格改定、200mm回復、新工場償却、為替、借入負担で上下する



[一次資料 2026-08-06](https://ssl4.eir-parts.net/doc/3436/tdnet/2864809/00.pdf)、[一次資料 2026-08-06](https://ssl4.eir-parts.net/doc/3436/tdnet/2864822/00.pdf)、[一次資料 2026-08-27](https://ssl4.eir-parts.net/doc/3436/tdnet/2878442/00.pdf)

### GlobalWafers（6488.TWO）

AI・HBM・先端ロジックのウェーハ消費に接続し、新規米国/日本/伊の認定後立上げを別ramp係数で明示。金融損益を大幅正常化しQ2EPSを伸ばさない。

**成立条件・反証：** Q2の最終利益率24.8%はOPM9.4%を大幅に上回り、その他益を反復させない 新工場の顧客認定、米国コスト、初期償却、地域化の重複投資、伊火災と為替 ramp1.15等は需要・認定が満たされた場合の売上能力消化仮定で会社ガイドではない



[一次資料 2026-08-04](https://www.sas-globalwafers.com/wp-content/uploads/2026/05/GlobalWafers_2026Q2-consolidated-financial-statement_EN.pdf)、[一次資料 2026-08-04](https://www.sas-globalwafers.com/en/gwc_news_en_20260804/)、[一次資料 2026-10-07](https://www.sas-globalwafers.com/en/gwc_news_en_20261007/)、[一次資料 2026-09-23](https://www.sas-globalwafers.com/en/gwc_news_en_20260923/)

### Siltronic（WAF.DE）

300mm面積と価格・シンガポール能力消化をモデル化。EBITDAを純利益に置かず、新工場減価償却を残したIFRS EBIT利益率を仮定する。

**成立条件・反証：** 基準EBIT14%は足元−16.6%から大幅な回復が必要。基準を中立・会社予想と呼ばない 高稼働でも価格が低ければ償却を吸収できない。200mm・電力・為替・借入金利も重要 利益赤字の弱気ケースではPE評価不能。資産価値ゼロの意味ではない 基準2029売上1.870bnEUR・EBIT14%は、償却をH1年率0.4776bnで維持するとEBITDA率約39.5%が必要。EBITDA30%/35%ならEPS約0.79/2.50EURで、基準4.05EURより低い。独自感応度。



[一次資料 2026-07-30](https://www.siltronic.com/fileadmin/investorrelations/2026/Q2/20260730_Siltronic_Half_Year_Financial_Report_2026.pdf)

### 東京エレクトロン（8035.T）

WFE/メモリ・先端ロジックcapexと工程複雑化を装置へ、既存装置台数・稼働をField Solutionsへ。市場150/190bnは会社予測であり確定受注ではない。基準装置OPM36.5%と価格改定は独自仮定。

**成立条件・反証：** 中国売上30%台と輸出規制、Lam等との低温エッチ・成膜の競争 35%OPM目標と数量3倍能力は実現済み利益ではない 部材、人件費、R&D、増産費用・為替と検収時期で利益変動



[一次資料 2026-07-30](https://www.tel.com/ir/library/report/i242su0000000goz-att/fy27q1tanshin-e.pdf)、[一次資料 2026-08-03](https://www.tel.com/ir/library/report/i242su0000000goz-att/FY27Q1_EarningCall_QA_E.pdf)、[一次資料 2026-10-01](https://www.tel.com/ir/stocks/info/)

### Lam Research（LRCX）

成膜・エッチの工程数増（NAND層数/GAA/背面給電）×新設装置需要、保守・部品は既存基盤と稼働へ別感応度。6月売上×4は売上水準の校正でFY/CY会社予想ではない。

**成立条件・反証：** Systemsのメモリ比率46%と中国売上26%の循環・規制 CSBGには旧世代装置も含み全額継続課金ではない 工程統合・競合・供給網/輸送コスト・R&Dと供給拡張。通常SBCと償却を残す



[一次資料 2026-07-29](https://investor.lamresearch.com/2026-07-29-Lam-Research-Corporation-Reports-Financial-Results-for-the-Quarter-Ended-June-28,-2026)

### ASML（ASML）

EUV需要と供給上限の小さい方、DUV市場×シェア、検査・既存機売上を積算。SBC/R&D込み費用・税・株数へ。

**成立条件・反証：** 基準2029売上704億EURは旧2030会社シナリオの上限600億EURを上回る独自上方想定。 増産・検収、輸出規制、High-NA採算、顧客投資の遅延。



[会社決算・説明資料 2026-10-14](https://investor.asml.com/static-files/40c56a6b-1460-4f69-9340-6a869560d24b)

### NVIDIA（NVDA）

共通AI投資から電子機器等の対象プールを切り出し、完成システム等の売上捕捉係数・その他事業・SBC/償却・税・株数を通じEPSへ。

**成立条件・反証：** 売上捕捉係数は観測済みのGPU市場シェアではない。基準2029は2026校正より取り分が増える。 購入契約・出資・条件付き保証、顧客回収、ASIC競争、粗利率。



[会社決算・説明資料 2026-08-26](https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Announces-Financial-Results-for-Second-Quarter-Fiscal-2027/)

### AMD（AMD）

AIアクセラレータ売上はNVIDIA・Broadcomと共有する電子部品売上プール×独自の実効捕捉係数。会社開示のデータセンター売上をInstinctとEPYC等へ独自に分け、PC・ゲーム・組込みを別計算する。部門利益から株式報酬・買収償却・本社費用を残して正常利益を算出する。

**成立条件・反証：** 2029年基準のAIプール捕捉7.5%は独自仮定で、現在の観測シェアではない CUDA・NVIDIA・専用ASICとの競争でGPU採用が伸びない可能性 HBM・実装能力、顧客の導入時期、中国輸出規制 顧客向け最大3.2億株の条件付きワラントと継続的な株式報酬による希薄化



[一次資料 2026-08-04](https://ir.amd.com/financial-information/sec-filings/content/0000002488-26-000121/q22026991.htm)、[一次資料 2026-08-05](https://www.sec.gov/Archives/edgar/data/2488/000000248826000123/amd-20260627.htm)

### Broadcom（AVGO）

AI ASIC/通信の対象プール内の取り分と非AI半導体・ソフト売上を積算。SBC・取得無形資産償却を残す。

**成立条件・反証：** 基準2029AI売上は2026校正の4倍以上。取り分固定ならEPS約13.74ドルまで低下し割安判定は逆転。 顧客集中・内製・設計変更、信用支援、取得無形資産償却と株数増。



[会社決算・説明資料 2026-09-02](https://investors.broadcom.com/news-releases/news-release-details/broadcom-inc-announces-third-quarter-fiscal-year-2026-financial)

### TSMC（2330.TW）

電子機器対象プールの製造・実装原価含有率×TSMCの取り分＋その他売上。供給上限・営業率・税・普通株数からEPSへ。

**成立条件・反証：** 上流原価含有率が2026校正8.5%から2029基準14%へ上昇する独自仮定。 海外工場費用、capex負担、地政学。普通株と米国ADRの価格差にも注意。



[会社決算・説明資料 2026-10-15](https://pr.tsmc.com/english/news/3346)

### ASE Technology（3711.TW）

先端組立・テスト複雑化をATMへ、汎用EMSは低いAI感応度。ATM+EMSの内部売上二重計上を残余方式で除外。金利と正常持分損益だけ金融損益へ残し、評価・ヘッジ益を年換算しない。

**成立条件・反証：** 先端実装需要の全額がOSATへ来るわけではなくTSMC等内製と競合 大顧客集中、設備/人員と減価償却、台湾・為替、テスト時間短縮 EMSの低利益率・部材パススルーが全社売上を大きくするためAI売上純度を過大評価しない



[一次資料 2026-07-30](https://www.sec.gov/Archives/edgar/data/1122411/000095010326011351/dp250868_6k.htm)、[一次資料 2026-10-12](https://www.sec.gov/Archives/edgar/data/1122411/000095010326015458/dp254866_6k.htm)

### 味の素（2802.T）

ABFは一基板の面積/層数・高機能化とAIチップ出荷へ接続。食品等の大きい非FMはAI予算から直接増やさない。会社事業利益から通常のその他営業費用12bn（年4%増）を控除してIFRS営業利益相当へ橋渡し。

**成立条件・反証：** 事業利益はIFRS営業利益と異なり持分損益を含む。部門別正常化は粗い 食品・冷食原材料と価格転嫁、医薬CDMO・R&D、人件費、全社費用がEPSを左右 ABF95%超は半導体材料全体のシェアではない。将来シェア上昇を仮定しない



[一次資料 2026-08-06](https://www.ajinomoto.co.jp/company/en/ir/event/presentation/main/011111113/teaserItems1/01/linkList/0/link/FY26Q1_Tanshin_E.pdf)、[一次資料 2026-08-06](https://www.ajinomoto.co.jp/company/en/ir/event/presentation/main/011111113/teaserItems1/01/linkList/02/link/FY26Q1_Forecast_E.pdf)、[一次資料 2026-06-30](https://www.ajinomoto.co.jp/company/en/ir/event/business_briefing/main/011117/teaserItems1/01/linkList/03/link/20260630_presentation_E.pdf)

### イビデン（4062.T）

CPU/GPU/スイッチ基板の大型・多層化と価格/新ライン歩留まりを電子へ。会社550bnをQ1売上構成で校正するため部門年売上は独自配分。遊休設備償却を金融等費用に残し、株売却益を除外。

**成立条件・反証：** 基準利益率31%は不足プレミアム・稼働率と新棟歩留まりに依存 膨大なcapexのCF支出はPERモデルに含まれず、償却とCFを分ける 同日付近説明PDFの数値と正式8/4短信に不整合があるため正式短信を優先した。旧メモの580/120/70bnを使用しない



[一次資料 2026-08-04](https://www.ibiden.com/ir/items/tannshinn2026Q1.pdf)

### Unimicron（3037.TW）

ABF需要をAIチップ面積・層数と能力認定へ、他PCBは低いAI感応度へ接続。Q2の巨額営業外益を延長せず、営業利益と通常金利から純利益を計算。

**成立条件・反証：** Q2営業外益が営業利益を超える。EPS8.38の4倍を正常利益にしない ABF新能力、原材料、歩留まり、顧客価格交渉・競合増設、HDI/BTの非AI市況 部門利益率とAI売上割合の公表はないため独自配分でC評価。ABF52%をAI売上52%と解釈しない



[一次資料 2026-07-29](https://www.unimicron.com/files/money/Earnings/en/2026-Q2-consolidated-en.pdf)、[一次資料 2026-10-18](https://www.unimicron.com/money01.html)

### ディスコ（6146.T）

HBM薄化・切断、AIロジックとOSAT設備、稼働に応じる工具を加重した工程需要モデル。装置/工具の最新精密構成が未取得なので公表されないTAMシェアを作らず全社校正。

**成立条件・反証：** 出荷と検収売上は違う。10/6単体速報を連結利益へ置換しない 新設備需要は稼働が満たされると一服。工程変更・並列化・顧客投資前倒し 基準OPM44%は足元42.9%近傍。R&D/人件費/償却を除外して利益率を作らない



[一次資料 2026-07-23](https://www.disco.co.jp/eg/ir/library/doc/fr/fr20260723.pdf)、[一次資料 2026-10-06](https://www-hq.disco.co.jp/eg/ir/library/doc/news/202610061_Preliminary_Report_on_Non-Consolidated_Sales_Figures_and_Shipment_Figures_(Second_Quarter_of_Fiscal_Year_2026).pdf)、[一次資料 2026-07-23](https://www.disco.co.jp/eg/ir/library/doc/film/20260723_note.pdf)

### アドバンテスト（6857.T）

SoC・メモリテスタ市場をAI投資とテスト複雑化へ接続し、シェア・他事業・全社営業率・税・株数からEPSへ。

**成立条件・反証：** 評価益・棚卸戻入れを恒久化しない。市場成長とテスト複雑化が同時に進む前提。 供給増・競争・顧客投資循環。高い将来PER維持を基準価格が必要とする。



[会社決算・説明資料 2026-07-29](https://www.advantest.com/document/en/investors/ir-library/result/JE_BIZ_260729_slide.pdf)

### Teradyne（TER）

SoC/メモリのテスト複雑化とAI設備増を半導体テストへ、Product Test・ロボティクスは別の低い感応度へ接続。Advantestとの競争によるシェア上昇を無条件に仮定しない。

**成立条件・反証：** 半導体テストの急増四半期からの校正。Q3会社予想はQ2より低い売上を示す HBM/GPU等の顧客採用、並列化・テスト短縮、Advantestとの競争 Roboticsの回復遅れ、ERP/人件費とR&D。通常のSBC・買収償却・持分投資償却を除外しない



[一次資料 2026-07-28](https://investors.teradyne.com/news-events/press-releases/detail/445/teradyne-reports-second-quarter-2026-results)

### SK hynix（000660.KS）

HBM・汎用DRAM・NANDを重複なく分け、2026年4〜6月の校正売上×出荷ビット数×単価×独自の製品構成・捕捉係数で予測する。数量とビット原価から製造費を計算し、研究開発・減価償却・株式報酬等の固定費を残す。NANDの数量・単価経路は既存キオクシア試算と統一した。製品別売上・原価の内訳は独自配賦で、会社開示値ではない。

**成立条件・反証：** Q2純利益には多額の配当・金融商品評価益があり、将来の反復利益へ延長しない HBM4の歩留まり・顧客集中、Samsung・Micronへの取り分流出 HBMと汎用DRAMの単価・利益率は異なり、HBM比率だけで収益改善を保証しない 汎用DRAM/NANDの値下がりと新工場・先端実装の償却負担。保有金融資産の価値は別評価が必要



[一次資料 2026-07-29](https://news.skhynix.com/en/q2-2026-business-results/)、[一次資料 2026-08-18](https://www.sec.gov/Archives/edgar/data/2120882/000119312526354777/d147827d6k.htm)、[一次資料 2026-08-19](https://www.sec.gov/Archives/edgar/data/2120882/000119312526356133/d428222d6k.htm)、[一次資料 2026-09-07](https://www.trendforce.com/presscenter/news/20260907-13219.html)、[一次資料 2026-08-18](https://www.trendforce.com/presscenter/news/20260818-13186.html)

### Micron（MU）

HBM・汎用DRAM・NAND・その他を分離し、共通の2026年4〜6月の校正売上に出荷数量・単価・費用を掛ける。最新8月期四半期と会社の2027/28年供給不足見通しは別の実績・会社見通しとして示し、独自基準には2028/29年の単価調整を置く。株式報酬・研究開発・通常償却は除外しない。

**成立条件・反証：** 会社は2027/28年も供給不足を予想するが、独自基準はその見通しを全面延長していない HBMの内訳は独自配賦で、共通Q2校正と最新四半期には価格・期間の差がある 複数年契約の価格バンドは一部収益を守るが、具体的な下限・製品構成は非公開 新工場・実装投資、中国競争、顧客前受金の2029〜31年返済と運転資金負担



[一次資料 2026-09-30](https://investors.micron.com/news/press-release/2026/Micron-Technology-Inc--Reports-Record-Fiscal-Fourth-Quarter-and-Full-Year-2026-Results/default.aspx)、[一次資料 2026-09-30](https://investors.micron.com/files/doc_financials/2026/q4/Q4-26-Earnings-Deck.pdf)、[一次資料 2026-10-09](https://www.sec.gov/Archives/edgar/data/723125/000072312526000023/mu-20260903.htm)、[一次資料 2026-09-07](https://www.trendforce.com/presscenter/news/20260907-13219.html)、[一次資料 2026-08-18](https://www.trendforce.com/presscenter/news/20260818-13186.html)

### Samsung Electronics（005930.KS）

HBM・汎用DRAM・NANDの数量、単価、ビット原価を別計算し、ファウンドリ等と端末・ディスプレー等を加える。部門間売上の重複を消去し、株式報酬・償却・研究開発費を残す。普通株と参加型優先株の利益分配を考慮した株数でEPSを計算する。10月8日のQ3速報は会社の予備見通しで、詳細費用の校正はQ2を使う。

**成立条件・反証：** Q3速報の高利益をそのまま恒常利益として年率換算しない メモリ製品別の売上・費用配分は独自仮定で、HBM認定と歩留まりも不確実 端末部門のメモリ調達費と半導体部門の利益が逆方向に動く場合がある 大型設備投資・株式報酬、普通株と優先株の配分、中国メモリメーカーの増産



[一次資料 2026-07-30](https://images.samsung.com/is/content/samsung/assets/global/ir/docs/2026_2Q_conference_eng.pdf)、[一次資料 2026-10-08](https://news.samsung.com/global/samsung-electronics-announces-earnings-guidance-for-third-quarter-2026)、[一次資料 2026-06-30](https://www.samsung.com/global/ir/stock-information/listing-Info/)、[一次資料 2026-08-18](https://www.trendforce.com/presscenter/news/20260818-13186.html)、[一次資料 2026-09-07](https://www.trendforce.com/presscenter/news/20260907-13219.html)

### キオクシアHD（285A.T）

全用途NANDのbit数量・ASP・金額シェアとcost/bit・固定費から利益を推計。その他低収益取引は売上と同額費用。

**成立条件・反証：** 基準2029営業利益率56.7%も高採算。ASP・cost/bit・投資後CFの変化が大きい。 終点EPS法は途中の高利益から残る現金・株主還元を十分評価しない。自社株買いを株数と現金で二重評価しない。



[会社決算・説明資料 2026-07-31](https://www2.jpx.co.jp/disc/285A0/140120260731505265.pdf)

### Sandisk（SNDK）

NANDブランド売上にSSDを含め、出荷ビット数×単価×独自の取り分変化から売上を予測する。JVのウェハ製造をブランド売上へ二重加算しない。株式報酬と研究開発費を残し、株式評価益を除く。会社のFY2028〜30調整後営業利益率75%という長期枠組みより、独自基準は慎重な単価・利益率を置く。

**成立条件・反証：** 直近四半期の株式評価益0.804bnUSDを反復利益に含めない 企業向けSSD・NBM契約は支えになるが、NANDの単価循環は残る JV投資と顧客前受金は現金の自由度に影響する 独自基準は会社の長期調整後利益率75%を下回る。HBFの追加利益は織り込まない



[一次資料 2026-08-05](https://www.sandisk.com/company/newsroom/press-releases/2026/2026-08-05-sandisk-reports-fiscal-fourth-quarter-2026-financial-results)、[一次資料 2026-08-17](https://www.sec.gov/Archives/edgar/data/2023554/000162828026057406/sndk-20260703.htm)、[一次資料 2026-08-13](https://www.sandisk.com/company/newsroom/press-releases/2026/2026-08-13-sandisk-investor-day-2026)、[一次資料 2026-08-18](https://www.trendforce.com/presscenter/news/20260818-13186.html)

### 富士通（6702.T）

Service Solutions内のUvanceと残りのサービスを重複なく分け、ハードウェア・端末と部門間売上消去を加える。Uvance全体をAI売上とは扱わず、企業IT需要とAI導入の弾性を別に置く。本社費用・株式報酬・通常償却を残し、過去の事業売却利益を除く。

**成立条件・反証：** AIによる生産性改善分が人月単価の低下として顧客へ還元される可能性 Uvanceには既存業務からの移行があり、すべてが新規AI需要ではない 海外再編と不採算プロジェクト 前期の非継続事業利益を将来EPSの起点にしない



[一次資料 2026-07-30](https://resources.global.fujitsu/prir/2026/07/2026Q1-Financial-Results-en.pdf)、[一次資料 2026-07-30](https://resources.global.fujitsu/prir/2026/07/2026Q1-Financial-Summary-en.pdf)

### NEC（6701.T）

国内ITをBluStellarと既存業務に分け、海外IT・CSG・社会インフラ等を別に計算する。会社の年間見通しはCSGを含まないため、CSG通年売上2000億円を独自の橋渡し仮定として追加する。本社費用と通常の買収償却・株式報酬を控除し、会社Non-GAAP利益をそのままEPSにしない。

**成立条件・反証：** CSG通年寄与と統合費用は独自仮定で、会社の年間見通しは買収後へ未更新 BluStellarには既存業務の移行が含まれ、すべてが新規AI売上ではない 会社Non-GAAP見通しで除外する株式報酬・買収償却を当モデルでは費用に残す 防衛・海底ケーブルの受注循環、案件損失・納期リスク



[一次資料 2026-07-29](https://group.nec/assets/global/en/about/ir/library/pdf/202607/2907-01-01.pdf)、[一次資料 2026-07-29](https://group.nec/assets/global/en/about/ir/library/pdf/260729/260729-01.pdf)

### Dell Technologies（DELL）

AIサーバーはFY27会社見通し740億USDを将来校正に用い、従来型ISGとPCは最新四半期を年換算する。AI売上はサーバー工程の市場規模×独自の取り分へ連動させる。AI単独の利益率は非開示のため独自仮定とし、本社費用・株式報酬・買収償却を残す。

**成立条件・反証：** 受注残は売上・回収を保証しない。Q2通常FCF0.986bnUSDと調整後8.149bnUSDには顧客金融等の差がある GPU等の仕入高を含む売上拡大とAI単独の利益率を混同しない ODMとの競争とNVIDIA標準設計による交渉力の制約 顧客金融・売掛金・在庫の資金需要が買戻し余力を制限する



[一次資料 2026-09-01](https://investors.delltechnologies.com/sec-filings/all-sec-filings/content/0001571996-26-000039/exhibit991earnings8kq2fy27.htm)

### Hewlett Packard Enterprise（HPE）

最新四半期のサーバー売上を独自にAI40%・従来型60%へ分け、ストレージ・金融・Juniperを含む通信等を計算する。Cloud&AI部門全体をAIとは扱わず、買収による売上増と有機成長を区別する。株式報酬・無形資産償却等を残し、H3C等の売却益を反復金融利益から除く。

**成立条件・反証：** AIサーバー売上割合は会社非開示で、出荷・検収の時期も変動する Juniperの統合、負債と買収無形資産の償却負担 通信機器競争とサーバー部材価格 金融債権と顧客の設備資金需要



[一次資料 2026-09-02](https://www.hpe.com/us/en/newsroom/press-release/2026/09/hpe-reports-fiscal-2026-third-quarter-results.html)、[一次資料 2026-09-02](https://www.hpe.com/content/dam/hpe/newsroom/2026/09/HPE_Q3FY26_earnings_financial_tables.pdf)

### Super Micro Computer（SMCI）

FY27会社売上見通し650〜720億USDの中点を将来校正に使い、AI80%・その他20%へ独自配分する。AI売上はサーバー市場×独自の取り分に連動し、基準ではシェア低下を置く。株式報酬・研究開発・償却を費用に残す。8月31日の監査済み10-Kで通期の売上・利益・営業CFが8月11日速報と一致することを確認した。

**成立条件・反証：** 監査済み財務諸表は無限定適正意見だが、IT全般統制の重大な不備が残る。独立輸出調査は完了、政府照会は継続 FY26は黒字でも営業CFが−6.81bnUSD。在庫・売掛金増には外部資金が必要 FY27会社見通し中点は前期比約75%増で、需要・検収・納期の未達リスクが大きい 強制転換優先株・転換社債・株式報酬による希薄化 Q4粗利益率17.5%は顧客・製品構成に左右され、通期の維持を保証しない



[一次資料 2026-08-11](https://ir.supermicro.com/news/news-details/2026/Supermicro-Announces-Fourth-Quarter-and-Full-Fiscal-Year-2026-Financial-Results/default.aspx)、[一次資料 2026-08-31](https://www.sec.gov/Archives/edgar/data/1375365/000137536526000022/smci-20260630.htm)

### Lenovo Group（0992.HK）

IDG・ISG・SSGを分け、部門間売上の重複を消去する。ISG年換算340億USDを独自にAI180億・従来型160億へ配分する。ワラント評価損と投資評価益の両方を除き、株式報酬・通常買収償却・研究開発を残す。将来黒字時の転換社債・ワラントを含む経済的希薄化株数を用い、USDのEPSをHKDへ一度だけ換算する。

**成立条件・反証：** Q1会計赤字にはワラント再評価損1.690bnUSDが大きく、実績EPSの単純延長は不適切 評価損益の除外は株式報酬・通常償却の除外を意味しない ワラント・転換社債の現金決済/株式決済によって経済的希薄化が変わる 薄いハードウェア利益率、在庫・顧客金融。SSGやAI関連売上にはAI PC等も含まれる



[一次資料 2026-08-13](https://news.lenovo.com/pressroom/press-releases/q1-fy-2026-27/)、[一次資料 2026-08-13](https://doc.irasia.com/listco/hk/lenovo/interim/2027/int1q.pdf)

### Quanta Computer（2382.TW）

2026校正は1〜9月実績売上＋Q4をQ3と同額とする独自仮定。AI65%・従来型サーバー15%・その他20%へ独自配分し、AI売上をサーバー工程の市場規模と取り分に連動させる。製品別割合は会社開示値ではない。株式報酬・通常償却・研究開発を利益率に残す。最新財務・株数は台湾証券取引所の一次APIで確認した。

**成立条件・反証：** AI製品別売上割合65%は独自推定で、会社の監査済みAI部門開示ではない 顧客支給GPU/メモリと売上総額計上の変更により、売上と出荷数量が乖離する 米国生産の立上げ、部品不足、貿易規制 顧客集中、在庫・売掛金の資金需要。現株数4.1076bnを使用し旧EPS分母を流用しない 旧試算のCB織込み不足を訂正。全元本上限を使う保守的経済EPSであり、残存元本・転換登録の精査でEPSは変わる。新規CB・追加資金調達は別の希薄化リスク。



[一次資料 2026-10-18](https://openapi.twse.com.tw/v1/opendata/t187ap06_L_ci)、[一次資料 2026-10-17](https://openapi.twse.com.tw/v1/opendata/t187ap05_L)、[一次資料 2026-10-17](https://openapi.twse.com.tw/v1/opendata/t187ap03_L)、[一次資料 2026-08-13](https://www.quantatw.com/Quanta/chinese/investment/financials_icp.aspx)、[一次資料 2026-08-03](https://links.sgx.com/1.0.0/corporate-announcements/A3JJ4IET6UQ7WOK9/21e6b795a85730c264e324874c22d5d196cdf37d2d8ef097d3c1c87706d7a1a1)、[一次資料 2026-08-03](https://links.sgx.com/1.0.0/corporate-announcements/RKZFKYAIL9T8YIJV/2a8abdf6562994d164d6413006aca6438132295e71a411e31d14b3bbc63308a3)

### Wiwynn（6669.TW）

1〜9月実績売上＋Q4をQ3と同額とする独自校正をAI80%・従来型20%へ配分する。4月以降の一部顧客のメモリ代理調達を反映した純額売上を使い、顧客支給部品を総額へ戻さない。Q2のNRE収入による利益率上振れを恒常化せず、株式報酬・償却等を費用に残す。9月権利落の株式配当後株数でEPSを計算する。

**成立条件・反証：** AI80%の売上内訳は独自仮定で、特定顧客・案件への集中がある 代理調達・顧客支給方式で売上総額が減っても出荷量・利益が同率で減るとは限らない Q2のNRE収入は利益率を押し上げたが、基準のAI営業利益率は6.5%に抑えた 大型設備投資、最大150億TWDの転換社債と15億USD融資による資金・希薄化リスク 株式配当19.827946TWD/旧株、倍率2.9827946を反映。旧Q2EPS80.43を現株価へ直接割らない 旧試算のCB織込み不足を訂正。全元本上限を使う保守的経済EPSであり、残存元本・転換登録の精査でEPSは変わる。新規CB・追加資金調達は別の希薄化リスク。



[一次資料 2026-10-18](https://openapi.twse.com.tw/v1/opendata/t187ap06_L_ci)、[一次資料 2026-10-17](https://openapi.twse.com.tw/v1/opendata/t187ap05_L)、[一次資料 2026-10-17](https://openapi.twse.com.tw/v1/opendata/t187ap03_L)、[一次資料 2026-08-07](https://www.wiwynn.com/news/wiwynn-reports-second-quarter-2026-financial-results?hs_amp=true)、[一次資料 2026-09-02](https://www.wiwynn.com/investors/shareholders-services)、[一次資料 2026-09-03](https://links.sgx.com/1.0.0/corporate-announcements/UDGP37S01F4SQYXD/d62fbc416c904566f43852fccda0e3bbd769fe8654517568e87f621cbc92a578)

### Hon Hai Precision（2317.TW）

2026校正は1〜9月実績売上＋Q4をQ3と同額とする独自仮定。AI45%・従来型通信等15%・端末等40%へ独自配分し、AIラック/ASIC増産と一般電子機器を分ける。顧客支給型ASICの部材を重複加算せず、株式報酬・償却・研究開発、通常金融費用、税・非支配持分を引いて親会社EPSを算出する。

**成立条件・反証：** AI45%の製品配分は独自仮定で、Cloud&Networkingの全売上をAIとは扱わない ASICの委託・顧客支給方式では売上総額と利益成長率が一致しない 米国等への生産移転、部品不足、貿易規制 上期営業CF−691億TWD・FCF−1500億TWD。増産に伴う在庫・売掛金と設備投資の資金負担 連結利益から非支配株主分を引く必要がある



[一次資料 2026-10-18](https://openapi.twse.com.tw/v1/opendata/t187ap06_L_ci)、[一次資料 2026-10-17](https://openapi.twse.com.tw/v1/opendata/t187ap05_L)、[一次資料 2026-10-17](https://openapi.twse.com.tw/v1/opendata/t187ap03_L)、[一次資料 2026-08-12](https://www.foxconn.com/en-us/press-center/press-releases/latest-news/2095)、[一次資料 2026-08-18](https://image.honhai.com/upload/202608/law_talk/Hon_Hai_2Q26_Results_Transcript_English_20260818_1815.pdf)

### Arista Networks（ANET）

共通AI投資×通信対象配分×取り分＋残余事業。全社営業率・金融収益・税・株数を通じEPSへ。

**成立条件・反証：** AI対象売上・シェアは独立実測でなく校正値。非AIとの区分も推定。 顧客集中・NVIDIA/ASIC通信競争、SBC・希薄化、評価倍率。



[会社決算・説明資料 2026-08-04](https://investors.arista.com/Communications/Press-Releases-and-Events/Press-Release-Detail/2026/Arista-Networks-Inc--Reports-Second-Quarter-2026-Financial-Results/default.aspx)

### フジクラ（5803.T）

2026のICT/その他配分はQ1と会社通期売上を整合させた独自推定。分割後株数でEPS算出。

**成立条件・反証：** 不足利幅の正常化、増産減価償却、円高。2030米国大型増産を29年売上に全額算入しない。



[一次資料 2026-08-07](https://ssl4.eir-parts.net/doc/5803/tdnet/2866589/00.pdf)、[一次資料 2026-08-07](https://ssl4.eir-parts.net/doc/5803/tdnet/2866585/00.pdf)、[一次資料 2026-08-07](https://www.fujikura.co.jp/en/ir/basic-information/)

### Coherent（COHR）

2026Q4年換算売上8.182を独自校正。非GAAP利益を使用せず、GAAP OPから改善を仮定。

**成立条件・反証：** 増産資金・運転資本、顧客集中、光技術交代。営業率はSBC/償却を含む。



[一次資料 2026-08-12](https://www.sec.gov/Archives/edgar/data/820318/000119312526346860/d128030dex991.htm)

### Lumentum（LITE）

調整営業率40%をGAAPとしない。SBC・無形償却を残すため将来標準32–33%。債務損失と関連税効果は除く。

**成立条件・反証：** CPO/EML競争、利益率正常化、転換株希薄化、設備資金。



[一次資料 2026-08-11](https://investor.lumentum.com/financial-news-releases/news-details/2026/Lumentum-Announces-Fourth-Quarter-and-Full-Fiscal-Year-2026-Results/default.aspx)

### 日立製作所（6501.T）

調整EBITAをそのまま使わず、買収償却を含む正常営業率を独自設定。基本株数900/201.14=4.4745bnを校正。

**成立条件・反証：** 送電納期・固定価格採算、円高、非AI需要。



[一次資料 2026-07-29](https://www.hitachi.com/content/dam/hitachi/global/en/press/files/2026/07/260729/2026_1Qpre.pdf)

### Eaton（ETN）

部門利益率から本社費/取得無形償却等1.6–1.8bn控除。SBC残す。Mobility将来売上は除くため現株主総価値比較は不完全。

**成立条件・反証：** Mobility分離株式の価値をこの残存ETN EPS法は評価しない。負債配賦と分離費用不明。

現在株価はMobility分離前の権利を含む。残存会社の将来EPSだけの計算価格には下方バイアスがあり、他社との割安順位から除外する。

[一次資料 2026-07-31](https://www.sec.gov/Archives/edgar/data/1551182/000155118226000030/etn-20260630.htm)、[一次資料 2026-07-31](https://www.eaton.com/us/en-us/company/news-insights/news-releases/2026/eaton-reports-record-second-quarter-2026-results.html)

### Vertiv（VRT）

共通AI投資×電源/冷却対象配分×取り分＋残余事業。全社営業率はSBC・償却込み。

**成立条件・反証：** AI専用売上・シェアは独立観測値でなく売上に合わせた校正。 顧客納期・運転資金、液冷競争、供給増、希薄化。



[会社決算・説明資料 2026-07-29](https://investors.vertiv.com/news/news-details/2026/Vertiv-Reports-Strong-Second-Quarter-2026-with-Diluted-EPS-Growth-of-53-Adjusted-Diluted-EPS-Growth-of-60-Raises-Full-Year-2026-Guidance-Across-All-Key-Metrics/default.aspx)

### ダイキン工業（6367.T）

DC分割150は実測ではない。全社会社計画5150と整合。

**成立条件・反証：** DC全社構成小。一般空調需要と買収償却・円高の影響大。



[一次資料 2026-08-04](https://www.daikin.com/-/media/993A6303AC814F598BD75FA6B53CFF56.ashx)、[一次資料 2026-08-04](https://www.daikin.com/-/media/Project/Daikin/daikin_com/investor/data/others/20251127-DC-Strategy/Presentation-3-Time.pdf)

### Amazon（AMZN）

2026年売上校正830は独自年率換算。営業率はSBC・R&D・償却を含む。capex自体をNIから控除せず、AWS弱気率28/27%で償却負担を反映。投資評価益は0。

**成立条件・反証：** データセンター償却増、利用率/価格、Anthropic投資損失、物流労務費。



[一次資料 2026-07-30](https://ir.aboutamazon.com/news-release/news-release-details/2026/Amazon-com-Announces-Second-Quarter-Results/default.aspx)

### Alphabet（GOOGL）

共有AI R&Dを年32–38bn別控除。潜在転換株を含む将来の完全希薄化株数を独自仮定。if-converted EPSと同様、優先配当は分子で加算戻すため別途二重控除しない。正式なGAAP EPS予想や転換時期の予想ではない。投資評価益0。

**成立条件・反証：** 検索代替、設備償却、追加資金調達。優先株転換は将来株数に含む仮定。



[一次資料 2026-07-22](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000066/googexhibit991q22026.htm)、[一次資料 2026-07-22](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000071/goog-20260630.htm)

### Apple（AAPL）

9mとQ3を用いた独自年間校正。季節性があり会社FY予想ではない。関税返金を外し継続営業率設定。SBC/R&D/償却を配賦後。

**成立条件・反証：** AI収益化は不確実。AppStore規制、中国競争。買戻し減少ならEPS低下。



[一次資料 2026-07-30](https://www.apple.com/newsroom/pdfs/fy2026q3/FY26_Q3_Consolidated_Financial_Statements.pdf)、[一次資料 2026-07-30](https://www.apple.com/newsroom/2026/07/apple-reports-third-quarter-results/)

### 三菱重工（7011.T）

2024年1:10分割後の株数を会社予想NI/EPSから校正。全社費用を別控除。

**成立条件・反証：** 長期工事原価・検収、円高、防衛案件。事業利益内の非反復損益を将来算入しない。



[一次資料 2026-08-04](https://www.mhi.com/finance/library/result/pdf/fy20261q/presentation.pdf)

### GE Vernova（GEV）

Q2年換算独自売上校正。EBITDA率をそのまま使用せず償却後営業率。税便益や投資再評価なし。

**成立条件・反証：** 前受CFは恒常利益でない。風力損失、ガス納期遅延。



[一次資料 2026-07-22](https://www.gevernova.com/sites/default/files/gev_webcast_pressrelease_07222026.pdf)、[一次資料 2026-07-22](https://www.sec.gov/Archives/edgar/data/1996810/000199681026000148/gev-20260630.htm)、[一次資料 2026-01-28](https://www.sec.gov/Archives/edgar/data/1996810/000199681026000012/gevpressrelease4q25.htm)

### Siemens Energy（ENR.DE）

Q3/9mから年間売上独自校正。取得無形償却を含む営業率、全社費用と非支配株主利益を控除。

**成立条件・反証：** Gamesa品質・大型固定価格案件。前受資金を現金価値に別加算しない。



[一次資料 2026-08-05](https://assets.siemens-energy.com/dam/d0147174-31a9-4a78-b062-b49d00428fc4/earnings-release-q3-fy2026-en-pdf_Original%20file.pdf)


## データ・再現・検証

- [表示用46社データ](ranking.json) · [276ケースJSON](results.json) · [CSV](results.csv)
- [10/16株価・為替・公開取得URL・原本ハッシュ](prices.json)
- 追加38社の保存入力：[装置・材料等12社](inputs/japan.json) · [計算・メモリ・サーバー14社](inputs/compute.json) · [光・電力・クラウド等12社](inputs/infrastructure.json)
- [入力ハッシュ](input-manifest.json) · [統合再計算](build_model.py)
- [検証結果](validation.json)

算術・単位・分割・ケース数・出典・欠損・ソート・画面を確認する。こうした検証は独自の将来利益・評価倍率の正しさを保証しない。
