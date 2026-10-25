# 日本・台湾・欧州装置/材料12社：2028/29年利益・EPSの独自シナリオ

確認2026-10-18 JST。金額・株数ともbillion、EPSは現地通貨の普通株1株当たり。株価は親側で取得。全72ケースは会社予想・コンセンサスではない。

市場TAMや工程内シェアを一次資料で確認できない企業は、最新部門売上を市場需要へ接続している。公表されないAI売上比率を捏造しないため、モデルの感応度配分は独自仮定として開示した。単純EPS CAGRは使わない。

## 共通式

revenue=sum(anchor × growth_factor × share_factor); OP=sum(segment revenue × OPM)−unallocated; pretax=OP+net_finance; tax=max(pretax,0)×rate; NI=pretax−tax−minority; EPS=NI/diluted shares

2026AIインフラ支出1,000bnUSDを校正。2028弱/基準/強=1,000/1,400/1,900、2029=950/1,700/2,500。各部門の成長係数は `(1−AI感応割合)×非AI需要係数 + AI感応割合×AI支出比^弾性×工程複雑化係数` に価格・能力消化係数を乗じる。割合は独自のモデル感応度で、実測AI売上比率や世界市場シェアではない。

SBC、R&D、償却を通常費用に残す。金融/持分/為替益は正常化し、赤字時に税便益を自動計上しない。終点PERは価格を参照して調整しておらず、事業の耐久性と循環に対する独自事前仮定。

## EPS一覧

| 企業 | 通貨 | 2028弱 | 2028基準 | 2028強 | 2029弱 | 2029基準 | 2029強 | 終点PER弱/基準/強 | 品質 |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| 信越化学 | JPY | 180.15 | 325.32 | 466.26 | 174.28 | 348.24 | 524.90 | 18/24/30 | B_segment_calibrated |
| SUMCO | JPY | -39.19 | 160.88 | 376.52 | -38.41 | 175.54 | 433.46 | 12/18/24 | C_scope_and_cycle_sensitive |
| GlobalWafers | TWD | 4.74 | 27.99 | 54.39 | 4.52 | 30.26 | 62.08 | 12/18/24 | B_minus_ramp_sensitive |
| Siltronic | EUR | -3.65 | 3.71 | 10.81 | -3.54 | 4.05 | 12.33 | 10/16/22 | C_depreciation_and_recovery_sensitive |
| 東京エレクトロン | JPY | 224.79 | 449.38 | 689.58 | 219.03 | 523.11 | 874.43 | 18/25/32 | B_process_and_service_calibrated |
| Lam Research | USD | 4.88 | 9.72 | 14.50 | 4.73 | 11.40 | 18.54 | 18/26/34 | B_process_and_support_calibrated |
| ASE Technology | TWD | 10.60 | 26.11 | 48.29 | 10.16 | 29.56 | 58.97 | 12/19/26 | B_ATM_EMS_calibrated |
| 味の素 | JPY | 108.54 | 162.83 | 221.02 | 106.72 | 178.73 | 257.81 | 20/28/35 | B_whole_company_bridge |
| イビデン | JPY | 89.19 | 221.22 | 409.27 | 85.63 | 259.21 | 522.98 | 16/24/32 | B_minus_source_discrepancy_and_capex |
| Unimicron | TWD | 6.98 | 26.61 | 54.04 | 6.64 | 30.89 | 68.18 | 14/22/30 | C_high_nonop_and_capacity_uncertainty |
| ディスコ | JPY | 932.53 | 1,813.35 | 2,758.12 | 906.00 | 2,094.66 | 3,444.99 | 24/34/44 | B_equipment_and_consumables_blend |
| Teradyne | USD | 5.53 | 12.68 | 20.26 | 5.27 | 14.76 | 25.67 | 18/26/34 | B_test_product_robotics_calibrated |

## 企業別の根拠と反証

### 信越化学（4063.T）

電子材料はAIチップの製造面積・工程増へ低めの弾性で接続。PVCはAI支出へ直接接続せず景気と価格。全社EPSをAI材料の成長率で伸ばさない。

最新一次確認：

- 2026-07-24 / company_actual / FY27/3 Q1 consolidated: {"revenue_bn": 662.424, "operating_income_bn": 173.798, "parent_income_bn": 130.829, "diluted_eps": 70.24, "external_segment_revenue_bn": [279.271, 227.798, 118.203, 37.151]}。[一次資料](https://www.shinetsu.co.jp/wp-content/uploads/2026/07/20260724_con_E.pdf)

- 2026-07-24 / company_guidance / FY27/3 full-year guidance: {"revenue_bn": 2700, "operating_income_bn": 700, "parent_income_bn": 525, "basic_eps": 286}。[一次資料](https://www.shinetsu.co.jp/wp-content/uploads/2026/07/20260724_con_E.pdf)

- 2026-09-15 / company_actual / FCSR adjustment; July repurchase: {"half_repurchased_shares_bn": 0.0162317, "adjustment_shares_returned_bn": 0.0006416}。[一次資料](https://www.shinetsu.co.jp/wp-content/uploads/2026/09/20260915E2.pdf)

株数：Q1 diluted NI/EPS≈1.863bn; July buyback32.4634m and September first adjustmentを参照。未来の追加買戻しを仮定せず2028/29=1.84/1.85bnの独自希薄化分母。

終点倍率：材料技術・財務耐久性に加点する一方、PVCとウェーハ循環があるため基準24倍。独自の2029終点倍率で現在PERではない。

独自シナリオの主要入力：

|部門|売上校正bn|AI感応割合（独自）|弾性|工程複雑化年率 弱/基準/強|価格係数|能力消化係数|OPM弱/基準/強|
|---|---:|---:|---:|---|---|---|---|
| 電子材料（ウェーハ・レジスト・マスク等） | 1117.0840 | 0.50 | 0.65 | 0.01/0.04/0.07 | 0.94/1/1.05 | 1/1/1 | 0.28/0.37/0.42 |
| 生活環境基盤材料（PVC・苛性ソーダ等） | 911.1920 | 0.00 | 0.00 | 0/0/0 | 0.9/1/1.06 | 1/1/1 | 0.08/0.16/0.23 |
| 機能材料 | 472.8120 | 0.10 | 0.40 | 0/0.01/0.02 | 0.94/1/1.05 | 1/1/1 | 0.19/0.245/0.28 |
| 加工・商事・技術サービス | 148.6040 | 0.10 | 0.40 | 0/0.01/0.02 | 0.94/1/1.05 | 1/1/1 | 0.15/0.2/0.23 |

反証・制約：

電子材料のAI感応度50%は独自配分で会社開示のAI売上比率ではない; PVC価格、中国供給、エネルギー、為替、ウェーハLTA更改と新能力の償却; 金融収益を正常化しても余剰現金の利息が一部含まれ得る。現金価値を別加算する場合は整合が必要。

再計算用の全係数・金融損益・税率・NCI・希薄化分母はJSONとPythonに保存。
### SUMCO（3436.T）

ウェーハ面積×価格×稼働率回復を売上へ反映。AI装置投資ほど高い弾性を与えず、減価償却込み営業利益率の回復を別仮定。FSTの2026年売却益はゼロ、将来の持分利益はnet_financeに含む少額の正常値。

最新一次確認：

- 2026-08-06 / company_actual / H1 consolidated: {"revenue_bn": 215.016, "operating_income_bn": -6.363, "parent_income_bn": -12.895, "basic_eps": -36.87, "basic_weighted_shares_bn": 0.3497186}。[一次資料](https://ssl4.eir-parts.net/doc/3436/tdnet/2864809/00.pdf)

- 2026-08-06 / company_actual_and_quarter_guidance / Q2 shipments/pricing and Q3 guidance: {"q2_revenue_bn": 113.6, "q2_operating_income_bn": -1.1, "q3_revenue_bn": 118, "q3_operating_income_bn": 0}。[一次資料](https://ssl4.eir-parts.net/doc/3436/tdnet/2864822/00.pdf)

- 2026-08-27 / company_actual / FST deconsolidation announcement: {"retained_voting_interest": 0.38, "deemed_reclassification_date": "2026-09-30", "reported_earnings_impact": "under review"}。[一次資料](https://ssl4.eir-parts.net/doc/3436/tdnet/2878442/00.pdf)

株数：最新発行350.175m・自己442,825株、H1平均349.719mを出発点。将来0.353/0.355bnは独自希薄化仮定。

終点倍率：循環回復に依存するウェーハ。赤字からの反転を成長株の高倍率で評価せず基準18倍。

独自シナリオの主要入力：

|部門|売上校正bn|AI感応割合（独自）|弾性|工程複雑化年率 弱/基準/強|価格係数|能力消化係数|OPM弱/基準/強|
|---|---:|---:|---:|---|---|---|---|
| 継続連結ウェーハ事業（FST除外校正） | 390.0320 | 0.55 | 0.55 | 0/0.025/0.05 | 0.9/1.04/1.1 | 1/1.08/1.15 | -0.02/0.16/0.27 |

反証・制約：

FST連結除外後の継続売上がまだ未確定なので390.032bnは粗い校正。正確なTAM×シェアではない; 基準OPM16%は足元赤字から大きな稼働率・価格改善を必要とする; LTAとスポットの価格改定、200mm回復、新工場償却、為替、借入負担で上下する。

再計算用の全係数・金融損益・税率・NCI・希薄化分母はJSONとPythonに保存。

正常化：2026 H1売上年換算からFST連結除外40bnを独自控除。誤差が大きくC評価。; 持分38%を売上に再加算せず、金融・持分損益の正常仮定に含め二重計上を防ぐ。
### GlobalWafers（6488.TWO）

AI・HBM・先端ロジックのウェーハ消費に接続し、新規米国/日本/伊の認定後立上げを別ramp係数で明示。金融損益を大幅正常化しQ2EPSを伸ばさない。

最新一次確認：

- 2026-08-04 / company_actual / Q2 and H1 consolidated: {"q2_revenue_bn": 15.21431, "q2_operating_income_bn": 1.422811, "q2_parent_income_bn": 3.779084, "q2_other_gains_bn": 3.13286, "q2_diluted_shares_bn": 0.478414, "h1_revenue_bn": 29.199108}。[一次資料](https://www.sas-globalwafers.com/wp-content/uploads/2026/05/GlobalWafers_2026Q2-consolidated-financial-statement_EN.pdf)

- 2026-08-04 / company_actual / capacity and demand comments: {"existing_12inch_utilization": "fully utilized excluding new lines", "texas": "multiple Tier-1 qualifications", "italy": "8inch fire July20; new12inch not affected"}。[一次資料](https://www.sas-globalwafers.com/en/gwc_news_en_20260804/)

- 2026-10-07 / company_actual / September/Q3 monthly sales; no Q3 profits yet: {"q3_revenue_bn_rounded": 14.87, "q3_revenue_qoq": -0.0226, "jan_sep_revenue_bn_from_monthly_sum": 44.07, "italy_epi_restart": "Sep14; downstream repair continues"}。[一次資料](https://www.sas-globalwafers.com/en/gwc_news_en_20261007/)

- 2026-09-23 / company_actual / GDS pricing, completion confirmedOct7: {"gds_issued_bn": 0.05, "ordinary_shares_per_GDS": 1, "gross_proceeds_usd_bn": 1.432, "proforma_shares_after_offering_bn": 0.528114}。[一次資料](https://www.sas-globalwafers.com/en/gwc_news_en_20260923/)

株数：Q2普通株478.114m・希薄化478.414m。9月GDS50m（各1普通株）を加味したプロフォーマ普通株528.114mから、将来0.535/0.540bnの希薄化分母。買戻しなし。

終点倍率：地域分散と顧客認定に価値はあるが、供給循環・資本集約・稼働回復に依存し基準18倍。

独自シナリオの主要入力：

|部門|売上校正bn|AI感応割合（独自）|弾性|工程複雑化年率 弱/基準/強|価格係数|能力消化係数|OPM弱/基準/強|
|---|---:|---:|---:|---|---|---|---|
| 半導体ウェーハ等 | 58.7600 | 0.55 | 0.55 | 0/0.025/0.05 | 0.92/1.03/1.08 | 1.02/1.15/1.28 | 0.08/0.23/0.32 |

反証・制約：

Q2の最終利益率24.8%はOPM9.4%を大幅に上回り、その他益を反復させない; 新工場の顧客認定、米国コスト、初期償却、地域化の重複投資、伊火災と為替; ramp1.15等は需要・認定が満たされた場合の売上能力消化仮定で会社ガイドではない。

再計算用の全係数・金融損益・税率・NCI・希薄化分母はJSONとPythonに保存。

正常化：Q2その他益3.132860bnを年換算せず、将来net_financeは−1/+0.5/+1.5bn。SBC・償却は営業利益率に残す。; 9月GDSの希薄化を無視しない。10/7公表のQ3売上はQoQ減で、全社の足元成長を一律AI好況としない。
### Siltronic（WAF.DE）

300mm面積と価格・シンガポール能力消化をモデル化。EBITDAを純利益に置かず、新工場減価償却を残したIFRS EBIT利益率を仮定する。

最新一次確認：

- 2026-07-30 / company_actual / H1 IFRS and new shares: {"revenue_bn": 0.6281, "ebitda_bn": 0.1345, "ebit_bn": -0.1043, "depreciation_bn": 0.2388, "net_income_before_nci_bn": -0.13, "new_shares_bn": 0.003, "capital_raise_bn": 0.273, "net_financial_debt_bn": 0.6919}。[一次資料](https://www.siltronic.com/fileadmin/investorrelations/2026/Q2/20260730_Siltronic_Half_Year_Financial_Report_2026.pdf)

- 2026-07-30 / company_guidance / FY26 guidance: {"revenue_change": "low-to-mid single digit decline vs FY25 EUR1.3467bn", "ebitda_margin_range": [0.2, 0.24]}。[一次資料](https://www.siltronic.com/fileadmin/investorrelations/2026/Q2/20260730_Siltronic_Half_Year_Financial_Report_2026.pdf)

株数：6月新株3mで30m→33m。将来33.5/34m、既存・将来希薄化と買戻しなし。NCIは正の税後利益の15%を独自控除。

終点倍率：ウェーハ循環と高固定費・債務を反映して基準16倍。回復時の利益に高い成長プレミアムを付けない。

独自シナリオの主要入力：

|部門|売上校正bn|AI感応割合（独自）|弾性|工程複雑化年率 弱/基準/強|価格係数|能力消化係数|OPM弱/基準/強|
|---|---:|---:|---:|---|---|---|---|
| シリコンウェーハ | 1.2562 | 0.55 | 0.55 | 0/0.02/0.04 | 0.9/1.05/1.14 | 1.02/1.12/1.25 | -0.06/0.14/0.25 |

反証・制約：

基準EBIT14%は足元−16.6%から大幅な回復が必要。基準を中立・会社予想と呼ばない; 高稼働でも価格が低ければ償却を吸収できない。200mm・電力・為替・借入金利も重要; 利益赤字の弱気ケースではPE評価不能。資産価値ゼロの意味ではない。

再計算用の全係数・金融損益・税率・NCI・希薄化分母はJSONとPythonに保存。
### 東京エレクトロン（8035.T）

WFE/メモリ・先端ロジックcapexと工程複雑化を装置へ、既存装置台数・稼働をField Solutionsへ。市場150/190bnは会社予測であり確定受注ではない。基準装置OPM36.5%と価格改定は独自仮定。

最新一次確認：

- 2026-07-30 / company_actual / FY27 Q1 consolidated: {"revenue_bn": 732.388, "operating_income_bn": 211.407, "parent_income_bn": 164.341, "basic_weighted_shares_bn_presplit": 0.454785263}。[一次資料](https://www.tel.com/ir/library/report/i242su0000000goz-att/fy27q1tanshin-e.pdf)

- 2026-07-30 / company_guidance / H1 company guidance: {"revenue_bn": 1620, "operating_income_bn": 458, "parent_income_bn": 349, "full_year_guidance": "not yet published"}。[一次資料](https://www.tel.com/ir/library/report/i242su0000000goz-att/fy27q1tanshin-e.pdf)

- 2026-08-03 / company_market_outlook_and_targets / July30 earnings QA: {"company_wfe_2026_usd_bn": ">150", "company_wfe_2027_usd_bn": ">190", "operating_margin_target": 0.35}。[一次資料](https://www.tel.com/ir/library/report/i242su0000000goz-att/FY27Q1_EarningCall_QA_E.pdf)

- 2026-10-01 / company_actual / ordinary share split basis: {"issued_shares_bn": 2.340163665, "inferred_split_from_June30": 5}。[一次資料](https://www.tel.com/ir/stocks/info/)

株数：10/1 1:5分割後。Q1平均454.785m×5≈2.274bn、将来2.28/2.29bn。旧EPSを5で割らず比較しない。

終点倍率：塗布現像の強い地位と工程の拡大を評価し基準25倍、WFE循環・対中規制でASML級独占倍率を自動付与しない。

独自シナリオの主要入力：

|部門|売上校正bn|AI感応割合（独自）|弾性|工程複雑化年率 弱/基準/強|価格係数|能力消化係数|OPM弱/基準/強|
|---|---:|---:|---:|---|---|---|---|
| 新規半導体製造装置 | 2177.5520 | 0.75 | 0.75 | 0.02/0.065/0.1 | 0.97/1.02/1.05 | 1/1.06/1.12 | 0.26/0.365/0.41 |
| Field Solutions（部品・サービス・中古/改造） | 752.0000 | 0.45 | 0.45 | 0.01/0.03/0.05 | 0.99/1.02/1.04 | 1/1/1 | 0.24/0.3/0.34 |

反証・制約：

中国売上30%台と輸出規制、Lam等との低温エッチ・成膜の競争; 35%OPM目標と数量3倍能力は実現済み利益ではない; 部材、人件費、R&D、増産費用・為替と検収時期で利益変動。

再計算用の全係数・金融損益・税率・NCI・希薄化分母はJSONとPythonに保存。
### Lam Research（LRCX）

成膜・エッチの工程数増（NAND層数/GAA/背面給電）×新設装置需要、保守・部品は既存基盤と稼働へ別感応度。6月売上×4は売上水準の校正でFY/CY会社予想ではない。

最新一次確認：

- 2026-07-29 / company_actual / Quarter ended June28 actual: {"revenue_bn": 6.722238, "systems_bn": 4.249848, "support_and_other_bn": 2.47239, "gaap_operating_margin": 0.374, "net_income_bn": 2.277282, "diluted_shares_bn": 1.256032}。[一次資料](https://investor.lamresearch.com/2026-07-29-Lam-Research-Corporation-Reports-Financial-Results-for-the-Quarter-Ended-June-28,-2026)

- 2026-07-29 / company_quarter_guidance / September quarter guidance: {"revenue_bn": 8.1, "revenue_range_bn": [7.7, 8.5], "gaap_operating_margin": 0.395, "diluted_shares_bn": 1.255}。[一次資料](https://investor.lamresearch.com/2026-07-29-Lam-Research-Corporation-Reports-Financial-Results-for-the-Quarter-Ended-June-28,-2026)

株数：最新実績希薄化1.256032bnと9月会社想定1.255bnから将来1.28/1.29bn。未発表買戻しによるEPS押上げを与えない。

終点倍率：高付加価値の成膜・エッチとサポートを評価し基準26倍。メモリ投資循環・規制を加味。

独自シナリオの主要入力：

|部門|売上校正bn|AI感応割合（独自）|弾性|工程複雑化年率 弱/基準/強|価格係数|能力消化係数|OPM弱/基準/強|
|---|---:|---:|---:|---|---|---|---|
| 新規Systems | 16.9994 | 0.78 | 0.78 | 0.025/0.075/0.11 | 0.97/1.02/1.04 | 1/1.05/1.12 | 0.32/0.435/0.47 |
| Customer Support関連・Reliant | 9.8896 | 0.50 | 0.45 | 0.01/0.03/0.05 | 0.94/1/1.05 | 1/1/1 | 0.27/0.35/0.39 |

反証・制約：

Systemsのメモリ比率46%と中国売上26%の循環・規制; CSBGには旧世代装置も含み全額継続課金ではない; 工程統合・競合・供給網/輸送コスト・R&Dと供給拡張。通常SBCと償却を残す。

再計算用の全係数・金融損益・税率・NCI・希薄化分母はJSONとPythonに保存。
### ASE Technology（3711.TW）

先端組立・テスト複雑化をATMへ、汎用EMSは低いAI感応度。ATM+EMSの内部売上二重計上を残余方式で除外。金利と正常持分損益だけ金融損益へ残し、評価・ヘッジ益を年換算しない。

最新一次確認：

- 2026-07-30 / company_actual / Q2 consolidated/ATM/EMS: {"revenue_bn": 191.064, "atm_revenue_bn": 126.148, "ems_reported_revenue_bn": 65.789, "operating_income_bn": 21.134, "parent_income_bn": 21.068, "diluted_shares_bn": 4.505702583, "atm_operating_margin": 0.157, "ems_operating_margin": 0.024, "fx_valuation_and_hedging_gain_bn": 3.637, "equity_method_gain_bn": 2.298}。[一次資料](https://www.sec.gov/Archives/edgar/data/1122411/000095010326011351/dp250868_6k.htm)

- 2026-10-12 / company_actual / Q3 sales-only flash; no Q3 profits: {"q3_revenue_bn": 244.161, "q3_atm_revenue_bn": 151.485, "q3_revenue_qoq": 0.278, "q3_revenue_yoy": 0.448}。[一次資料](https://www.sec.gov/Archives/edgar/data/1122411/000095010326015458/dp254866_6k.htm)

株数：台湾普通株のQ2希薄化4.505703bn。将来4.60/4.65bn、米国ADSへの変換はしない。NCIは正の税後利益2%控除。

終点倍率：AI先端実装とテストの付加価値に加点する一方EMS・資本集約と顧客集中を踏まえ基準19倍。

独自シナリオの主要入力：

|部門|売上校正bn|AI感応割合（独自）|弾性|工程複雑化年率 弱/基準/強|価格係数|能力消化係数|OPM弱/基準/強|
|---|---:|---:|---:|---|---|---|---|
| Assembly/Test/Materials | 555.2660 | 0.60 | 0.70 | 0.01/0.055/0.09 | 0.98/1.02/1.05 | 1/1.06/1.14 | 0.12/0.19/0.25 |
| EMS・連結調整後残余 | 315.1840 | 0.25 | 0.45 | 0/0.01/0.025 | 0.94/1/1.05 | 1/1/1 | 0.02/0.035/0.05 |

反証・制約：

先端実装需要の全額がOSATへ来るわけではなくTSMC等内製と競合; 大顧客集中、設備/人員と減価償却、台湾・為替、テスト時間短縮; EMSの低利益率・部材パススルーが全社売上を大きくするためAI売上純度を過大評価しない。

再計算用の全係数・金融損益・税率・NCI・希薄化分母はJSONとPythonに保存。
### 味の素（2802.T）

ABFは一基板の面積/層数・高機能化とAIチップ出荷へ接続。食品等の大きい非FMはAI予算から直接増やさない。会社事業利益から通常のその他営業費用12bn（年4%増）を控除してIFRS営業利益相当へ橋渡し。

最新一次確認：

- 2026-08-06 / company_actual / Q1 IFRS: {"revenue_bn": 412.105, "business_profit_bn": 60.116, "ifrs_operating_profit_bn": 55.895, "parent_income_bn": 36.452, "basic_weighted_shares_bn": 0.956451886, "diluted_eps": 38.1}。[一次資料](https://www.ajinomoto.co.jp/company/en/ir/event/presentation/main/011111113/teaserItems1/01/linkList/0/link/FY26Q1_Tanshin_E.pdf)

- 2026-08-06 / company_guidance / FY26 revised guidance by division: {"revenue_bn": 1732, "business_profit_bn": 202, "fm_revenue_bn": 120.6, "fm_business_profit_bn": 65.5, "parent_income_bn": 123.5}。[一次資料](https://www.ajinomoto.co.jp/company/en/ir/event/presentation/main/011111113/teaserItems1/01/linkList/02/link/FY26Q1_Forecast_E.pdf)

- 2026-06-30 / company_strategy / ABF business technology briefing: {"company_ABF_share": "more than95% of target insulation film market", "new_Gifu_start": "2032, outside horizon"}。[一次資料](https://www.ajinomoto.co.jp/company/en/ir/event/business_briefing/main/011117/teaserItems1/01/linkList/03/link/20260630_presentation_E.pdf)

株数：最新平均956.452m、希薄化EPS38.10対基本38.11。将来960/965m、2025年以前の株数を流用しない。

終点倍率：材料の認定・高シェアと食品収益の安定性を評価し基準28倍。ABF純粋企業と同じ全社成長倍率にはしない。

独自シナリオの主要入力：

|部門|売上校正bn|AI感応割合（独自）|弾性|工程複雑化年率 弱/基準/強|価格係数|能力消化係数|OPM弱/基準/強|
|---|---:|---:|---:|---|---|---|---|
| Functional Materials（ABF等） | 120.6000 | 0.85 | 0.75 | 0.015/0.06/0.09 | 0.98/1.02/1.05 | 1/1/1 | 0.45/0.55/0.6 |
| 非FM事業・配賦後事業利益相当 | 1611.4000 | 0.00 | 0.00 | 0/0/0 | 1/1/1 | 1/1/1 | 0.075/0.09/0.105 |

反証・制約：

事業利益はIFRS営業利益と異なり持分損益を含む。部門別正常化は粗い; 食品・冷食原材料と価格転嫁、医薬CDMO・R&D、人件費、全社費用がEPSを左右; ABF95%超は半導体材料全体のシェアではない。将来シェア上昇を仮定しない。

再計算用の全係数・金融損益・税率・NCI・希薄化分母はJSONとPythonに保存。

正常化：通常のその他営業費用を12bn校正し控除。事業利益に含まれる通常持分利益は残余の校正内、金融へ再加算しない。
### イビデン（4062.T）

CPU/GPU/スイッチ基板の大型・多層化と価格/新ライン歩留まりを電子へ。会社550bnをQ1売上構成で校正するため部門年売上は独自配分。遊休設備償却を金融等費用に残し、株売却益を除外。

最新一次確認：

- 2026-08-04 / company_actual / FY26 Q1 formal consolidated release: {"revenue_bn": 123.219, "operating_income_bn": 26.88, "parent_income_bn": 17.918, "electronic_external_revenue_bn": 77.522, "electronic_op_bn": 21.375, "inactive_asset_depreciation_nonop_bn": 0.834, "diluted_eps_presplit": 60.76, "issued_shares_bn_presplit": 0.281944019}。[一次資料](https://www.ibiden.com/ir/items/tannshinn2026Q1.pdf)

- 2026-08-04 / company_guidance / FY26 formal full-year forecast: {"revenue_bn": 550, "operating_income_bn": 127, "parent_income_bn": 84, "basic_eps_post_October_split": 149.68, "October1_split_ratio": 2}。[一次資料](https://www.ibiden.com/ir/items/tannshinn2026Q1.pdf)

株数：1/1と10/1の各1:2分割を混同しない。Q1希薄化NI/EPS×2≈0.5898bn（CB利息調整等で概数）と7月転換を踏まえ将来0.600/0.606bn。

終点倍率：高付加価値基板の技術・顧客認定を評価するが、顧客集中・価格循環・巨額capexを反映して基準24倍。

独自シナリオの主要入力：

|部門|売上校正bn|AI感応割合（独自）|弾性|工程複雑化年率 弱/基準/強|価格係数|能力消化係数|OPM弱/基準/強|
|---|---:|---:|---:|---|---|---|---|
| 電子事業 | 346.0270 | 0.80 | 0.75 | 0.01/0.065/0.1 | 0.92/1.02/1.07 | 1.02/1.13/1.25 | 0.22/0.31/0.38 |
| セラミック | 108.7555 | 0.10 | 0.35 | 0/0.01/0.02 | 0.94/1/1.05 | 1/1/1 | 0.07/0.12/0.16 |
| その他 | 95.2085 | 0.05 | 0.30 | 0/0/0.01 | 0.94/1/1.05 | 1/1/1 | 0.07/0.105/0.13 |

反証・制約：

基準利益率31%は不足プレミアム・稼働率と新棟歩留まりに依存; 膨大なcapexのCF支出はPERモデルに含まれず、償却とCFを分ける; 同日付近説明PDFの数値と正式8/4短信に不整合があるため正式短信を優先した。旧メモの580/120/70bnを使用しない。

再計算用の全係数・金融損益・税率・NCI・希薄化分母はJSONとPythonに保存。

正常化：投資有価証券売却益等を将来へゼロ延長。通常償却・R&D・株式報酬は費用に残す。; Q1遊休設備償却834mは営業外費用。将来net_finance−5bn等に正常な金利・遊休償却を含む。
### Unimicron（3037.TW）

ABF需要をAIチップ面積・層数と能力認定へ、他PCBは低いAI感応度へ接続。Q2の巨額営業外益を延長せず、営業利益と通常金利から純利益を計算。

最新一次確認：

- 2026-07-29 / company_actual / Q2 company earnings deck: {"revenue_bn": 42.89, "operating_income_bn": 6.651, "net_nonoperating_income_bn": 8.925, "parent_income_bn": 13.115, "diluted_eps": 8.38, "abf_revenue_mix": 0.52, "q2_DA_bn": 5.109}。[一次資料](https://www.unimicron.com/files/money/Earnings/en/2026-Q2-consolidated-en.pdf)

- 2026-10-18 / company_actual / Official monthly sales page checked as of Oct18; release date not stated on page: {"july_revenue_bn": 16.253637, "august_revenue_bn": 17.745519, "september_revenue_bn": 18.650679, "q3_revenue_bn_derived": 52.649835, "q3_profit": "not yet published"}。[一次資料](https://www.unimicron.com/money01.html)

株数：Q2親会社利益/希薄化EPSから約1.565bnの分母水準（EPS丸め・CB調整で厳密ではない）。将来1.60/1.63bnを置き、調達・希薄化に余裕。

終点倍率：ABF材料・基板の認定は評価するが、供給能力の循環と営業外益依存を踏まえ基準22倍。

独自シナリオの主要入力：

|部門|売上校正bn|AI感応割合（独自）|弾性|工程複雑化年率 弱/基準/強|価格係数|能力消化係数|OPM弱/基準/強|
|---|---:|---:|---:|---|---|---|---|
| ABF基板 | 99.3614 | 0.85 | 0.75 | 0.01/0.065/0.1 | 0.91/1.03/1.09 | 1.02/1.12/1.25 | 0.15/0.29/0.38 |
| BT/HDI/PCB/FPC等 | 91.7182 | 0.25 | 0.45 | 0/0.02/0.035 | 0.94/1/1.05 | 1/1/1 | 0.035/0.105/0.16 |

反証・制約：

Q2営業外益が営業利益を超える。EPS8.38の4倍を正常利益にしない; ABF新能力、原材料、歩留まり、顧客価格交渉・競合増設、HDI/BTの非AI市況; 部門利益率とAI売上割合の公表はないため独自配分でC評価。ABF52%をAI売上52%と解釈しない。

再計算用の全係数・金融損益・税率・NCI・希薄化分母はJSONとPythonに保存。

正常化：Q2 net nonop+8.925bnを年換算せず、正常net_finance−2/−1/0bnに置換。; 2026Q2 deckは会社公式ホストから10/18取得。Webテキスト取得失敗のためcurlとpdftotextで本文確認。
### ディスコ（6146.T）

HBM薄化・切断、AIロジックとOSAT設備、稼働に応じる工具を加重した工程需要モデル。装置/工具の最新精密構成が未取得なので公表されないTAMシェアを作らず全社校正。

最新一次確認：

- 2026-07-23 / company_actual / Q1 consolidated actual: {"revenue_bn": 114.308, "operating_income_bn": 49.033, "parent_income_bn": 34.221, "basic_eps": 315.51, "issued_shares_bn": 0.108483729, "treasury_shares_bn": 1.6004e-05}。[一次資料](https://www.disco.co.jp/eg/ir/library/doc/fr/fr20260723.pdf)

- 2026-10-06 / company_actual / Q2 nonconsolidated flash only: {"q2_sales_bn": 118.5, "q2_shipments_bn": 123.9, "q2_shipments_yoy": 0.6, "q2_consolidated_profit": "not released; scheduledOct22"}。[一次資料](https://www-hq.disco.co.jp/eg/ir/library/doc/news/202610061_Preliminary_Report_on_Non-Consolidated_Sales_Figures_and_Shipment_Figures_(Second_Quarter_of_Fiscal_Year_2026).pdf)

- 2026-07-23 / company_plan / investment and R&D plan: {"FY26_capex_bn": 33, "FY26_RD_bn": 38, "FY26_depreciation_bn": 16}。[一次資料](https://www.disco.co.jp/eg/ir/library/doc/film/20260723_note.pdf)

株数：Q1発行108.484m・自己16,004株、将来109/109.5m（独自希薄化、株価53,850円と同じ普通株基準）。

終点倍率：加工技術と稼働連動工具、財務健全性を評価し基準34倍。ただし設備循環のため永続的倍率とはしない。

独自シナリオの主要入力：

|部門|売上校正bn|AI感応割合（独自）|弾性|工程複雑化年率 弱/基準/強|価格係数|能力消化係数|OPM弱/基準/強|
|---|---:|---:|---:|---|---|---|---|
| 精密加工装置・工具・保守（連結全体） | 457.2320 | 0.65 | 0.70 | 0.015/0.06/0.09 | 0.97/1.02/1.04 | 1/1.05/1.12 | 0.33/0.44/0.49 |

反証・制約：

出荷と検収売上は違う。10/6単体速報を連結利益へ置換しない; 新設備需要は稼働が満たされると一服。工程変更・並列化・顧客投資前倒し; 基準OPM44%は足元42.9%近傍。R&D/人件費/償却を除外して利益率を作らない。

再計算用の全係数・金融損益・税率・NCI・希薄化分母はJSONとPythonに保存。
### Teradyne（TER）

SoC/メモリのテスト複雑化とAI設備増を半導体テストへ、Product Test・ロボティクスは別の低い感応度へ接続。Advantestとの競争によるシェア上昇を無条件に仮定しない。

最新一次確認：

- 2026-07-28 / company_actual / Quarter ended June28 actual; callJuly29: {"revenue_bn": 1.329, "semi_test_bn": 1.122, "product_test_bn": 0.107, "robotics_bn": 0.1, "gaap_parent_income_bn": 0.3745, "diluted_shares_bn": 0.1577, "h1_gaap_operating_income_bn": 0.9108}。[一次資料](https://investors.teradyne.com/news-events/press-releases/detail/445/teradyne-reports-second-quarter-2026-results)

- 2026-07-28 / company_quarter_guidance / Q3 guidance: {"revenue_range_bn": [1.2, 1.3], "gaap_eps_range": [1.79, 2.09]}。[一次資料](https://investors.teradyne.com/news-events/press-releases/detail/445/teradyne-reports-second-quarter-2026-results)

株数：最新Q2希薄化157.7m。将来160/162m、未発表買戻しは含まない。

終点倍率：AIテストの成長・製品多様性を評価し基準26倍。競争・非半導体の収益性を加味し最上位の独占倍率を自動適用しない。

独自シナリオの主要入力：

|部門|売上校正bn|AI感応割合（独自）|弾性|工程複雑化年率 弱/基準/強|価格係数|能力消化係数|OPM弱/基準/強|
|---|---:|---:|---:|---|---|---|---|
| Semiconductor Test | 4.4880 | 0.70 | 0.70 | 0.01/0.07/0.11 | 0.97/1.02/1.04 | 1/1.04/1.1 | 0.28/0.39/0.44 |
| Product Test | 0.4280 | 0.35 | 0.45 | 0/0.025/0.04 | 0.94/1/1.05 | 1/1/1 | 0.09/0.17/0.22 |
| Robotics | 0.4000 | 0.05 | 0.30 | 0/0.01/0.02 | 0.94/1/1.05 | 1/1/1 | -0.05/0.08/0.15 |

反証・制約：

半導体テストの急増四半期からの校正。Q3会社予想はQ2より低い売上を示す; HBM/GPU等の顧客採用、並列化・テスト短縮、Advantestとの競争; Roboticsの回復遅れ、ERP/人件費とR&D。通常のSBC・買収償却・持分投資償却を除外しない。

再計算用の全係数・金融損益・税率・NCI・希薄化分母はJSONとPythonに保存。

## とくに残る制約

SUMCOはFSTの9/30みなし連結除外により、過去売上と将来連結売上の範囲が変わる。今回40bnJPYを独自控除したため、精密な継続事業予測として扱えない。SiltronicはEBITDAが黒字でも巨大償却により最終赤字。基準ケースの利益回復には大きな稼働/価格改善が必要。Unimicronは巨額営業外益を延長しない。イビデンは8/4正式短信と8/5説明資料メモの数値不整合を残し、正式短信の550/127/84bnを採用。

校正年の季節性、為替、通貨別売上・費用、投資回収CFの年次積上げを省略したスクリーニングモデル。売上成長率とEPS成長率が企業間で違う理由を見せるもので、1円単位の目標株価を保証しない。Q2未発表の会社に10月後半以後の決算を先取りしない。
