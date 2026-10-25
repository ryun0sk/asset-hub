# AI46社拡張：担当14社の2028/29年EPS試算（2026-10-18）

全84ケースは独自の将来シナリオ。会社予想・市場予想ではない。金額・株数はそれぞれ財務通貨の十億単位・十億株、EPSは現地普通株1株。LenovoだけUSD利益を固定USDHKD7.84719992で一度HKDへ換算する。株価を使って利益を逆算・調整していない。

`python3 research/themes/ai-valuation-ranking/2026-10-18/inputs/compute.py` でJSONと本メモを再生成できる。

## 主要結果（EPS、弱気／基準／強気）

|企業|通貨|2028弱|基準|強|2029弱|基準|強|モデル確度|
|---|---|---:|---:|---:|---:|---:|---:|---|
|AMD|USD|3.33|10.51|16.51|3.12|16.62|28.83|medium_low|
|SK hynix|KRW|59,930.67|234,295.18|437,667.56|38,359.83|262,034.79|552,706.08|medium_low|
|Samsung Electronics|KRW|4,670.98|30,717.36|65,529.72|430.79|31,103.71|76,843.06|medium_low|
|Micron|USD|23.99|89.94|169.66|14.35|94.01|199.29|medium_low|
|Sandisk|USD|14.23|80.81|189.51|3.50|85.53|205.30|medium_low|
|富士通|JPY|123.29|204.97|297.30|120.11|220.62|344.39|medium|
|NEC|JPY|156.23|240.32|346.29|150.08|252.36|396.01|medium_low|
|Dell Technologies|USD|11.95|29.81|49.37|11.58|35.58|63.94|medium|
|Hewlett Packard Enterprise|USD|1.66|3.87|6.02|1.63|4.51|7.50|medium_low|
|Super Micro Computer|USD|0.78|4.40|11.07|0.72|5.50|14.67|low|
|Lenovo|HKD|0.43|2.01|3.78|0.40|2.35|4.78|medium_low|
|Quanta Computer|TWD|13.93|37.68|64.58|13.41|45.30|82.59|medium_low|
|Wiwynn|TWD|59.47|173.11|312.86|56.74|218.65|418.81|low|
|Hon Hai Precision|TWD|10.70|23.11|36.84|10.27|27.52|46.88|medium_low|

## 読み方・共通の限界

- 2028/29は暦年相当の通年利益水準。厳密な決算期積上げではない。基準ケースに確率は付けない。
- AI支出2028=1.0/1.4/1.9兆USD、2029=0.95/1.7/2.5兆USD。サーバー/ストレージ工程の売上機会は独自に2028=500/800/1150bnUSD、2029=475/1050/1600bnUSD。ODM売上とOEM売上、GPU/メモリ売上は費用を内包するため合計しない。
- メモリのNAND数量・ASPは既存キオクシアと同じ経路。DRAM/HBMは別の数量・単価を置く。HBMが汎用DRAMより高収益だと固定しない。2026の汎用DRAM価格急騰はHBMの利益率を超えるため、HBM比率上昇だけで利益率改善とは限らない。
- メモリの基準2028/29にはASP調整を置き、MU等の「2027/28供給不足」という会社見通しを全面延長していない。基準でも高収益が残る仮定で、循環中立利益と同義ではない。
- HBM/汎用DRAM/NANDの製品別費用は未開示のため独自配賦。Korean現地通貨アンカーとUSD市場推計には平均為替・期間の差がある。将来の量/ASP指数を比較するための校正値で、将来の金額シェアと混同しない。
- SBC、通常償却、研究開発費を費用に残す。金融資産評価益、持分売却益、ワラント評価損益、例外税便益を反復利益へ延長しない。既存保有資産価値はゼロとみなすわけではなく、利益倍率とは別評価。
- capexと運転資金はEPSから重複控除せず、費用に残す償却と資金負担の注意を分けて保存した。MU等の顧客前受金は将来返済義務があり恒久的余剰資金ではない。
- PE仮定は独自の事前設定。将来EPS×仮定PEの価格条件は実績PER/会社予想PERやDCFではない。

## 企業別の根拠と仮定

### AMD（AMD）

AIアクセラレータ売上はNVIDIA・Broadcomと共有する電子部品売上プール×独自の実効捕捉係数。会社開示のデータセンター売上をInstinctとEPYC等へ独自に分け、PC・ゲーム・組込みを別計算する。部門利益から株式報酬・買収償却・本社費用を残して正常利益を算出する。

株数・通貨：Q2 EPS-implied diluted anchor ~1.665bn (rounding); forecast 1.74–2.04bn includes SBC and partial/full 320m conditional warrant effect, not immediate guaranteed issuance.

仮定終点PER（弱/基準/強）：22/30/38倍。

一次アンカー（実績/会社予想は各scope/typeで区別）：
- [2026-08-04 Q2 ended 2026-06-27, consolidated GAAP actual; Q3 company guide](https://ir.amd.com/financial-information/sec-filings/content/0000002488-26-000121/q22026991.htm)：`{"revenue_bn":11.536,"operating_income_bn":1.99,"net_income_bn":2.297,"diluted_eps":1.38,"data_center_revenue_bn":6.718,"client_bn":3.062,"gaming_bn":0.779,"embedded_bn":0.977,"Q3_revenue_guide_bn":13.0}`
- [2026-08-05 conditional financing dilution; not vested sales](https://www.sec.gov/Archives/edgar/data/2488/000000248826000123/amd-20260627.htm)：`{"OpenAI_max_warrant_shares_bn":0.16,"Meta_max_warrant_shares_bn":0.16,"none_vested_at_2026_06_27":true}`

成立条件：MI450以降の顧客採用が進みAIプールの取り分が増えることが必要で、CUDA・ASICとの競争と最大3.2億株の条件付き希薄化が主要リスク。

反証・監視点：2029年基準のAIプール捕捉7.5%は独自仮定で、現在の観測シェアではない／CUDA・NVIDIA・専用ASICとの競争でGPU採用が伸びない可能性／HBM・実装能力、顧客の導入時期、中国輸出規制／顧客向け最大3.2億株の条件付きワラントと継続的な株式報酬による希薄化

### SK hynix（000660.KS）

HBM・汎用DRAM・NANDを重複なく分け、2026年4〜6月の校正売上×出荷ビット数×単価×独自の製品構成・捕捉係数で予測する。数量とビット原価から製造費を計算し、研究開発・減価償却・株式報酬等の固定費を残す。NANDの数量・単価経路は既存キオクシア試算と統一した。製品別売上・原価の内訳は独自配賦で、会社開示値ではない。

株数・通貨：8/19 SEC total issued ~730.4923m inferred from stated 1% limit; treasury 1.625769m before planned24.07m buyback. Forecast 705–715m diluted allows announced cancellation plus SBC; planned buyback is not assumed completed at cutoff.

仮定終点PER（弱/基準/強）：8/11/15倍。

一次アンカー（実績/会社予想は各scope/typeで区別）：
- [2026-07-29 Q2 consolidated K-IFRS preliminary actual, KRW bn](https://news.skhynix.com/en/q2-2026-business-results/)：`{"revenue_bn":79318.7,"operating_income_bn":60542.6,"net_income_bn":93922.6}`
- [2026-08-18 Q2 financial income in KRW bn; excluded from projected recurring profit](https://www.sec.gov/Archives/edgar/data/2120882/000119312526354777/d147827d6k.htm)：`{"dividend_income_bn":10027.945,"fair_value_gains_bn":53237.425,"parent_net_income_bn":93820.236}`
- [2026-08-19 shareholder capital actions](https://www.sec.gov/Archives/edgar/data/2120882/000119312526356133/d428222d6k.htm)：`{"planned_buyback_shares_bn":0.02407,"planned_cost_KRW_bn":40004.34,"period_ends":"2026-11-19","treasury_pre_buyback_bn":0.001625769}`
- [2026-09-07 external original Q2 estimates; not issuer segments](https://www.trendforce.com/presscenter/news/20260907-13219.html)：`{"SK_DRAM_USD_bn":38.59,"global_DRAM_USD_bn":154.73}`
- [2026-08-18 external original Q2 estimates](https://www.trendforce.com/presscenter/news/20260818-13186.html)：`{"SK_group_NAND_USD_bn":14.27}`

成立条件：金融評価益を除いてもHBM量産と汎用DRAMの利益が残ることが成立条件で、価格調整・競合増産・新工場の償却負担でEPSが大きく振れる。

反証・監視点：Q2純利益には多額の配当・金融商品評価益があり、将来の反復利益へ延長しない／HBM4の歩留まり・顧客集中、Samsung・Micronへの取り分流出／HBMと汎用DRAMの単価・利益率は異なり、HBM比率だけで収益改善を保証しない／汎用DRAM/NANDの値下がりと新工場・先端実装の償却負担。保有金融資産の価値は別評価が必要

### Samsung Electronics（005930.KS）

HBM・汎用DRAM・NANDの数量、単価、ビット原価を別計算し、ファウンドリ等と端末・ディスプレー等を加える。部門間売上の重複を消去し、株式報酬・償却・研究開発費を残す。普通株と参加型優先株の利益分配を考慮した株数でEPSを計算する。10月8日のQ3速報は会社の予備見通しで、詳細費用の校正はQ2を使う。

株数・通貨：Common and participating preferred EPS are equal in Q2. Denominator is combined earnings-participating equivalent shares (issued6.64865bn less treasury0.08209bn), not ordinary5.84628bn alone. Forecast6.60–6.70bn includes SBC; EPS per005930 ordinary equivalent.

仮定終点PER（弱/基準/強）：9/12/16倍。

一次アンカー（実績/会社予想は各scope/typeで区別）：
- [2026-07-30 Q2 consolidated and semiconductor results KRW bn](https://images.samsung.com/is/content/samsung/assets/global/ir/docs/2026_2Q_conference_eng.pdf)：`{"consolidated_revenue_bn":171500,"operating_income_bn":89490,"DS_revenue_bn":127500,"DS_operating_income_bn":89200,"memory_revenue_bn":120800,"ordinary_and_preferred_eps_KRW":10849}`
- [2026-10-08 Q3 management preliminary guidance, NOT full financial statements](https://news.samsung.com/global/samsung-electronics-announces-earnings-guidance-for-third-quarter-2026)：`{"revenue_KRW_bn":195000,"operating_income_KRW_bn":107400,"no_Q3_net_income_or_EPS_guidance_in_this_release":true}`
- [2026-06-30 Q2 share structure period, retrieved10/18](https://www.samsung.com/global/ir/stock-information/listing-Info/)：`{"common_issued_bn":5.846278608,"preferred_issued_bn":0.802371203,"common_treasury_bn":0.082086705}`
- [2026-08-18 external original Q2 estimates](https://www.trendforce.com/presscenter/news/20260818-13186.html)：`{"Samsung_NAND_USD_bn":23.06,"NAND_share":0.293}`
- [2026-09-07 external original Q2 estimates](https://www.trendforce.com/presscenter/news/20260907-13219.html)：`{"Samsung_DRAM_USD_bn":60.98,"DRAM_share":0.394}`

成立条件：HBMの顧客認定・量産を進めつつ汎用メモリの価格調整を吸収する必要があり、ファウンドリの赤字と大型投資が利益回復を妨げる可能性。

反証・監視点：Q3速報の高利益をそのまま恒常利益として年率換算しない／メモリ製品別の売上・費用配分は独自仮定で、HBM認定と歩留まりも不確実／端末部門のメモリ調達費と半導体部門の利益が逆方向に動く場合がある／大型設備投資・株式報酬、普通株と優先株の配分、中国メモリメーカーの増産

### Micron（MU）

HBM・汎用DRAM・NAND・その他を分離し、共通の2026年4〜6月の校正売上に出荷数量・単価・費用を掛ける。最新8月期四半期と会社の2027/28年供給不足見通しは別の実績・会社見通しとして示し、独自基準には2028/29年の単価調整を置く。株式報酬・研究開発・通常償却は除外しない。

株数・通貨：Latest Q4 diluted1.147bn, Q1FY27 guide~1.15bn. Forecast1.17–1.21bn includes continuing SBC; no unannounced buyback assumed.

仮定終点PER（弱/基準/強）：8/12/16倍。

一次アンカー（実績/会社予想は各scope/typeで区別）：
- [2026-09-30 FY26/Q4 consolidated GAAP actual and Q1FY27 guide](https://investors.micron.com/news/press-release/2026/Micron-Technology-Inc--Reports-Record-Fiscal-Fourth-Quarter-and-Full-Year-2026-Results/default.aspx)：`{"FY_revenue_bn":133.188,"FY_operating_income_bn":99.34,"FY_net_income_bn":84.969,"FY_diluted_eps":74.33,"Q4_revenue_bn":54.229,"Q4_operating_income_bn":43.751,"Q4_net_income_bn":37.701,"Q4_diluted_shares_bn":1.147,"Q1FY27_revenue_guide_bn":61.5,"Q1FY27_GAAP_EPS_guide":37.84}`
- [2026-09-30 latest product results and company outlook, not our forecasts](https://investors.micron.com/files/doc_financials/2026/q4/Q4-26-Earnings-Deck.pdf)：`{"Q4_DRAM_revenue_bn":39.8,"Q4_NAND_revenue_bn":14.1,"Q4_DC_SSD_revenue_nearly_bn":10,"expected_2027_2028_DRAM_bit_growth":"low20s_pct","expected_NAND_bit_growth":"mid20s_pct","SCAs_signed":26,"estimated_revenue_share_through2030":">35%","customer_financial_commitments_bn":32}`
- [2026-10-09 10K annual actual and contract footnote](https://www.sec.gov/Archives/edgar/data/723125/000072312526000023/mu-20260903.htm)：`{"SBC_bn":1.285,"RPO_bn":134,"customer_contract_liabilities_bn":13,"deposits_repayment":"mostly2029–2031","normal_effective_tax_rate_FY26":0.148}`
- [2026-09-07 common CYQ2 industry calibration, separate from later FYQ4](https://www.trendforce.com/presscenter/news/20260907-13219.html)：`{"Micron_DRAM_bn":36}`
- [2026-08-18 common CYQ2 calibration](https://www.trendforce.com/presscenter/news/20260818-13186.html)：`{"Micron_NAND_bn":11.85}`

成立条件：価格バンド付き契約とHBM・企業向けSSDが利益を支えることが必要で、メモリ単価正常化と新工場投資・顧客前受金返済が主要リスク。

反証・監視点：会社は2027/28年も供給不足を予想するが、独自基準はその見通しを全面延長していない／HBMの内訳は独自配賦で、共通Q2校正と最新四半期には価格・期間の差がある／複数年契約の価格バンドは一部収益を守るが、具体的な下限・製品構成は非公開／新工場・実装投資、中国競争、顧客前受金の2029〜31年返済と運転資金負担

### Sandisk（SNDK）

NANDブランド売上にSSDを含め、出荷ビット数×単価×独自の取り分変化から売上を予測する。JVのウェハ製造をブランド売上へ二重加算しない。株式報酬と研究開発費を残し、株式評価益を除く。会社のFY2028〜30調整後営業利益率75%という長期枠組みより、独自基準は慎重な単価・利益率を置く。

株数・通貨：Q4 diluted157m vs basic147m; economic forecast160–165m retains SBC/equity-award dilution and does not assume full15.5bn buyback completion.

仮定終点PER（弱/基準/強）：8/12/16倍。

一次アンカー（実績/会社予想は各scope/typeで区別）：
- [2026-08-05 FY26/Q4 unaudited GAAP and next-quarter management guide](https://www.sandisk.com/company/newsroom/press-releases/2026/2026-08-05-sandisk-reports-fiscal-fourth-quarter-2026-financial-results)：`{"FY_revenue_bn":20.248,"FY_operating_income_bn":12.389,"FY_net_income_bn":11.433,"FY_diluted_eps":73.76,"Q4_revenue_bn":8.965,"Q4_gross_margin":0.846,"Q4_op_income_bn":7.037,"Q4_net_income_bn":6.903,"Q4_equity_gain_bn":0.804,"Q4_SBC_bn":0.067,"Q4_diluted_shares_bn":0.157,"Q1FY27_revenue_guide_bn":[10.3,10.8],"Q1FY27_adjusted_EPS_guide":[44,46]}`
- [2026-08-17 audited FY26 consolidated actual and share structure](https://www.sec.gov/Archives/edgar/data/2023554/000162828026057406/sndk-20260703.htm)：`{"revenue_bn":20.248,"operating_income_bn":12.389,"net_income_bn":11.433,"diluted_shares_bn":0.155,"dilution_instruments":"employee_RSU_PSU_ESPP_no_convertible_needed"}`
- [2026-08-13 company FY2028–FY2030 longterm nonGAAP framework, NOT our base assumptions](https://www.sandisk.com/company/newsroom/press-releases/2026/2026-08-13-sandisk-investor-day-2026)：`{"revenue_growth":"mid_to_high_teens_pct","gross_margin":0.8,"operating_margin":0.75,"adjusted_FCF_margin":0.5,"NBM_FY27_bit_coverage":"~50%","NBM_FY28_bit_coverage":"~two_thirds"}`
- [2026-08-18 common Q2 brand NAND calibration; SSD included](https://www.trendforce.com/presscenter/news/20260818-13186.html)：`{"SanDisk_NAND_Q2_USD_bn":8.97,"global_NAND_Q2_derived_bn":78.82352941176471}`

成立条件：NBM契約と企業向けSSDでNAND価格・利益率を維持できるかが核心で、会社の長期75%調整後営業利益率を下回る独自基準では割安度が縮む。

反証・監視点：直近四半期の株式評価益0.804bnUSDを反復利益に含めない／企業向けSSD・NBM契約は支えになるが、NANDの単価循環は残る／JV投資と顧客前受金は現金の自由度に影響する／独自基準は会社の長期調整後利益率75%を下回る。HBFの追加利益は織り込まない

### 富士通（6702.T）

Service Solutions内のUvanceと残りのサービスを重複なく分け、ハードウェア・端末と部門間売上消去を加える。Uvance全体をAI売上とは扱わず、企業IT需要とAI導入の弾性を別に置く。本社費用・株式報酬・通常償却を残し、過去の事業売却利益を除く。

株数・通貨：Q1 diluted EPS ~1.7404bn implied; 2028/29 economic diluted1.70–1.76bn after announced-program calibration, not a guaranteed future buyback.

仮定終点PER（弱/基準/強）：14/20/26倍。

一次アンカー（実績/会社予想は各scope/typeで区別）：
- [2026-07-30 FY26Q1 actual and FY26 endingMarch2027 company guide, JPYbn](https://resources.global.fujitsu/prir/2026/07/2026Q1-Financial-Results-en.pdf)：`{"Q1_revenue":779.377,"Q1_GAAP_OP":52.534,"Q1_parent_NI":40.134,"Q1_diluted_EPS":23.06,"issued_shares_bn":1.739778265,"treasury_shares_bn":0.00500098,"FY_revenue_guide":3510,"FY_GAAP_OP_guide":415,"FY_parent_NI_guide":310}`
- [2026-07-30 company FY26 segment plan, JPYbn; Uvance included within services](https://resources.global.fujitsu/prir/2026/07/2026Q1-Financial-Summary-en.pdf)：`{"service_solutions_revenue":2470,"hardware_solutions_revenue":960,"ubiquitous_revenue":160,"revenue_elimination":-80,"Uvance_revenue":840,"service_adjusted_OP":430,"corporate_adjusted_cost":95,"GAAP_adjustment_cost":10}`

成立条件：AI導入で工数を削減し価値に応じた価格を維持することが必要で、既存業務の置換と値下げで増益効果が相殺されるリスク。

反証・監視点：AIによる生産性改善分が人月単価の低下として顧客へ還元される可能性／Uvanceには既存業務からの移行があり、すべてが新規AI需要ではない／海外再編と不採算プロジェクト／前期の非継続事業利益を将来EPSの起点にしない

### NEC（6701.T）

国内ITをBluStellarと既存業務に分け、海外IT・CSG・社会インフラ等を別に計算する。会社の年間見通しはCSGを含まないため、CSG通年売上2000億円を独自の橋渡し仮定として追加する。本社費用と通常の買収償却・株式報酬を控除し、会社Non-GAAP利益をそのままEPSにしない。

株数・通貨：2025 five-for-one split reflected; Q1 average1.326343bn. Forecast1.34–1.37bn diluted retains SBC; old pre-split EPS not used.

仮定終点PER（弱/基準/強）：16/22/28倍。

一次アンカー（実績/会社予想は各scope/typeで区別）：
- [2026-07-29 Q1FY27/3 actual and revised full-year company forecast, JPYbn](https://group.nec/assets/global/en/about/ir/library/pdf/202607/2907-01-01.pdf)：`{"Q1_revenue":819.774,"Q1_GAAP_OP":58.77,"Q1_nonGAAP_OP":74.738,"Q1_parent_NI":49.698,"Q1_EPS":37.47,"average_ordinary_shares_bn":1.326343019,"FY_revenue_guide":3540,"FY_nonGAAP_OP_guide":430,"FY_nonGAAP_parent_NI_guide":290}`
- [2026-07-29 company annual segment guide excludes CSG acquisition; JPYbn](https://group.nec/assets/global/en/about/ir/library/pdf/260729/260729-01.pdf)：`{"BluStellar_domestic_IT":760,"legacy_domestic_IT":1415,"international_IT":450,"social_infrastructure":780,"other":135,"corporate_nonGAAP_cost":54,"CSG_not_in_annual_guide":true}`

成立条件：BluStellarの単価・生産性改善とCSG統合が成立する必要があり、CSGの独自寄与仮定と買収償却・案件損失で利益が下振れし得る。

反証・監視点：CSG通年寄与と統合費用は独自仮定で、会社の年間見通しは買収後へ未更新／BluStellarには既存業務の移行が含まれ、すべてが新規AI売上ではない／会社Non-GAAP見通しで除外する株式報酬・買収償却を当モデルでは費用に残す／防衛・海底ケーブルの受注循環、案件損失・納期リスク

### Dell Technologies（DELL）

AIサーバーはFY27会社見通し740億USDを将来校正に用い、従来型ISGとPCは最新四半期を年換算する。AI売上はサーバー工程の市場規模×独自の取り分へ連動させる。AI単独の利益率は非開示のため独自仮定とし、本社費用・株式報酬・買収償却を残す。

株数・通貨：Q2 diluted652m; future630–660m, modest buyback assumption offset by SBC.

仮定終点PER（弱/基準/強）：10/15/20倍。

一次アンカー（実績/会社予想は各scope/typeで区別）：
- [2026-09-01 Q2FY27 consolidated GAAP actual and full-year issuer guide](https://investors.delltechnologies.com/sec-filings/all-sec-filings/content/0001571996-26-000039/exhibit991earnings8kq2fy27.htm)：`{"Q2_revenue_bn":46.971,"Q2_OP_bn":5.385,"Q2_parent_NI_bn":4.133,"Q2_diluted_shares_bn":0.652,"Q2_AI_servers_bn":16.401,"Q2_traditional_server_network_bn":10.531,"Q2_storage_bn":4.85,"Q2_CSG_bn":15.034,"Q2_CFO_bn":2.225,"Q2_unadjusted_FCF_bn":0.986,"FY27_revenue_guide_bn":192,"FY27_AI_server_guide_bn":74,"FY27_GAAP_EPS_guide":24.37,"AI_orders_bn":60.9,"AI_backlog_bn":95}`

成立条件：受注残の売上化に加えAIサーバーの利益率と代金回収が維持される必要があり、GPU仕入高だけの売上成長と運転資金増が主要リスク。

反証・監視点：受注残は売上・回収を保証しない。Q2通常FCF0.986bnUSDと調整後8.149bnUSDには顧客金融等の差がある／GPU等の仕入高を含む売上拡大とAI単独の利益率を混同しない／ODMとの競争とNVIDIA標準設計による交渉力の制約／顧客金融・売掛金・在庫の資金需要が買戻し余力を制限する

### Hewlett Packard Enterprise（HPE）

最新四半期のサーバー売上を独自にAI40%・従来型60%へ分け、ストレージ・金融・Juniperを含む通信等を計算する。Cloud&AI部門全体をAIとは扱わず、買収による売上増と有機成長を区別する。株式報酬・無形資産償却等を残し、H3C等の売却益を反復金融利益から除く。

株数・通貨：Q3 diluted1.449bn includes if-converted effects. Forecast1.46–1.52bn after preferred conversion: no double subtraction of preferred dividends on if-converted earnings.

仮定終点PER（弱/基準/強）：10/14/18倍。

一次アンカー（実績/会社予想は各scope/typeで区別）：
- [2026-09-02 Q3FY26 issuer results and outlook; Cloud&AI includes nonAI](https://www.hpe.com/us/en/newsroom/press-release/2026/09/hpe-reports-fiscal-2026-third-quarter-results.html)：`{"Q3_revenue_bn":12.213,"Q3_GAAP_OP_margin":0.114,"Q3_networking_revenue_bn":2.9,"Q3_cloud_AI_revenue_bn":9.0,"Q3_all_servers_bn":6.8,"Q3_storage_bn":1.3,"Q3_financial_services_bn":0.9,"FY26_GAAP_EPS_guide":[2.93,3.03],"FY27_revenue_growth_guide":[0.13,0.17],"FY27_nonGAAP_OP_margin_guide":[0.14,0.15]}`
- [2026-09-02 Q3 GAAP actual/reconciliation](https://www.hpe.com/content/dam/hpe/newsroom/2026/09/HPE_Q3FY26_earnings_financial_tables.pdf)：`{"OP_bn":1.393,"net_earnings_bn":1.54,"equity_sale_gain_bn":0.444,"SBC_bn":0.165,"intangibles_amort_bn":0.315,"diluted_shares_bn":1.449,"CFO_bn":1.6,"FCF_bn":1.0}`

成立条件：Juniperを含む通信部門の採算とAIサーバーの売上化が維持される必要があり、買収負債・無形資産償却と顧客金融が利益・現金の伸びを抑える。

反証・監視点：AIサーバー売上割合は会社非開示で、出荷・検収の時期も変動する／Juniperの統合、負債と買収無形資産の償却負担／通信機器競争とサーバー部材価格／金融債権と顧客の設備資金需要

### Super Micro Computer（SMCI）

FY27会社売上見通し650〜720億USDの中点を将来校正に使い、AI80%・その他20%へ独自配分する。AI売上はサーバー市場×独自の取り分に連動し、基準ではシェア低下を置く。株式報酬・研究開発・償却を費用に残す。8月31日の監査済み10-Kで通期の売上・利益・営業CFが8月11日速報と一致することを確認した。

株数・通貨：2024年1:10分割後。6/30普通株656.882499m＋優先株4.3125m×転換率30.3040〜36.3640＝130.689〜156.819750m＋既存CB全転換73.803045m。潜在株合計は最小861.374544m、最大887.505294m。現金決済の資金手当を仮定せず最大側に将来株式報酬を上乗せし、2028年930/950/980m、2029年950/980/1020m（弱/基準/強）の経済的希薄化株数を使用する。優先株は転換済み相当として配当を重複控除せず、CB利息は加戻さず金融費用全額を残す保守的経済EPSで、厳密なGAAP希薄化EPSではない。

仮定終点PER（弱/基準/強）：8/12/18倍。

一次アンカー（実績/会社予想は各scope/typeで区別）：
- [2026-08-11 FY26 preliminary unaudited actual and FY27 company guide](https://ir.supermicro.com/news/news-details/2026/Supermicro-Announces-Fourth-Quarter-and-Full-Fiscal-Year-2026-Financial-Results/default.aspx)：`{"FY_revenue_bn":39.063072,"FY_GAAP_OP_bn":2.770486,"FY_parent_common_NI_bn":2.217365,"FY_EPS":3.26,"Q4_revenue_bn":11.119777,"Q4_GAAP_OP_bn":1.488064,"Q4_net_income_bn":1.178217,"Q4_diluted_shares_bn":0.705001,"FY_SBC_bn":0.412115,"FY_CFO_bn":-6.809886,"FY_inventory_bn":12.895949,"FY27_revenue_guide_bn":[65,72],"Q1FY27_revenue_guide_bn":[14.5,15.5],"Q1FY27_GAAP_diluted_shares_guide_bn":0.745}`
- [2026-08-31 audited FY26 filed8/31 confirms results; updated governance status supersedes preliminary8/11](https://www.sec.gov/Archives/edgar/data/1375365/000137536526000022/smci-20260630.htm)：`{"FY_revenue_bn":39.063072,"FY_GAAP_OP_bn":2.770486,"FY_NI_bn":2.230453,"FY_CFO_bn":-6.809886,"financial_statement_audit":"unqualified","internal_control_audit":"material_weakness_IT_general_controls","internal_export_investigation":"completed; no basis found to question prior financial statements","government_inquiries":"ongoing"}`

成立条件：高いFY27会社見通しと回収・利益率の維持が必要で、営業CF赤字による資金調達・転換株式の希薄化、内部統制の重大な不備と政府照会が大きなリスク。

反証・監視点：監査済み財務諸表は無限定適正意見だが、IT全般統制の重大な不備が残る。独立輸出調査は完了、政府照会は継続／FY26は黒字でも営業CFが−6.81bnUSD。在庫・売掛金増には外部資金が必要／FY27会社見通し中点は前期比約75%増で、需要・検収・納期の未達リスクが大きい／強制転換優先株・転換社債・株式報酬による希薄化／Q4粗利益率17.5%は顧客・製品構成に左右され、通期の維持を保証しない

### Lenovo（0992.HK）

IDG・ISG・SSGを分け、部門間売上の重複を消去する。ISG年換算340億USDを独自にAI180億・従来型160億へ配分する。ワラント評価損と投資評価益の両方を除き、株式報酬・通常買収償却・研究開発を残す。将来黒字時の転換社債・ワラントを含む経済的希薄化株数を用い、USDのEPSをHKDへ一度だけ換算する。

株数・通貨：Q1会計赤字の分母12.077851410bnは逆希薄化証券を含まない。8/8条件調整後は普通株12.404659302bn＋2029CB0.421385398bn＋2028CB1.667342582bn＋2033CB0.438343592bn＋ワラント最大転換1.229930495bn＝16.161661369bn。2033CBは通常2032年まで転換不可だが、長期の経済的希薄化として前倒し保守計上する。将来株式報酬を上乗せし16.2〜16.5bnを使用。現金決済・発行代金による買戻しを仮定しない。EPSはUSD×USDHKD7.84719992で一度だけHKD換算し、0992普通株と比較する。

仮定終点PER（弱/基準/強）：8/11/15倍。

一次アンカー（実績/会社予想は各scope/typeで区別）：
- [2026-08-13 Q1FY26/27 issuer segment actual](https://news.lenovo.com/pressroom/press-releases/q1-fy-2026-27/)：`{"group_revenue_bn":26.943,"IDG_bn":17.1,"ISG_bn":8.5,"SSG_bn":2.9,"ISG_OP_bn":0.777,"SSG_OP_bn":0.697,"AI_related_bn":9.3,"AI_pipeline_bn":54}`
- [2026-08-13 HKFRS Q1 reconciliation and dilution](https://doc.irasia.com/listco/hk/lenovo/interim/2027/int1q.pdf)：`{"reported_OP_bn":0.019202,"reported_parent_NI_bn":-0.6086,"warrant_FV_loss_bn":1.690299,"financial_asset_FV_gain_bn":0.250083,"M_A_amortization_bn":0.016524,"basic_denominator_bn":12.07785141,"issued_warrant_instruments_bn":1.15,"ordinary_issued_shares_bn":12.404659302,"2029_CB_adjusted_potential_shares_bn":0.421385398,"2028_CB_adjusted_potential_shares_bn":1.667342582,"2033_CB_adjusted_potential_shares_bn":0.438343592,"warrants_adjusted_potential_shares_bn":1.229930495,"fully_issued_plus_all_potential_bn":16.161661369}`

成立条件：ISGの利益率とサービス成長が維持される必要があり、ワラント評価損益を除いても転換社債・ワラント希薄化と薄利ハードウェアの資金負担が残る。

反証・監視点：Q1会計赤字にはワラント再評価損1.690bnUSDが大きく、実績EPSの単純延長は不適切／評価損益の除外は株式報酬・通常償却の除外を意味しない／ワラント・転換社債の現金決済/株式決済によって経済的希薄化が変わる／薄いハードウェア利益率、在庫・顧客金融。SSGやAI関連売上にはAI PC等も含まれる

### Quanta Computer（2382.TW）

2026校正は1〜9月実績売上＋Q4をQ3と同額とする独自仮定。AI65%・従来型サーバー15%・その他20%へ独自配分し、AI売上をサーバー工程の市場規模と取り分に連動させる。製品別割合は会社開示値ではない。株式報酬・通常償却・研究開発を利益率に残す。最新財務・株数は台湾証券取引所の一次APIで確認した。

株数・通貨：Current ordinary shares from exchange, not H1 weighted average. Forecast grows share count for employee/convertible dilution. 4.107627432bn current differs from H1EPS-implied~3.855bn; latest issued basis used. 追補訂正：既存CB全元本の潜在株を明示。現在株数＋全元本潜在株を保守的な経済分母の上限として採用し、元と同じ年1.0/1.2/2.0%の将来株数増を加える。最新残存元本は未確定で、既転換分が重複し得るため、正確な実株数・GAAP希薄化EPSではない。金融費用は加戻さない。

仮定終点PER（弱/基準/強）：10/15/20倍。

一次アンカー（実績/会社予想は各scope/typeで区別）：
- [2026-10-18 Q2 cumulative Jan-Jun2026, TWD bn; EPS is then-current share basis](https://openapi.twse.com.tw/v1/opendata/t187ap06_L_ci)：`{"H1_revenue_bn":1845.813767,"H1_operating_income_bn":57.268079,"H1_parent_NI_bn":49.843907,"H1_basic_EPS":12.93}`
- [2026-10-17 latest September cumulative sales; original release occurred before10/18, API export10/17](https://openapi.twse.com.tw/v1/opendata/t187ap05_L)：`{"JanSep_sales_TWD_bn":2961.358288,"Q3_sales_derived_TWD_bn":1115.5445209999998}`
- [2026-10-17 10/17 issued ordinary shares](https://openapi.twse.com.tw/v1/opendata/t187ap03_L)：`{"ordinary_shares_bn":4.107627432}`
- [2026-08-13 Q2 results event confirmed; numerical PDF fetch blocked by site protection](https://www.quantatw.com/Quanta/chinese/investment/financials_icp.aspx)：`{"event_date":"2026-08-13","numbers_from_exchange_primary_API_instead":true}`
- [2026-08-03 CB conversion terms; full original principal is a conservative economic dilution upper bound, not verified remaining principal](https://links.sgx.com/1.0.0/corporate-announcements/A3JJ4IET6UQ7WOK9/21e6b795a85730c264e324874c22d5d196cdf37d2d8ef097d3c1c87706d7a1a1)：`{"current_issued_bn":4.107627432,"full_original_principal_potential_shares_bn":0.17905205630343662,"economic_share_base_upper_bn":4.286679488303437}`
- [2026-08-03 IV CB USD1bn, fixedFX32.055, conversion price322.01 after GDS245m ordinary issue](https://links.sgx.com/1.0.0/corporate-announcements/RKZFKYAIL9T8YIJV/2a8abdf6562994d164d6413006aca6438132295e71a411e31d14b3bbc63308a3)：`{"conversion_price_TWD":322.01,"principal_USD_bn":1,"fixed_USDTWD":32.055}`

成立条件：AIサーバーの増産を3%台以上の営業利益率で回収できることが必要で、独自AI売上割合・顧客支給部品の計上変更・運転資金が不確実。

反証・監視点：AI製品別売上割合65%は独自推定で、会社の監査済みAI部門開示ではない／顧客支給GPU/メモリと売上総額計上の変更により、売上と出荷数量が乖離する／米国生産の立上げ、部品不足、貿易規制／顧客集中、在庫・売掛金の資金需要。現株数4.1076bnを使用し旧EPS分母を流用しない／旧試算のCB織込み不足を訂正。全元本上限を使う保守的経済EPSであり、残存元本・転換登録の精査でEPSは変わる。新規CB・追加資金調達は別の希薄化リスク。

### Wiwynn（6669.TW）

1〜9月実績売上＋Q4をQ3と同額とする独自校正をAI80%・従来型20%へ配分する。4月以降の一部顧客のメモリ代理調達を反映した純額売上を使い、顧客支給部品を総額へ戻さない。Q2のNRE収入による利益率上振れを恒常化せず、株式報酬・償却等を費用に残す。9月権利落の株式配当後株数でEPSを計算する。

株数・通貨：Current ordinary shares from exchange, not H1 weighted average. Forecast grows share count for employee/convertible dilution. Q2EPS80.43 is before stock dividend; old shares×2.9827946; current560.199772m issued is used. Additional proposed15bnTWD CB may dilute. 追補訂正：既存CB全元本の潜在株を明示。現在株数＋全元本潜在株を保守的な経済分母の上限として採用し、元と同じ年1.0/1.2/2.0%の将来株数増を加える。最新残存元本は未確定で、既転換分が重複し得るため、正確な実株数・GAAP希薄化EPSではない。金融費用は加戻さない。

仮定終点PER（弱/基準/強）：12/18/24倍。

一次アンカー（実績/会社予想は各scope/typeで区別）：
- [2026-10-18 Q2 cumulative Jan-Jun2026, TWD bn; EPS is then-current share basis](https://openapi.twse.com.tw/v1/opendata/t187ap06_L_ci)：`{"H1_revenue_bn":554.660326,"H1_operating_income_bn":37.676176,"H1_parent_NI_bn":29.083507,"H1_basic_EPS":156.38}`
- [2026-10-17 latest September cumulative sales; original release occurred before10/18, API export10/17](https://openapi.twse.com.tw/v1/opendata/t187ap05_L)：`{"JanSep_sales_TWD_bn":989.278016,"Q3_sales_derived_TWD_bn":434.6176899999999}`
- [2026-10-17 10/17 issued ordinary shares](https://openapi.twse.com.tw/v1/opendata/t187ap03_L)：`{"ordinary_shares_bn":0.560199772}`
- [2026-08-07 Q2 actual and operating model](https://www.wiwynn.com/news/wiwynn-reports-second-quarter-2026-financial-results?hs_amp=true)：`{"Q2_revenue_bn":278.153,"Q2_PAT_bn":14.969,"Q2_OP_margin":0.073,"Q2_pre_stock_dividend_EPS":80.43,"procurement_agency_from_April":"specified customer memory excluded from revenue and COGS","H2_capex_budget_USD_bn":0.942,"proposed_CB_TWD_bn":15,"syndicated_loan_USD_bn":1.5}`
- [2026-09-02 stock dividend](https://www.wiwynn.com/investors/shareholders-services)：`{"stock_dividend_TWD_per_old_share":19.827946,"par_value_TWD":10,"share_multiplier":2.9827946,"ex_rights":"2026-09-02","stock_distribution":"2026-10-14"}`
- [2026-09-03 CB conversion terms; full original principal is a conservative economic dilution upper bound, not verified remaining principal](https://links.sgx.com/1.0.0/corporate-announcements/UDGP37S01F4SQYXD/d62fbc416c904566f43852fccda0e3bbd769fe8654517568e87f621cbc92a578)：`{"current_issued_bn":0.560199772,"full_original_principal_potential_shares_bn":0.06496470941139926,"economic_share_base_upper_bn":0.6251644814113992}`

成立条件：代理調達後の売上でもAI増産を6%台の営業利益率で利益へ変えることが必要で、顧客集中・大型投資と転換社債の希薄化が主要リスク。 残存CB未確定のため全元本上限を分母に採用。

反証・監視点：AI80%の売上内訳は独自仮定で、特定顧客・案件への集中がある／代理調達・顧客支給方式で売上総額が減っても出荷量・利益が同率で減るとは限らない／Q2のNRE収入は利益率を押し上げたが、基準のAI営業利益率は6.5%に抑えた／大型設備投資、最大150億TWDの転換社債と15億USD融資による資金・希薄化リスク／株式配当19.827946TWD/旧株、倍率2.9827946を反映。旧Q2EPS80.43を現株価へ直接割らない／旧試算のCB織込み不足を訂正。全元本上限を使う保守的経済EPSであり、残存元本・転換登録の精査でEPSは変わる。新規CB・追加資金調達は別の希薄化リスク。

### Hon Hai Precision（2317.TW）

2026校正は1〜9月実績売上＋Q4をQ3と同額とする独自仮定。AI45%・従来型通信等15%・端末等40%へ独自配分し、AIラック/ASIC増産と一般電子機器を分ける。顧客支給型ASICの部材を重複加算せず、株式報酬・償却・研究開発、通常金融費用、税・非支配持分を引いて親会社EPSを算出する。

株数・通貨：Current ordinary shares from exchange, not H1 weighted average. Forecast grows share count for employee/convertible dilution.

仮定終点PER（弱/基準/強）：9/13/17倍。

一次アンカー（実績/会社予想は各scope/typeで区別）：
- [2026-10-18 Q2 cumulative Jan-Jun2026, TWD bn; EPS is then-current share basis](https://openapi.twse.com.tw/v1/opendata/t187ap06_L_ci)：`{"H1_revenue_bn":4645.427824,"H1_operating_income_bn":170.451721,"H1_parent_NI_bn":109.89322,"H1_basic_EPS":7.84}`
- [2026-10-17 latest September cumulative sales; original release occurred before10/18, API export10/17](https://openapi.twse.com.tw/v1/opendata/t187ap05_L)：`{"JanSep_sales_TWD_bn":7669.77251,"Q3_sales_derived_TWD_bn":3024.3446859999995}`
- [2026-10-17 10/17 issued ordinary shares](https://openapi.twse.com.tw/v1/opendata/t187ap03_L)：`{"ordinary_shares_bn":14.075746497}`
- [2026-08-12 Q2 actual; company outlook](https://www.foxconn.com/en-us/press-center/press-releases/latest-news/2095)：`{"Q2_revenue_TWD_bn":2530,"Q2_OP_TWD_bn":94.8,"Q2_parent_NI_TWD_bn":60,"Q2_EPS":4.27,"cloud_networking_Q2_revenue_share":">50%","full_year_AI_rack_unit_growth":"more_than_double_company_expectation"}`
- [2026-08-18 cash and gross revenue recognition](https://image.honhai.com/upload/202608/law_talk/Hon_Hai_2Q26_Results_Transcript_English_20260818_1815.pdf)：`{"H1_CFO_TWD_bn":-69.1,"H1_FCF_TWD_bn":-150.0,"net_cash_TWD_bn":219.8,"midlongterm_OP_margin_target":">3%","ASIC_projects":"mostly_consignment_customer_components_may_not_enter_revenue"}`

成立条件：AIラック増産を3〜4%台の営業利益率と回収につなげる必要があり、部材計上方式・生産移転・増産時の資金負担が売上成長の利益化を左右する。

反証・監視点：AI45%の製品配分は独自仮定で、Cloud&Networkingの全売上をAIとは扱わない／ASICの委託・顧客支給方式では売上総額と利益成長率が一致しない／米国等への生産移転、部品不足、貿易規制／上期営業CF−691億TWD・FCF−1500億TWD。増産に伴う在庫・売掛金と設備投資の資金負担／連結利益から非支配株主分を引く必要がある
