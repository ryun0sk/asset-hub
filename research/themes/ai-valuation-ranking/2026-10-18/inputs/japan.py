#!/usr/bin/env python3
"""Public-primary calibrated scenarios; all money and share counts are billions.
No prices or network access are required for reproduction. Own assumptions != guidance.
"""
import json, math
from pathlib import Path

PREFIX=Path(__file__).resolve().with_suffix('')
MACRO={2026:{'calibration':1000},2028:{'weak':1000,'base':1400,'strong':1900},2029:{'weak':950,'base':1700,'strong':2500}}
CASES=('weak','base','strong')

def fact(date,scope,url,numbers,kind='company_actual'):
    return dict(date=date,scope=scope,source_url=url,url=url,numbers=numbers,classification=kind,verified_as_of='2026-10-18 JST')

def seg(name,anchor,exposure,elasticity,complexity,margins,nonai=(-.03,.025,.05),price=(.94,1,1.05),ramp=(1,1,1),basis='latest revenue calibration'):
    return dict(name=name,anchor=anchor,exposure=exposure,elasticity=elasticity,complexity=complexity,margins=margins,nonai=nonai,price=price,ramp=ramp,basis=basis)

SOURCES={
 'shin':'https://www.shinetsu.co.jp/wp-content/uploads/2026/07/20260724_con_E.pdf',
 'shinbuy':'https://www.shinetsu.co.jp/wp-content/uploads/2026/09/20260915E2.pdf',
 'sum':'https://ssl4.eir-parts.net/doc/3436/tdnet/2864809/00.pdf',
 'sumdeck':'https://ssl4.eir-parts.net/doc/3436/tdnet/2864822/00.pdf',
 'sumreclass':'https://ssl4.eir-parts.net/doc/3436/tdnet/2878442/00.pdf',
 'gwc':'https://www.sas-globalwafers.com/en/gwc_news_en_20260804/',
 'gwcfs':'https://www.sas-globalwafers.com/wp-content/uploads/2026/05/GlobalWafers_2026Q2-consolidated-financial-statement_EN.pdf',
 'gwcsep':'https://www.sas-globalwafers.com/en/gwc_news_en_20261007/',
 'gwcgds':'https://www.sas-globalwafers.com/en/gwc_news_en_20260923/',
 'waf':'https://www.siltronic.com/fileadmin/investorrelations/2026/Q2/20260730_Siltronic_Half_Year_Financial_Report_2026.pdf',
 'tel':'https://www.tel.com/ir/library/report/i242su0000000goz-att/fy27q1tanshin-e.pdf',
 'telqa':'https://www.tel.com/ir/library/report/i242su0000000goz-att/FY27Q1_EarningCall_QA_E.pdf',
 'telshares':'https://www.tel.com/ir/stocks/info/',
 'teltrans':'https://www.tel.com/ir/library/report/i242su0000000goz-att/fy27q1transcript-e.pdf',
 'lam':'https://investor.lamresearch.com/2026-07-29-Lam-Research-Corporation-Reports-Financial-Results-for-the-Quarter-Ended-June-28,-2026',
 'ase':'https://www.sec.gov/Archives/edgar/data/1122411/000095010326011351/dp250868_6k.htm',
 'asesep':'https://www.sec.gov/Archives/edgar/data/1122411/000095010326015458/dp254866_6k.htm',
 'aji':'https://www.ajinomoto.co.jp/company/en/ir/event/presentation/main/011111113/teaserItems1/01/linkList/0/link/FY26Q1_Tanshin_E.pdf',
 'ajiforecast':'https://www.ajinomoto.co.jp/company/en/ir/event/presentation/main/011111113/teaserItems1/01/linkList/02/link/FY26Q1_Forecast_E.pdf',
 'ajitech':'https://www.ajinomoto.co.jp/company/en/ir/event/business_briefing/main/011117/teaserItems1/01/linkList/03/link/20260630_presentation_E.pdf',
 'ibi':'https://www.ibiden.com/ir/items/tannshinn2026Q1.pdf',
 'ibiqa':'https://www.ibiden.com/ir/items/en_QA_FY2026Q1.pdf',
 'unim':'https://www.unimicron.com/files/money/Earnings/en/2026-Q2-consolidated-en.pdf',
 'unimsep':'https://www.unimicron.com/money01.html',
 'disco':'https://www.disco.co.jp/eg/ir/library/doc/fr/fr20260723.pdf',
 'disconote':'https://www.disco.co.jp/eg/ir/library/doc/film/20260723_note.pdf',
 'discoflash':'https://www-hq.disco.co.jp/eg/ir/library/doc/news/202610061_Preliminary_Report_on_Non-Consolidated_Sales_Figures_and_Shipment_Figures_(Second_Quarter_of_Fiscal_Year_2026).pdf',
 'ter':'https://investors.teradyne.com/news-events/press-releases/detail/445/teradyne-reports-second-quarter-2026-results',
}

def company(symbol,name,ccy,quality,segments,shares,finance,tax,pe,anchor_facts,method,risks,unallocated=0,minority_ratio=0,pe_reason='',share_basis='',adjustments=None):
    return dict(symbol=symbol,name=name,financial_currency=ccy,quote_currency=ccy,model_quality=quality,anchor_facts=anchor_facts,method=method,risks=risks,terminal_pe=dict(zip(CASES,pe)),terminal_pe_basis=pe_reason,share_basis=share_basis,assumptions=dict(segments=segments,diluted_shares_bn_by_year=shares,net_finance_bn_by_case=finance,tax_rate_by_case=tax,unallocated_cost_bn_2026=unallocated,unallocated_cost_growth=.04,minority_share_of_positive_posttax=minority_ratio),normalization_adjustments=adjustments or [],rows=[])

companies=[]
companies.append(company('4063.T','信越化学','JPY','B_segment_calibrated',[
 seg('電子材料（ウェーハ・レジスト・マスク等）',279.271*4,.50,.65,(.01,.04,.07),(.28,.37,.42),basis='Q1 external revenue ×4; calibration, not FY forecast'),
 seg('生活環境基盤材料（PVC・苛性ソーダ等）',227.798*4,0,0,(0,0,0),(.08,.16,.23),nonai=(-.04,.025,.05),price=(.90,1,1.06)),
 seg('機能材料',118.203*4,.10,.40,(0,.01,.02),(.19,.245,.28)),
 seg('加工・商事・技術サービス',37.151*4,.10,.40,(0,.01,.02),(.15,.20,.23)),
],{2028:1.84,2029:1.85},(25,40,50),(.30,.29,.28),(18,24,30),[
 fact('2026-07-24','FY27/3 Q1 consolidated',SOURCES['shin'],{'revenue_bn':662.424,'operating_income_bn':173.798,'parent_income_bn':130.829,'diluted_eps':70.24,'external_segment_revenue_bn':[279.271,227.798,118.203,37.151]}),
 fact('2026-07-24','FY27/3 full-year guidance',SOURCES['shin'],{'revenue_bn':2700,'operating_income_bn':700,'parent_income_bn':525,'basic_eps':286},'company_guidance'),
 fact('2026-09-15','FCSR adjustment; July repurchase',SOURCES['shinbuy'],{'half_repurchased_shares_bn':.0162317,'adjustment_shares_returned_bn':.0006416})
],
 '電子材料はAIチップの製造面積・工程増へ低めの弾性で接続。PVCはAI支出へ直接接続せず景気と価格。全社EPSをAI材料の成長率で伸ばさない。',
 ['電子材料のAI感応度50%は独自配分で会社開示のAI売上比率ではない','PVC価格、中国供給、エネルギー、為替、ウェーハLTA更改と新能力の償却','金融収益を正常化しても余剰現金の利息が一部含まれ得る。現金価値を別加算する場合は整合が必要'],
 pe_reason='材料技術・財務耐久性に加点する一方、PVCとウェーハ循環があるため基準24倍。独自の2029終点倍率で現在PERではない。',share_basis='Q1 diluted NI/EPS≈1.863bn; July buyback32.4634m and September first adjustmentを参照。未来の追加買戻しを仮定せず2028/29=1.84/1.85bnの独自希薄化分母。'))

# FST reclassification: 2026 H1 annualized 430.032 less a deliberately disclosed own 40bn scope adjustment.
companies.append(company('3436.T','SUMCO','JPY','C_scope_and_cycle_sensitive',[
 seg('継続連結ウェーハ事業（FST除外校正）',390.032,.55,.55,(0,.025,.05),(-.02,.16,.27),price=(.90,1.04,1.10),ramp=(1.0,1.08,1.15),basis='H1 revenue ×2 =430.032 minus own FST scope estimate40; not reported continuing revenue'),
],{2028:.353,2029:.355},(-7,-3,1),(.28,.28,.27),(12,18,24),[
 fact('2026-08-06','H1 consolidated',SOURCES['sum'],{'revenue_bn':215.016,'operating_income_bn':-6.363,'parent_income_bn':-12.895,'basic_eps':-36.87,'basic_weighted_shares_bn':.3497186}),
 fact('2026-08-06','Q2 shipments/pricing and Q3 guidance',SOURCES['sumdeck'],{'q2_revenue_bn':113.6,'q2_operating_income_bn':-1.1,'q3_revenue_bn':118,'q3_operating_income_bn':0},'company_actual_and_quarter_guidance'),
 fact('2026-08-27','FST deconsolidation announcement',SOURCES['sumreclass'],{'retained_voting_interest':.38,'deemed_reclassification_date':'2026-09-30','reported_earnings_impact':'under review'})
],
 'ウェーハ面積×価格×稼働率回復を売上へ反映。AI装置投資ほど高い弾性を与えず、減価償却込み営業利益率の回復を別仮定。FSTの2026年売却益はゼロ、将来の持分利益はnet_financeに含む少額の正常値。',
 ['FST連結除外後の継続売上がまだ未確定なので390.032bnは粗い校正。正確なTAM×シェアではない','基準OPM16%は足元赤字から大きな稼働率・価格改善を必要とする','LTAとスポットの価格改定、200mm回復、新工場償却、為替、借入負担で上下する'],
 pe_reason='循環回復に依存するウェーハ。赤字からの反転を成長株の高倍率で評価せず基準18倍。',share_basis='最新発行350.175m・自己442,825株、H1平均349.719mを出発点。将来0.353/0.355bnは独自希薄化仮定。',adjustments=['2026 H1売上年換算からFST連結除外40bnを独自控除。誤差が大きくC評価。','持分38%を売上に再加算せず、金融・持分損益の正常仮定に含め二重計上を防ぐ。']))

companies.append(company('6488.TWO','GlobalWafers','TWD','B_minus_ramp_sensitive',[
 seg('半導体ウェーハ等',44.070*4/3,.55,.55,(0,.025,.05),(.08,.23,.32),price=(.92,1.03,1.08),ramp=(1.02,1.15,1.28),basis='2026 Jan-Sep monthly revenue sum44.070 ×4/3 calibration; not full-year guidance'),
],{2028:.535,2029:.540},(-1,.5,1.5),(.23,.22,.21),(12,18,24),[
 fact('2026-08-04','Q2 and H1 consolidated',SOURCES['gwcfs'],{'q2_revenue_bn':15.214310,'q2_operating_income_bn':1.422811,'q2_parent_income_bn':3.779084,'q2_other_gains_bn':3.132860,'q2_diluted_shares_bn':.478414,'h1_revenue_bn':29.199108}),
 fact('2026-08-04','capacity and demand comments',SOURCES['gwc'],{'existing_12inch_utilization':'fully utilized excluding new lines','texas':'multiple Tier-1 qualifications','italy':'8inch fire July20; new12inch not affected'}),
 fact('2026-10-07','September/Q3 monthly sales; no Q3 profits yet',SOURCES['gwcsep'],{'q3_revenue_bn_rounded':14.87,'q3_revenue_qoq':-.0226,'jan_sep_revenue_bn_from_monthly_sum':44.070,'italy_epi_restart':'Sep14; downstream repair continues'}),
 fact('2026-09-23','GDS pricing, completion confirmedOct7',SOURCES['gwcgds'],{'gds_issued_bn':.050,'ordinary_shares_per_GDS':1,'gross_proceeds_usd_bn':1.432,'proforma_shares_after_offering_bn':.528114})
],
 'AI・HBM・先端ロジックのウェーハ消費に接続し、新規米国/日本/伊の認定後立上げを別ramp係数で明示。金融損益を大幅正常化しQ2EPSを伸ばさない。',
 ['Q2の最終利益率24.8%はOPM9.4%を大幅に上回り、その他益を反復させない','新工場の顧客認定、米国コスト、初期償却、地域化の重複投資、伊火災と為替','ramp1.15等は需要・認定が満たされた場合の売上能力消化仮定で会社ガイドではない'],
 pe_reason='地域分散と顧客認定に価値はあるが、供給循環・資本集約・稼働回復に依存し基準18倍。',share_basis='Q2普通株478.114m・希薄化478.414m。9月GDS50m（各1普通株）を加味したプロフォーマ普通株528.114mから、将来0.535/0.540bnの希薄化分母。買戻しなし。',adjustments=['Q2その他益3.132860bnを年換算せず、将来net_financeは−1/+0.5/+1.5bn。SBC・償却は営業利益率に残す。','9月GDSの希薄化を無視しない。10/7公表のQ3売上はQoQ減で、全社の足元成長を一律AI好況としない。']))

companies.append(company('WAF.DE','Siltronic','EUR','C_depreciation_and_recovery_sensitive',[
 seg('シリコンウェーハ',.6281*2,.55,.55,(0,.02,.04),(-.06,.14,.25),price=(.90,1.05,1.14),ramp=(1.02,1.12,1.25),basis='2026 H1 revenue ×2; IFRS EBIT after Singapore depreciation'),
],{2028:.0335,2029:.0340},(-.055,-.040,-.025),(.28,.27,.26),(10,16,22),[
 fact('2026-07-30','H1 IFRS and new shares',SOURCES['waf'],{'revenue_bn':.6281,'ebitda_bn':.1345,'ebit_bn':-.1043,'depreciation_bn':.2388,'net_income_before_nci_bn':-.1300,'new_shares_bn':.003,'capital_raise_bn':.273,'net_financial_debt_bn':.6919}),
 fact('2026-07-30','FY26 guidance',SOURCES['waf'],{'revenue_change':'low-to-mid single digit decline vs FY25 EUR1.3467bn','ebitda_margin_range':[.20,.24]},'company_guidance')
],
 '300mm面積と価格・シンガポール能力消化をモデル化。EBITDAを純利益に置かず、新工場減価償却を残したIFRS EBIT利益率を仮定する。',
 ['基準EBIT14%は足元−16.6%から大幅な回復が必要。基準を中立・会社予想と呼ばない','高稼働でも価格が低ければ償却を吸収できない。200mm・電力・為替・借入金利も重要','利益赤字の弱気ケースではPE評価不能。資産価値ゼロの意味ではない'],
 minority_ratio=.15,pe_reason='ウェーハ循環と高固定費・債務を反映して基準16倍。回復時の利益に高い成長プレミアムを付けない。',share_basis='6月新株3mで30m→33m。将来33.5/34m、既存・将来希薄化と買戻しなし。NCIは正の税後利益の15%を独自控除。'))

companies.append(company('8035.T','東京エレクトロン','JPY','B_process_and_service_calibrated',[
 seg('新規半導体製造装置', (732.388-188)*4,.75,.75,(.02,.065,.10),(.26,.365,.41),price=(.97,1.025,1.05),ramp=(1,1.06,1.12),basis='Q1 group revenue less Field Solutions188bn, ×4'),
 seg('Field Solutions（部品・サービス・中古/改造）',188*4,.45,.45,(.01,.03,.05),(.24,.30,.34),price=(.99,1.02,1.04),basis='Q1 Field Solutions ×4; not all subscription'),
],{2028:2.28,2029:2.29},(0,10,15),(.30,.29,.28),(18,25,32),[
 fact('2026-07-30','FY27 Q1 consolidated',SOURCES['tel'],{'revenue_bn':732.388,'operating_income_bn':211.407,'parent_income_bn':164.341,'basic_weighted_shares_bn_presplit':.454785263}),
 fact('2026-07-30','H1 company guidance',SOURCES['tel'],{'revenue_bn':1620,'operating_income_bn':458,'parent_income_bn':349,'full_year_guidance':'not yet published'},'company_guidance'),
 fact('2026-08-03','July30 earnings QA',SOURCES['telqa'],{'company_wfe_2026_usd_bn':'>150','company_wfe_2027_usd_bn':'>190','operating_margin_target':.35},'company_market_outlook_and_targets'),
 fact('2026-10-01','ordinary share split basis',SOURCES['telshares'],{'issued_shares_bn':2.340163665,'inferred_split_from_June30':5})
],
 'WFE/メモリ・先端ロジックcapexと工程複雑化を装置へ、既存装置台数・稼働をField Solutionsへ。市場150/190bnは会社予測であり確定受注ではない。基準装置OPM36.5%と価格改定は独自仮定。',
 ['中国売上30%台と輸出規制、Lam等との低温エッチ・成膜の競争','35%OPM目標と数量3倍能力は実現済み利益ではない','部材、人件費、R&D、増産費用・為替と検収時期で利益変動'],
 pe_reason='塗布現像の強い地位と工程の拡大を評価し基準25倍、WFE循環・対中規制でASML級独占倍率を自動付与しない。',share_basis='10/1 1:5分割後。Q1平均454.785m×5≈2.274bn、将来2.28/2.29bn。旧EPSを5で割らず比較しない。'))

companies.append(company('LRCX','Lam Research','USD','B_process_and_support_calibrated',[
 seg('新規Systems',4.249848*4,.78,.78,(.025,.075,.11),(.32,.435,.47),price=(.97,1.02,1.04),ramp=(1,1.05,1.12)),
 seg('Customer Support関連・Reliant',2.472390*4,.50,.45,(.01,.03,.05),(.27,.35,.39)),
],{2028:1.28,2029:1.29},(-.10,0,.05),(.15,.15,.15),(18,26,34),[
 fact('2026-07-29','Quarter ended June28 actual',SOURCES['lam'],{'revenue_bn':6.722238,'systems_bn':4.249848,'support_and_other_bn':2.472390,'gaap_operating_margin':.374,'net_income_bn':2.277282,'diluted_shares_bn':1.256032}),
 fact('2026-07-29','September quarter guidance',SOURCES['lam'],{'revenue_bn':8.1,'revenue_range_bn':[7.7,8.5],'gaap_operating_margin':.395,'diluted_shares_bn':1.255},'company_quarter_guidance')
],
 '成膜・エッチの工程数増（NAND層数/GAA/背面給電）×新設装置需要、保守・部品は既存基盤と稼働へ別感応度。6月売上×4は売上水準の校正でFY/CY会社予想ではない。',
 ['Systemsのメモリ比率46%と中国売上26%の循環・規制','CSBGには旧世代装置も含み全額継続課金ではない','工程統合・競合・供給網/輸送コスト・R&Dと供給拡張。通常SBCと償却を残す'],
 unallocated=.4,pe_reason='高付加価値の成膜・エッチとサポートを評価し基準26倍。メモリ投資循環・規制を加味。',share_basis='最新実績希薄化1.256032bnと9月会社想定1.255bnから将来1.28/1.29bn。未発表買戻しによるEPS押上げを与えない。'))

companies.append(company('3711.TW','ASE Technology','TWD','B_ATM_EMS_calibrated',[
 seg('Assembly/Test/Materials',(126.148+151.485)*2,.60,.70,(.01,.055,.09),(.12,.19,.25),price=(.98,1.02,1.05),ramp=(1,1.06,1.14),basis='Q2 actual ATM plus Oct12 Q3 sales-only flash, ×2; revenue calibration only'),
 seg('EMS・連結調整後残余',((191.064+244.161)-(126.148+151.485))*2,.25,.45,(0,.01,.025),(.02,.035,.05),basis='latest Q2+Q3 consolidated less ATM, ×2, to eliminate intercompany overlap'),
],{2028:4.60,2029:4.65},(-8,-5,-2),(.20,.19,.18),(12,19,26),[
 fact('2026-07-30','Q2 consolidated/ATM/EMS',SOURCES['ase'],{'revenue_bn':191.064,'atm_revenue_bn':126.148,'ems_reported_revenue_bn':65.789,'operating_income_bn':21.134,'parent_income_bn':21.068,'diluted_shares_bn':4.505702583,'atm_operating_margin':.157,'ems_operating_margin':.024,'fx_valuation_and_hedging_gain_bn':3.637,'equity_method_gain_bn':2.298}),
 fact('2026-10-12','Q3 sales-only flash; no Q3 profits',SOURCES['asesep'],{'q3_revenue_bn':244.161,'q3_atm_revenue_bn':151.485,'q3_revenue_qoq':.278,'q3_revenue_yoy':.448})
],
 '先端組立・テスト複雑化をATMへ、汎用EMSは低いAI感応度。ATM+EMSの内部売上二重計上を残余方式で除外。金利と正常持分損益だけ金融損益へ残し、評価・ヘッジ益を年換算しない。',
 ['先端実装需要の全額がOSATへ来るわけではなくTSMC等内製と競合','大顧客集中、設備/人員と減価償却、台湾・為替、テスト時間短縮','EMSの低利益率・部材パススルーが全社売上を大きくするためAI売上純度を過大評価しない'],
 minority_ratio=.02,pe_reason='AI先端実装とテストの付加価値に加点する一方EMS・資本集約と顧客集中を踏まえ基準19倍。',share_basis='台湾普通株のQ2希薄化4.505703bn。将来4.60/4.65bn、米国ADSへの変換はしない。NCIは正の税後利益2%控除。'))

companies.append(company('2802.T','味の素','JPY','B_whole_company_bridge',[
 seg('Functional Materials（ABF等）',120.6,.85,.75,(.015,.06,.09),(.45,.55,.60),price=(.98,1.02,1.05),basis='FY26 revised company forecast; includes materials other than ABF'),
 seg('非FM事業・配賦後事業利益相当',1732-120.6,0,0,(0,0,0),(.075,.090,.105),nonai=(0,.035,.06),price=(1,1,1),basis='company total less FM; base includes companywide cost before other-operating bridge'),
],{2028:.960,2029:.965},(-5,-4,-3),(.29,.28,.27),(20,28,35),[
 fact('2026-08-06','Q1 IFRS',SOURCES['aji'],{'revenue_bn':412.105,'business_profit_bn':60.116,'ifrs_operating_profit_bn':55.895,'parent_income_bn':36.452,'basic_weighted_shares_bn':.956451886,'diluted_eps':38.10}),
 fact('2026-08-06','FY26 revised guidance by division',SOURCES['ajiforecast'],{'revenue_bn':1732,'business_profit_bn':202,'fm_revenue_bn':120.6,'fm_business_profit_bn':65.5,'parent_income_bn':123.5},'company_guidance'),
 fact('2026-06-30','ABF business technology briefing',SOURCES['ajitech'],{'company_ABF_share':'more than95% of target insulation film market','new_Gifu_start':'2032, outside horizon'},'company_strategy')
],
 'ABFは一基板の面積/層数・高機能化とAIチップ出荷へ接続。食品等の大きい非FMはAI予算から直接増やさない。会社事業利益から通常のその他営業費用12bn（年4%増）を控除してIFRS営業利益相当へ橋渡し。',
 ['事業利益はIFRS営業利益と異なり持分損益を含む。部門別正常化は粗い','食品・冷食原材料と価格転嫁、医薬CDMO・R&D、人件費、全社費用がEPSを左右','ABF95%超は半導体材料全体のシェアではない。将来シェア上昇を仮定しない'],
 unallocated=12,minority_ratio=.065,pe_reason='材料の認定・高シェアと食品収益の安定性を評価し基準28倍。ABF純粋企業と同じ全社成長倍率にはしない。',share_basis='最新平均956.452m、希薄化EPS38.10対基本38.11。将来960/965m、2025年以前の株数を流用しない。',adjustments=['通常のその他営業費用を12bn校正し控除。事業利益に含まれる通常持分利益は残余の校正内、金融へ再加算しない。']))

# Ibiden FY26 latest formal guidance, allocated by Q1 external revenue mix (not a company segment FY forecast).
scale=550/123.219
companies.append(company('4062.T','イビデン','JPY','B_minus_source_discrepancy_and_capex',[
 seg('電子事業',77.522*scale,.80,.75,(.01,.065,.10),(.22,.31,.38),price=(.92,1.02,1.07),ramp=(1.02,1.13,1.25),basis='latest formal FY revenue guidance550 × Q1 external mix77.522/123.219'),
 seg('セラミック',24.365*scale,.10,.35,(0,.01,.02),(.07,.12,.16),nonai=(-.02,.02,.04)),
 seg('その他',21.330*scale,.05,.30,(0,0,.01),(.07,.105,.13)),
],{2028:.600,2029:.606},(-7,-5,-3),(.31,.30,.29),(16,24,32),[
 fact('2026-08-04','FY26 Q1 formal consolidated release',SOURCES['ibi'],{'revenue_bn':123.219,'operating_income_bn':26.880,'parent_income_bn':17.918,'electronic_external_revenue_bn':77.522,'electronic_op_bn':21.375,'inactive_asset_depreciation_nonop_bn':.834,'diluted_eps_presplit':60.76,'issued_shares_bn_presplit':.281944019}),
 fact('2026-08-04','FY26 formal full-year forecast',SOURCES['ibi'],{'revenue_bn':550,'operating_income_bn':127,'parent_income_bn':84,'basic_eps_post_October_split':149.68,'October1_split_ratio':2},'company_guidance')
],
 'CPU/GPU/スイッチ基板の大型・多層化と価格/新ライン歩留まりを電子へ。会社550bnをQ1売上構成で校正するため部門年売上は独自配分。遊休設備償却を金融等費用に残し、株売却益を除外。',
 ['基準利益率31%は不足プレミアム・稼働率と新棟歩留まりに依存','膨大なcapexのCF支出はPERモデルに含まれず、償却とCFを分ける','同日付近説明PDFの数値と正式8/4短信に不整合があるため正式短信を優先した。旧メモの580/120/70bnを使用しない'],
 pe_reason='高付加価値基板の技術・顧客認定を評価するが、顧客集中・価格循環・巨額capexを反映して基準24倍。',share_basis='1/1と10/1の各1:2分割を混同しない。Q1希薄化NI/EPS×2≈0.5898bn（CB利息調整等で概数）と7月転換を踏まえ将来0.600/0.606bn。',adjustments=['投資有価証券売却益等を将来へゼロ延長。通常償却・R&D・株式報酬は費用に残す。','Q1遊休設備償却834mは営業外費用。将来net_finance−5bn等に正常な金利・遊休償却を含む。']))

companies.append(company('3037.TW','Unimicron','TWD','C_high_nonop_and_capacity_uncertainty',[
 seg('ABF基板',(42.890+52.649835)*2*.52,.85,.75,(.01,.065,.10),(.15,.29,.38),price=(.91,1.03,1.09),ramp=(1.02,1.12,1.25),basis='Q2 sales + Q3 sum of Jul-Sep monthly sales ×2 × latest known Q2 ABF mix52%; Q3 mix is own carry-forward'),
 seg('BT/HDI/PCB/FPC等',(42.890+52.649835)*2*.48,.25,.45,(0,.02,.035),(.035,.105,.16),nonai=(-.02,.025,.045),basis='same latest six-month sales calibration × latest known nonABF mix48%'),
],{2028:1.60,2029:1.63},(-2,-1,0),(.23,.22,.21),(14,22,30),[
 fact('2026-07-29','Q2 company earnings deck',SOURCES['unim'],{'revenue_bn':42.890,'operating_income_bn':6.651,'net_nonoperating_income_bn':8.925,'parent_income_bn':13.115,'diluted_eps':8.38,'abf_revenue_mix':.52,'q2_DA_bn':5.109}),
 fact('2026-10-18','Official monthly sales page checked as of Oct18; release date not stated on page',SOURCES['unimsep'],{'july_revenue_bn':16.253637,'august_revenue_bn':17.745519,'september_revenue_bn':18.650679,'q3_revenue_bn_derived':52.649835,'q3_profit':'not yet published'})
],
 'ABF需要をAIチップ面積・層数と能力認定へ、他PCBは低いAI感応度へ接続。Q2の巨額営業外益を延長せず、営業利益と通常金利から純利益を計算。',
 ['Q2営業外益が営業利益を超える。EPS8.38の4倍を正常利益にしない','ABF新能力、原材料、歩留まり、顧客価格交渉・競合増設、HDI/BTの非AI市況','部門利益率とAI売上割合の公表はないため独自配分でC評価。ABF52%をAI売上52%と解釈しない'],
 minority_ratio=.025,pe_reason='ABF材料・基板の認定は評価するが、供給能力の循環と営業外益依存を踏まえ基準22倍。',share_basis='Q2親会社利益/希薄化EPSから約1.565bnの分母水準（EPS丸め・CB調整で厳密ではない）。将来1.60/1.63bnを置き、調達・希薄化に余裕。',adjustments=['Q2 net nonop+8.925bnを年換算せず、正常net_finance−2/−1/0bnに置換。','2026Q2 deckは会社公式ホストから10/18取得。Webテキスト取得失敗のためcurlとpdftotextで本文確認。']))

companies.append(company('6146.T','ディスコ','JPY','B_equipment_and_consumables_blend',[
 seg('精密加工装置・工具・保守（連結全体）',114.308*4,.65,.70,(.015,.06,.09),(.33,.44,.49),price=(.97,1.02,1.04),ramp=(1,1.05,1.12),basis='Q1 consolidated sales ×4 calibration, not nonconsolidated shipments'),
],{2028:.1090,2029:.1095},(-1,0,1),(.30,.29,.28),(24,34,44),[
 fact('2026-07-23','Q1 consolidated actual',SOURCES['disco'],{'revenue_bn':114.308,'operating_income_bn':49.033,'parent_income_bn':34.221,'basic_eps':315.51,'issued_shares_bn':.108483729,'treasury_shares_bn':.000016004}),
 fact('2026-10-06','Q2 nonconsolidated flash only',SOURCES['discoflash'],{'q2_sales_bn':118.5,'q2_shipments_bn':123.9,'q2_shipments_yoy':.60,'q2_consolidated_profit':'not released; scheduledOct22'}),
 fact('2026-07-23','investment and R&D plan',SOURCES['disconote'],{'FY26_capex_bn':33,'FY26_RD_bn':38,'FY26_depreciation_bn':16},'company_plan')
],
 'HBM薄化・切断、AIロジックとOSAT設備、稼働に応じる工具を加重した工程需要モデル。装置/工具の最新精密構成が未取得なので公表されないTAMシェアを作らず全社校正。',
 ['出荷と検収売上は違う。10/6単体速報を連結利益へ置換しない','新設備需要は稼働が満たされると一服。工程変更・並列化・顧客投資前倒し','基準OPM44%は足元42.9%近傍。R&D/人件費/償却を除外して利益率を作らない'],
 pe_reason='加工技術と稼働連動工具、財務健全性を評価し基準34倍。ただし設備循環のため永続的倍率とはしない。',share_basis='Q1発行108.484m・自己16,004株、将来109/109.5m（独自希薄化、株価53,850円と同じ普通株基準）。'))

companies.append(company('TER','Teradyne','USD','B_test_product_robotics_calibrated',[
 seg('Semiconductor Test',1.122*4,.70,.70,(.01,.07,.11),(.28,.39,.44),price=(.97,1.02,1.04),ramp=(1,1.04,1.10)),
 seg('Product Test',.107*4,.35,.45,(0,.025,.04),(.09,.17,.22)),
 seg('Robotics',.100*4,.05,.30,(0,.01,.02),(-.05,.08,.15),nonai=(-.02,.04,.08)),
],{2028:.160,2029:.162},(-.01,.02,.04),(.19,.18,.17),(18,26,34),[
 fact('2026-07-28','Quarter ended June28 actual; callJuly29',SOURCES['ter'],{'revenue_bn':1.329,'semi_test_bn':1.122,'product_test_bn':.107,'robotics_bn':.100,'gaap_parent_income_bn':.3745,'diluted_shares_bn':.1577,'h1_gaap_operating_income_bn':.9108}),
 fact('2026-07-28','Q3 guidance',SOURCES['ter'],{'revenue_range_bn':[1.2,1.3],'gaap_eps_range':[1.79,2.09]},'company_quarter_guidance')
],
 'SoC/メモリのテスト複雑化とAI設備増を半導体テストへ、Product Test・ロボティクスは別の低い感応度へ接続。Advantestとの競争によるシェア上昇を無条件に仮定しない。',
 ['半導体テストの急増四半期からの校正。Q3会社予想はQ2より低い売上を示す','HBM/GPU等の顧客採用、並列化・テスト短縮、Advantestとの競争','Roboticsの回復遅れ、ERP/人件費とR&D。通常のSBC・買収償却・持分投資償却を除外しない'],
 unallocated=.12,pe_reason='AIテストの成長・製品多様性を評価し基準26倍。競争・非半導体の収益性を加味し最上位の独占倍率を自動適用しない。',share_basis='最新Q2希薄化157.7m。将来160/162m、未発表買戻しは含まない。'))

def generate_row(c,year,case):
    i=CASES.index(case);n=year-2026; a=c['assumptions']; demand=MACRO[year][case]/1000
    segments=[]
    for s in a['segments']:
        exposure=s['exposure']; elasticity=s['elasticity']
        ai_factor=(demand**elasticity)*((1+s['complexity'][i])**n)
        nonai_factor=(1+s['nonai'][i])**n
        # ramp is a one-time capacity/qualification absorption factor by endpoint, not annual CAGR.
        # For 2029 the same factor is used; no silent extrapolation of a 2028 construction plan.
        gf=((1-exposure)*nonai_factor+exposure*ai_factor)*s['price'][i]*s['ramp'][i]
        revenue=s['anchor']*gf
        segments.append(dict(name=s['name'],market_or_revenue_anchor_bn=s['anchor'],anchor_type='company_revenue_calibration_not_observed_global_TAM',anchor_basis=s['basis'],growth_factor=gf,share_factor=1.0,revenue_bn=revenue,operating_margin=s['margins'][i],growth_components=dict(ai_exposure_assumption=exposure,ai_spend_ratio=demand,elasticity_assumption=elasticity,complexity_annual_assumption=s['complexity'][i],ai_factor=ai_factor,nonai_factor=nonai_factor,price_factor=s['price'][i],capacity_or_qualification_absorption=s['ramp'][i]),all_parameters_classification='independent_scenario_except_identified_anchor'))
    revenue=sum(s['revenue_bn'] for s in segments)
    unallocated=a['unallocated_cost_bn_2026']*(1+a['unallocated_cost_growth'])**n
    op=sum(s['revenue_bn']*s['operating_margin'] for s in segments)-unallocated
    finance=a['net_finance_bn_by_case'][i]
    pretax=op+finance
    rate=a['tax_rate_by_case'][i]
    tax=max(pretax,0)*rate # No automatic tax benefit in an accounting loss.
    posttax=pretax-tax
    minority=max(posttax,0)*a['minority_share_of_positive_posttax']
    ni=posttax-minority
    shares=a['diluted_shares_bn_by_year'][year]
    return dict(year=year,case=case,segments=segments,revenue_bn=revenue,unallocated_cost_bn=unallocated,operating_income_bn=op,net_finance_bn=finance,tax_rate=rate,normal_tax_bn=tax,pretax_income_bn=pretax,minority_bn=minority,normal_net_income_bn=ni,diluted_shares_bn=shares,eps_quote_currency=ni/shares,eps_financial_currency=ni/shares,normal_operating_margin=op/revenue,negative_earnings_pe=None if ni<=0 else 'eligible',tax_benefit_on_loss=False,classification='independent_scenario_CY_full_year_equivalent')

for c in companies:
    for year in (2028,2029):
        for case in CASES:c['rows'].append(generate_row(c,year,case))
    for r in c['rows']:
        assert math.isclose(sum(s['revenue_bn'] for s in r['segments']),r['revenue_bn'],rel_tol=1e-12)
        assert math.isclose(sum(s['revenue_bn']*s['operating_margin'] for s in r['segments'])-r['unallocated_cost_bn'],r['operating_income_bn'],rel_tol=1e-12)
        assert math.isclose((r['operating_income_bn']+r['net_finance_bn'])-r['normal_tax_bn']-r['minority_bn'],r['normal_net_income_bn'],rel_tol=1e-12)
        assert math.isclose(r['normal_net_income_bn']/r['diluted_shares_bn'],r['eps_quote_currency'],rel_tol=1e-12)
        for s in r['segments']:assert math.isclose(s['market_or_revenue_anchor_bn']*s['growth_factor']*s['share_factor'],s['revenue_bn'],rel_tol=1e-12)

out=dict(as_of='2026-10-18 JST',money_unit='billion local currency',share_unit='billion ordinary shares',period='CY2028 and CY2029 full-year equivalent, not strict fiscal quarter build',macro_ai_infrastructure_usd_bn=MACRO,scenario_status='all endpoint values independent scenarios; no probabilities',formula='revenue=sum(anchor × growth_factor × share_factor); OP=sum(segment revenue × OPM)−unallocated; pretax=OP+net_finance; tax=max(pretax,0)×rate; NI=pretax−tax−minority; EPS=NI/diluted shares',growth_method='Revenue-calibrated pipeline when defensible global TAM/share is unavailable. AI-exposed revenue responds to macro spending with subunit elasticity and process/material intensity, non-AI revenue has separate growth. Exposures, elasticity, price/ramp/margins/terminal PE are independent assumptions, not reported market share. share_factor=1 gives no unproven share gain.',model_limitations=['Models prioritize a reproducible screening range over a false precision forecast. B/C quality labels explicitly retain uncertainty.','Quarter/H1 annualization is an anchor only; it is not a company annual earnings forecast or a floor.','Normal R&D, SBC, depreciation and usual acquired intangible amortization remain within operating margins. One-time equity gains/FX windfalls are not extrapolated.','No terminal net cash or interim dividends are added. EPS×PE valuation must not be described as full DCF.','For loss cases PE valuation is undefined, not a zero valuation of assets.','Future normal interest/associated-company income may embed cash earnings, so a separate cash valuation requires reconciliation.'],source_access='All twelve latest primary results were checked on 2026-10-18 via issuer/SEC/JPX web plus issuer-hosted downloads when web extraction failed. Saved public files are in /private/tmp/ai-wide-*.pdf/txt; no authentication or paid data.',companies=companies)
PREFIX.with_suffix('.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')

lines=['# 日本・台湾・欧州装置/材料12社：2028/29年利益・EPSの独自シナリオ','', '確認2026-10-18 JST。金額・株数ともbillion、EPSは現地通貨の普通株1株当たり。株価は親側で取得。全72ケースは会社予想・コンセンサスではない。','', '市場TAMや工程内シェアを一次資料で確認できない企業は、最新部門売上を市場需要へ接続している。公表されないAI売上比率を捏造しないため、モデルの感応度配分は独自仮定として開示した。単純EPS CAGRは使わない。','', '## 共通式','',out['formula'],'', '2026AIインフラ支出1,000bnUSDを校正。2028弱/基準/強=1,000/1,400/1,900、2029=950/1,700/2,500。各部門の成長係数は `(1−AI感応割合)×非AI需要係数 + AI感応割合×AI支出比^弾性×工程複雑化係数` に価格・能力消化係数を乗じる。割合は独自のモデル感応度で、実測AI売上比率や世界市場シェアではない。','', 'SBC、R&D、償却を通常費用に残す。金融/持分/為替益は正常化し、赤字時に税便益を自動計上しない。終点PERは価格を参照して調整しておらず、事業の耐久性と循環に対する独自事前仮定。','', '## EPS一覧','', '| 企業 | 通貨 | 2028弱 | 2028基準 | 2028強 | 2029弱 | 2029基準 | 2029強 | 終点PER弱/基準/強 | 品質 |','|---|---|---:|---:|---:|---:|---:|---:|---|---|']
for c in companies:
    e=[r['eps_quote_currency'] for r in c['rows']]
    lines.append('| '+c['name']+' | '+c['quote_currency']+' | '+' | '.join(f'{x:,.2f}' for x in e)+' | '+'/'.join(str(c['terminal_pe'][k]) for k in CASES)+' | '+c['model_quality']+' |')
lines+=['','## 企業別の根拠と反証','']
for c in companies:
    lines+=['### '+c['name']+'（'+c['symbol']+'）','',c['method'],'','最新一次確認：']
    for f in c['anchor_facts']:
        lines+=['',f'- {f["date"]} / {f["classification"]} / {f["scope"]}: '+json.dumps(f['numbers'],ensure_ascii=False)+f'。[一次資料]({f["source_url"]})']
    lines+=['','株数：'+c['share_basis'],'','終点倍率：'+c['terminal_pe_basis'],'','独自シナリオの主要入力：','', '|部門|売上校正bn|AI感応割合（独自）|弾性|工程複雑化年率 弱/基準/強|価格係数|能力消化係数|OPM弱/基準/強|','|---|---:|---:|---:|---|---|---|---|']
    for s in c['assumptions']['segments']:
        fmt=lambda vs:'/'.join(f'{x:.3g}' for x in vs)
        lines+=['| '+s['name']+f' | {s["anchor"]:.4f} | {s["exposure"]:.2f} | {s["elasticity"]:.2f} | '+fmt(s['complexity'])+' | '+fmt(s['price'])+' | '+fmt(s['ramp'])+' | '+fmt(s['margins'])+' |']
    lines+=['','反証・制約：']+['','; '.join(c['risks'])+'。','', '再計算用の全係数・金融損益・税率・NCI・希薄化分母はJSONとPythonに保存。']
    if c['normalization_adjustments']:lines+=['','正常化：'+'; '.join(c['normalization_adjustments'])]
lines+=['','## とくに残る制約','', 'SUMCOはFSTの9/30みなし連結除外により、過去売上と将来連結売上の範囲が変わる。今回40bnJPYを独自控除したため、精密な継続事業予測として扱えない。SiltronicはEBITDAが黒字でも巨大償却により最終赤字。基準ケースの利益回復には大きな稼働/価格改善が必要。Unimicronは巨額営業外益を延長しない。イビデンは8/4正式短信と8/5説明資料メモの数値不整合を残し、正式短信の550/127/84bnを採用。','', '校正年の季節性、為替、通貨別売上・費用、投資回収CFの年次積上げを省略したスクリーニングモデル。売上成長率とEPS成長率が企業間で違う理由を見せるもので、1円単位の目標株価を保証しない。Q2未発表の会社に10月後半以後の決算を先取りしない。']
PREFIX.with_suffix('.md').write_text('\n'.join(lines)+'\n')
print(f'{len(companies)} companies; {sum(len(c["rows"]) for c in companies)} rows; formulas reconciled')
for c in companies:
    r=next(r for r in c['rows'] if r['year']==2029 and r['case']=='base')
    print(c['symbol'],c['quote_currency'],'rev',round(r['revenue_bn'],3),'NI',round(r['normal_net_income_bn'],3),'EPS',round(r['eps_quote_currency'],3))
