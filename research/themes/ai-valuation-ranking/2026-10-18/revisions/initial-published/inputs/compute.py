#!/usr/bin/env python3
"""14 issuers, 84 independent CY-equivalent scenarios; no network or third-party dependencies.
Money/shares = billion of financial currency/billion shares. All 2028/29 assumptions are ours.
"""
import json, math, pathlib
OUT=pathlib.Path(__file__).resolve().with_suffix('')
CASES=['weak','base','strong']; YEARS=[2028,2029]
MACRO={2028:[1000,1400,1900],2029:[950,1700,2500]}
FX={'USDJPY':157.98699951,'USDTWD':32.4280014,'USDKRW':1340.94995117,'USDHKD':7.84719992}
POOL={2028:[550,910,1273],2029:[522.5,1088,1625]}
# Server/storage manufacturer's booked-revenue opportunity. Do not sum OEM+ODM+chip sales.
SERVER={2026:[500,500,500],2028:[500,800,1150],2029:[475,1050,1600]}
NAND0=315.29411764705884
NAND_BITS=[.12,.22,.30]; NAND_ASP={2028:[.28,.45,.70],2029:[.22,.40,.60]}
DRAM_BITS=[.10,.20,.27]; DRAM_ASP={2028:[.30,.55,.85],2029:[.22,.45,.75]}
HBM_BITS=[.25,.45,.65]; HBM_ASP={2028:[.75,1.20,1.40],2029:[.65,1.10,1.30]}
COST_DOWN=[.05,.10,.12]; FIX_GROW=[.08,.12,.16]
S={
 'amd':('2026-08-04','issuer_actual_and_guidance','https://ir.amd.com/financial-information/sec-filings/content/0000002488-26-000121/q22026991.htm'),
 'amdq':('2026-08-05','issuer_SEC_10Q','https://www.sec.gov/Archives/edgar/data/2488/000000248826000123/amd-20260627.htm'),
 'sk':('2026-07-29','issuer_preliminary_actual','https://news.skhynix.com/en/q2-2026-business-results/'),
 'skfs':('2026-08-18','issuer_SEC_halfyear','https://www.sec.gov/Archives/edgar/data/2120882/000119312526354777/d147827d6k.htm'),
 'skcap':('2026-08-19','issuer_SEC_share_buyback','https://www.sec.gov/Archives/edgar/data/2120882/000119312526356133/d428222d6k.htm'),
 'mu':('2026-09-30','issuer_actual_and_guidance','https://investors.micron.com/news/press-release/2026/Micron-Technology-Inc--Reports-Record-Fiscal-Fourth-Quarter-and-Full-Year-2026-Results/default.aspx'),
 'mudeck':('2026-09-30','issuer_results_and_outlook','https://investors.micron.com/files/doc_financials/2026/q4/Q4-26-Earnings-Deck.pdf'),
 'mu10k':('2026-10-09','issuer_SEC_10K','https://www.sec.gov/Archives/edgar/data/723125/000072312526000023/mu-20260903.htm'),
 'samsung':('2026-07-30','issuer_actual_and_outlook','https://images.samsung.com/is/content/samsung/assets/global/ir/docs/2026_2Q_conference_eng.pdf'),
 'samguide':('2026-10-08','issuer_Q3_preliminary_guidance_NOT_actual','https://news.samsung.com/global/samsung-electronics-announces-earnings-guidance-for-third-quarter-2026'),
 'samshares':('2026-06-30','issuer_share_structure_period_date_retrieved_2026-10-18','https://www.samsung.com/global/ir/stock-information/listing-Info/'),
 'sndk':('2026-08-05','issuer_unaudited_actual_and_guidance','https://www.sandisk.com/company/newsroom/press-releases/2026/2026-08-05-sandisk-reports-fiscal-fourth-quarter-2026-financial-results'),
 'fuji':('2026-07-30','issuer_actual_and_guidance','https://resources.global.fujitsu/prir/2026/07/2026Q1-Financial-Results-en.pdf'),
 'fujideck':('2026-07-30','issuer_segment_results_and_guidance','https://resources.global.fujitsu/prir/2026/07/2026Q1-Financial-Summary-en.pdf'),
 'nec':('2026-07-29','issuer_actual_and_guidance','https://group.nec/assets/global/en/about/ir/library/pdf/202607/2907-01-01.pdf'),
 'necdeck':('2026-07-29','issuer_segment_results_and_guidance','https://group.nec/assets/global/en/about/ir/library/pdf/260729/260729-01.pdf'),
 'dell':('2026-09-01','issuer_actual_and_guidance','https://investors.delltechnologies.com/sec-filings/all-sec-filings/content/0001571996-26-000039/exhibit991earnings8kq2fy27.htm'),
 'hpe':('2026-09-02','issuer_actual_and_guidance','https://www.hpe.com/us/en/newsroom/press-release/2026/09/hpe-reports-fiscal-2026-third-quarter-results.html'),
 'hpefs':('2026-09-02','issuer_financial_tables','https://www.hpe.com/content/dam/hpe/newsroom/2026/09/HPE_Q3FY26_earnings_financial_tables.pdf'),
 'smci10k':('2026-08-31','issuer_SEC_audited_10K','https://www.sec.gov/Archives/edgar/data/1375365/000137536526000022/smci-20260630.htm'),
 'sndk10k':('2026-08-17','issuer_SEC_audited_10K','https://www.sec.gov/Archives/edgar/data/2023554/000162828026057406/sndk-20260703.htm'),
 'sndkday':('2026-08-13','issuer_longterm_nonGAAP_model_NOT_actual','https://www.sandisk.com/company/newsroom/press-releases/2026/2026-08-13-sandisk-investor-day-2026'),
 'smci':('2026-08-11','issuer_preliminary_unaudited_actual_and_guidance','https://ir.supermicro.com/news/news-details/2026/Supermicro-Announces-Fourth-Quarter-and-Full-Fiscal-Year-2026-Financial-Results/default.aspx'),
 'lenovo':('2026-08-13','issuer_actual_and_outlook','https://news.lenovo.com/pressroom/press-releases/q1-fy-2026-27/'),
 'lenovofs':('2026-08-13','issuer_HKEX_quarterly_announcement','https://doc.irasia.com/listco/hk/lenovo/interim/2027/int1q.pdf'),
 'quanta':('2026-08-13','issuer_latest_Q2_results_index_verified','https://www.quantatw.com/Quanta/chinese/investment/financials_icp.aspx'),
 'wiwynn':('2026-08-07','issuer_actual','https://www.wiwynn.com/news/wiwynn-reports-second-quarter-2026-financial-results?hs_amp=true'),
 'wiwynnmonths':('2026-10-18','issuer_latest_monthly_table_retrieved','https://www.wiwynn.com/investors'),
 'wiwynnstock':('2026-09-02','issuer_stock_dividend_effective_date','https://www.wiwynn.com/investors/shareholders-services'),
 'honhai':('2026-08-12','issuer_actual_and_outlook','https://www.foxconn.com/en-us/press-center/press-releases/latest-news/2095'),
 'honhaitrans':('2026-08-18','issuer_Q2_call_transcript','https://image.honhai.com/upload/202608/law_talk/Hon_Hai_2Q26_Results_Transcript_English_20260818_1815.pdf'),
 'twsefs':('2026-10-18','exchange_primary_Q2_2026_cumulative_data_export_date_NOT_release_date','https://openapi.twse.com.tw/v1/opendata/t187ap06_L_ci'),
 'twseshares':('2026-10-17','exchange_issued_ordinary_shares_export_date','https://openapi.twse.com.tw/v1/opendata/t187ap03_L'),
 'twsemonths':('2026-10-17','exchange_September2026_monthly_sales_export_date_NOT_original_release_date','https://openapi.twse.com.tw/v1/opendata/t187ap05_L'),
 'nand':('2026-08-18','industry_researcher_original_estimates','https://www.trendforce.com/presscenter/news/20260818-13186.html'),
 'dram':('2026-09-07','industry_researcher_original_estimates','https://www.trendforce.com/presscenter/news/20260907-13219.html')
}
def fact(src,scope,values):
 d,t,u=S[src]; return {'date':d,'type':t,'scope':scope,'values':values,'url':u}
def company(sym,name,ccy,quality,pe,facts,method,risks,share_note):
 return {'symbol':sym,'name':name,'financial_currency':ccy,'quote_currency':'HKD' if sym=='0992.HK' else ccy,'model_quality':quality,'terminal_pe':dict(zip(CASES,pe)),
 'terminal_pe_status':'independent_prior_assumptions_not_market_consensus_not_fitted_to_price','anchor_facts':facts,'method':method,'risks':risks,'share_basis':share_note,'rows':[]}
def seg(name,anchor,growth=1,share=1,margin=0,**kw):
 rev=anchor*growth*share
 return dict(name=name,market_or_revenue_anchor_bn=anchor,growth_factor=growth,share_factor=share,revenue_bn=rev,operating_margin=margin,**kw)
def row(co,year,i,segs,unallocated,finance,tax,shares,minority=0,minority_rate=0,**kw):
 rev=sum(s['revenue_bn'] for s in segs);op=sum(s['revenue_bn']*s['operating_margin'] for s in segs)-unallocated
 pre=op+finance;tx=max(pre,0)*tax; mi=minority+max(pre-tx,0)*minority_rate;ni=pre-tx-mi
 ep=ni/shares;fx=FX['USDHKD'] if co['symbol']=='0992.HK' else 1
 r={'year':year,'case':CASES[i],'status':'independent_scenario_NOT_company_or_consensus_forecast','macro_ai_spend_usd_bn':MACRO[year][i],
 'segments':segs,'revenue_bn':rev,'unallocated_cost_bn':unallocated,'operating_income_bn':op,'net_finance_bn':finance,'pretax_income_bn':pre,
 'tax_rate':tax,'tax_bn':tx,'minority_bn':mi,'normal_net_income_bn':ni,'diluted_shares_bn':shares,'eps_financial_currency':ep,'fx_quote_per_financial_currency':fx,'eps_quote_currency':ep*fx,
 'expense_basis':'GAAP/IFRS-like economic profit: SBC, recurring depreciation/amortization and R&D remain expenses; no investment revaluation/divestiture gain or exceptional tax benefit projected',**kw}
 co['rows'].append(r);return r
companies=[]
# 1 AMD. Instinct and EPYC split is our estimate; reported DC itself is not pure GPU revenue.
c=company('AMD','AMD','USD','medium_low',[22,30,38],[
 fact('amd','Q2 ended 2026-06-27, consolidated GAAP actual; Q3 company guide',{'revenue_bn':11.536,'operating_income_bn':1.990,'net_income_bn':2.297,'diluted_eps':1.38,'data_center_revenue_bn':6.718,'client_bn':3.062,'gaming_bn':.779,'embedded_bn':.977,'Q3_revenue_guide_bn':13.0}),
 fact('amdq','conditional financing dilution; not vested sales',{'OpenAI_max_warrant_shares_bn':.160,'Meta_max_warrant_shares_bn':.160,'none_vested_at_2026_06_27':True})],
 'AI accelerators = shared NVDA/AVGO electronic pool × independent effective capture; EPYC is separated from Instinct inside reported DC. Non-DC revenue = Q2 client+gaming+embedded ×4 and independent unit/mix growth. Segment margins include direct R&D; unallocated cost retains SBC/acquisition amortization and central costs.',
 ['CUDA/software adoption and Nvidia/ASIC competition','GPU capture rises from estimated ~2% to 7.5% in 2029 base; not an observed market share','capacity/HBM/customer ramp; conditional customer warrants dilute upside','China export restriction and inventory charges'],
 'Q2 EPS-implied diluted anchor ~1.665bn (rounding); forecast 1.74–2.04bn includes SBC and partial/full 320m conditional warrant effect, not immediate guaranteed issuance.')
for y in YEARS:
 t=y-2026
 for i in range(3):
  cap={2028:[.035,.05,.055],2029:[.035,.075,.085]}[y][i]
  ai=seg('Instinct AI accelerator pool capture',POOL[y][i],1,cap,[.25,.38,.43][i],anchor_kind='independent_market_pool_USD_bn',pool_capture_is_not_observed_share=True)
  cpu=seg('EPYC and other DC excluding Instinct',14.872,(1+[.06,.18,.27][i])**t,1,[.28,.37,.42][i],anchor_kind='own_split_of_reported_Q2_DC_annualized',q2_total_DC_annualized_bn=26.872,own_Instinct_anchor_bn=12)
  other=seg('Client gaming embedded',19.272,(1+[.00,.07,.12][i])**t,1,[.16,.22,.26][i],anchor_kind='Q2_actual_annualized')
  row(c,y,i,[ai,cpu,other],[5.4,6.2,7.3][i]*(1.07**(t-2)),[-.1,.1,.3][i],.18,{2028:[1.74,1.85,1.96],2029:[1.77,1.91,2.04]}[y][i],capex_bn=[2.5,4,6][i],cash_conversion_risk='Advanced packaging/HBM supply commitments and inventory; no fab capex deducted a second time from net income.')
companies.append(c)
# Memory. All bit/ASP factors are independent; HBM split/cost allocation not separately disclosed.
def memory_model(sym,name,ccy,pe,anchors,varcost,fixed,othersegs,shares,facts,finance,tax,hbm_capture,nand_capture,quality,risks):
 co=company(sym,name,ccy,quality,pe,facts,
 'Three products HBM/non-HBM DRAM/NAND are disjoint. Revenue = annualized common Q2-2026 calibration × shipped-bit index × ASP index × independent mix/capture factor. Variable production costs = calibrated cost × physical-bit index × unit-cost index; fixed R&D/depreciation/SBC/SG&A grows separately. Product split/cost allocation are our estimates, not issuer segment disclosures. NAND bit/ASP path matches Kioxia model; money shares need not be added across incompatible FX/periods. Broad AI macro selects demand scenarios; memory content/AI adoption and non-AI demand determine the bit path.',
 risks,
 shares['note'])
 co['product_calibration']={'status':'independent_product_split_and_cost_allocation_calibrated_to_reported_or_industry_revenue','anchor_year':2026,'anchor_period':'Q2 revenue level ×4; not a FY2026 forecast','product_revenue_bn':anchors,'variable_production_cost_bn':varcost,'fixed_operating_cost_bn':fixed,'financial_currency':ccy}
 for y in YEARS:
  t=y-2026
  for i in range(3):
   ss=[]
   for p in anchors:
    if p=='HBM':bits=(1+HBM_BITS[i])**t;asp=HBM_ASP[y][i];cap=hbm_capture[i];down=[.04,.08,.10][i]
    elif p=='DRAM_ex_HBM':bits=(1+DRAM_BITS[i])**t;asp=DRAM_ASP[y][i];cap=1;down=COST_DOWN[i]
    elif p=='NAND':bits=(1+NAND_BITS[i])**t;asp=NAND_ASP[y][i];cap=nand_capture[i];down=COST_DOWN[i]
    else:bits=(1+[.00,.04,.08][i])**t;asp=1;cap=1;down=COST_DOWN[i]
    q=bits*cap;cost=varcost[p]*q*(1-down)**t*([1.12,1,1][i] if p!='HBM' else 1)
    rv=anchors[p]*bits*asp*cap
    ss.append(seg(p,anchors[p],bits*asp,cap,1-cost/rv,quantity_factor=bits,asp_factor=asp,unit_cost_factor=(1-down)**t,variable_cost_bn=cost,anchor_kind='common_Q2_2026_calibrated_run_rate_own_product_allocation'))
   for s in othersegs(y,i,t):ss.append(s)
   fixedy=fixed*(1+FIX_GROW[i])**t
   r=row(co,y,i,ss,fixedy,finance[i],tax,shares[y][i],minority_rate=.002 if sym=='005930.KS' else 0,
    memory_fixed_cost_bn=fixedy,bit_asp_scenario_is_independent=True,market_reference={'NAND_global_USD_bn':NAND0*(1+NAND_BITS[i])**t*NAND_ASP[y][i],'DRAM_global_Q2_annualized_USD_bn':154.73*4,'HBM_and_DRAM_bits_not_added':True},capex_share_of_revenue=[.20,.23,.26][i],cash_warning='Net income is not FCF. Capex is paid in cash, depreciation remains in production/fixed costs. Multi-year deposits are liabilities, not permanent free cash.')
 return co
# SK: IFRS Q2 total annual revenue 317274.8; NAND proportion from researcher's product revenue ratio.
sk_total=79318.7*4;sk_nand=sk_total*14.27/(14.27+38.59);sk_hbm=50000;sk_dram=sk_total-sk_nand-sk_hbm
sk_var={'HBM':sk_hbm*.35,'DRAM_ex_HBM':sk_dram*.10,'NAND':sk_nand*.15}
sk_fixed=sk_total-60542.6*4-sum(sk_var.values())
c=memory_model('000660.KS','SK hynix','KRW',[8,11,15],{'HBM':sk_hbm,'DRAM_ex_HBM':sk_dram,'NAND':sk_nand},sk_var,sk_fixed,lambda y,i,t:[],
 {'note':'8/19 SEC total issued ~730.4923m inferred from stated 1% limit; treasury 1.625769m before planned24.07m buyback. Forecast 705–715m diluted allows announced cancellation plus SBC; planned buyback is not assumed completed at cutoff.',2028:[.715,.710,.710],2029:[.715,.705,.705]},
 [fact('sk','Q2 consolidated K-IFRS preliminary actual, KRW bn',{'revenue_bn':79318.7,'operating_income_bn':60542.6,'net_income_bn':93922.6}),fact('skfs','Q2 financial income in KRW bn; excluded from projected recurring profit',{'dividend_income_bn':10027.945,'fair_value_gains_bn':53237.425,'parent_net_income_bn':93820.236}),fact('skcap','shareholder capital actions',{'planned_buyback_shares_bn':.02407,'planned_cost_KRW_bn':40004.34,'period_ends':'2026-11-19','treasury_pre_buyback_bn':.001625769}),fact('dram','external original Q2 estimates; not issuer segments',{'SK_DRAM_USD_bn':38.59,'global_DRAM_USD_bn':154.73}),fact('nand','external original Q2 estimates',{'SK_group_NAND_USD_bn':14.27})],
 [300,1200,2500],.25,[.95,.95,.90],[.90,.98,1.0],'medium_low',
 ['Q2 net profit includes huge investment/dividend gains; none is extended into recurring NI','HBM4 yield/customer concentration and Samsung/Micron share gains','HBM and conventional DRAM have different ASP/margin paths; product split not disclosed','Cyclical ASP compression and high new-fab/packaging depreciation; financial assets require separate valuation'])
companies.append(c)
# Samsung: Q2 memory483200 + other semi26800 + net other176000 = consolidated686000.
sam_mem=120800*4;sam_nand=sam_mem*23.06/(23.06+60.98);sam_hbm=20000;sam_dram=sam_mem-sam_nand-sam_hbm
sam_var={'HBM':sam_hbm*.40,'DRAM_ex_HBM':sam_dram*.12,'NAND':sam_nand*.14};sam_fixed=sam_mem-360000-sum(sam_var.values())
def sam_other(y,i,t):
 return [seg('Foundry/System LSI excluding memory',26800,(1+[-.02,.12,.25][i])**t,1,[-.10,.05,.15][i],anchor_kind='Q2_DS_minus_memory_annualized'),seg('DX Display Harman net of group revenue eliminations',176000,(1+[-.01,.03,.06][i])**t,1,[.02,.065,.09][i],anchor_kind='consolidated_revenue_minus_memory_and_other_DS_not_gross_segment_sum')]
c=memory_model('005930.KS','Samsung Electronics','KRW',[9,12,16],{'HBM':sam_hbm,'DRAM_ex_HBM':sam_dram,'NAND':sam_nand},sam_var,sam_fixed,sam_other,
 {'note':'Common and participating preferred EPS are equal in Q2. Denominator is combined earnings-participating equivalent shares (issued6.64865bn less treasury0.08209bn), not ordinary5.84628bn alone. Forecast6.60–6.70bn includes SBC; EPS per005930 ordinary equivalent.',2028:[6.70,6.65,6.60],2029:[6.70,6.65,6.60]},
 [fact('samsung','Q2 consolidated and semiconductor results KRW bn',{'consolidated_revenue_bn':171500,'operating_income_bn':89490,'DS_revenue_bn':127500,'DS_operating_income_bn':89200,'memory_revenue_bn':120800,'ordinary_and_preferred_eps_KRW':10849}),fact('samguide','Q3 management preliminary guidance, NOT full financial statements',{'revenue_KRW_bn':195000,'operating_income_KRW_bn':107400,'no_Q3_net_income_or_EPS_guidance_in_this_release':True}),fact('samshares','Q2 share structure period, retrieved10/18',{'common_issued_bn':5.846278608,'preferred_issued_bn':.802371203,'common_treasury_bn':.082086705}),fact('nand','external original Q2 estimates',{'Samsung_NAND_USD_bn':23.06,'NAND_share':.293}),fact('dram','external original Q2 estimates',{'Samsung_DRAM_USD_bn':60.98,'DRAM_share':.394})],
 [1500,3000,4500],.24,[1.10,1.25,1.40],[.90,.95,1.0],'medium_low',
 ['Q3速報の高い利益をそのまま将来へ年率換算しない','Memory product mix and cost are own allocation; foundry yield and customer qualifications uncertain','DX memory procurement costs currently depress device profits; internal segment sales are eliminated','Large capex/SBC and ordinary/preferred participation; Chinese DRAM/NAND expansion'])
companies.append(c)
# MU uses common industry CYQ2 product revenue, and latest Q4 actual as a separately disclosed benchmark.
mu_anchors={'HBM':15,'DRAM_ex_HBM':144-15,'NAND':47.4,'NOR_other':1.316}
mu_var={'HBM':6.0,'DRAM_ex_HBM':12.90,'NAND':6.636,'NOR_other':.50}
# Total common Q2 revenue192.716. All-in operating cost calibrated to20% of that level; Q4 ex-license GM not projected straight.
mu_fixed=sum(mu_anchors.values())*.20-sum(mu_var.values())
c=memory_model('MU','Micron','USD',[8,12,16],mu_anchors,mu_var,mu_fixed,lambda y,i,t:[],
 {'note':'Latest Q4 diluted1.147bn, Q1FY27 guide~1.15bn. Forecast1.17–1.21bn includes continuing SBC; no unannounced buyback assumed.',2028:[1.17,1.18,1.19],2029:[1.18,1.19,1.21]},
 [fact('mu','FY26/Q4 consolidated GAAP actual and Q1FY27 guide',{'FY_revenue_bn':133.188,'FY_operating_income_bn':99.340,'FY_net_income_bn':84.969,'FY_diluted_eps':74.33,'Q4_revenue_bn':54.229,'Q4_operating_income_bn':43.751,'Q4_net_income_bn':37.701,'Q4_diluted_shares_bn':1.147,'Q1FY27_revenue_guide_bn':61.5,'Q1FY27_GAAP_EPS_guide':37.84}),fact('mudeck','latest product results and company outlook, not our forecasts',{'Q4_DRAM_revenue_bn':39.8,'Q4_NAND_revenue_bn':14.1,'Q4_DC_SSD_revenue_nearly_bn':10,'expected_2027_2028_DRAM_bit_growth':'low20s_pct','expected_NAND_bit_growth':'mid20s_pct','SCAs_signed':26,'estimated_revenue_share_through2030':'>35%','customer_financial_commitments_bn':32}),fact('mu10k','10K annual actual and contract footnote',{'SBC_bn':1.285,'RPO_bn':134,'customer_contract_liabilities_bn':13,'deposits_repayment':'mostly2029–2031','normal_effective_tax_rate_FY26':.148}),fact('dram','common CYQ2 industry calibration, separate from later FYQ4',{'Micron_DRAM_bn':36}),fact('nand','common CYQ2 calibration',{'Micron_NAND_bn':11.85})],
 [.2,1,2],.18,[1.0,1.10,1.05],[.95,1.10,1.12],'medium_low',
 ['会社は2027/28供給不足を予想するが、独自基準は2028/29ASP調整を置く。会社見通しの全面延長ではない','HBM allocation not separately disclosed; common Q2 calendar calibration differs from latest August-quarter prices','SCA price bands protect some revenue, exact floors/mix not public; deposits must be repaid','Large fabs/packaging capex, Chinese competition and industry bit supply expansion'])
companies.append(c)
# SNDK: no DRAM; no separate addition of JV production to branded NAND/SSD sales.
c=memory_model('SNDK','Sandisk','USD',[8,12,16],{'NAND':8.965*4},{'NAND':(8.965*(1-.846))*4},.545*4,lambda y,i,t:[],
 {'note':'Q4 diluted157m vs basic147m; economic forecast160–165m retains SBC/equity-award dilution and does not assume full15.5bn buyback completion.',2028:[.160,.160,.162],2029:[.162,.162,.165]},
 [fact('sndk','FY26/Q4 unaudited GAAP and next-quarter management guide',{'FY_revenue_bn':20.248,'FY_operating_income_bn':12.389,'FY_net_income_bn':11.433,'FY_diluted_eps':73.76,'Q4_revenue_bn':8.965,'Q4_gross_margin':.846,'Q4_op_income_bn':7.037,'Q4_net_income_bn':6.903,'Q4_equity_gain_bn':.804,'Q4_SBC_bn':.067,'Q4_diluted_shares_bn':.157,'Q1FY27_revenue_guide_bn':[10.3,10.8],'Q1FY27_adjusted_EPS_guide':[44,46]}),fact('sndk10k','audited FY26 consolidated actual and share structure',{'revenue_bn':20.248,'operating_income_bn':12.389,'net_income_bn':11.433,'diluted_shares_bn':.155,'dilution_instruments':'employee_RSU_PSU_ESPP_no_convertible_needed'}),fact('sndkday','company FY2028–FY2030 longterm nonGAAP framework, NOT our base assumptions',{'revenue_growth':'mid_to_high_teens_pct','gross_margin':.80,'operating_margin':.75,'adjusted_FCF_margin':.50,'NBM_FY27_bit_coverage':'~50%','NBM_FY28_bit_coverage':'~two_thirds'}),fact('nand','common Q2 brand NAND calibration; SSD included',{'SanDisk_NAND_Q2_USD_bn':8.97,'global_NAND_Q2_derived_bn':NAND0/4})],
 [-.05,.10,.25],.18,[1,1,1],[.96,1.06,1.14],'medium_low',
 ['株式評価益0.804bnを反復利益へ延長しない','eSSD qualification/customer agreements support demand but NAND remains price-sensitive','JV wafer activity is not additional branded NAND demand; deposits/flash-venture capex affect cash','Our base ASP/margin are below company FY28–30 nonGAAP75%OP framework; this is an explicit skeptical scenario, not company consensus; HBF upside excluded'])
companies.append(c)
# Japanese service providers. Service brands are not AI-only revenues.
c=company('6702.T','富士通','JPY','medium',[14,20,26],[fact('fuji','FY26Q1 actual and FY26 endingMarch2027 company guide, JPYbn',{'Q1_revenue':779.377,'Q1_GAAP_OP':52.534,'Q1_parent_NI':40.134,'Q1_diluted_EPS':23.06,'issued_shares_bn':1.739778265,'treasury_shares_bn':.005000980,'FY_revenue_guide':3510,'FY_GAAP_OP_guide':415,'FY_parent_NI_guide':310}),fact('fujideck','company FY26 segment plan, JPYbn; Uvance included within services',{'service_solutions_revenue':2470,'hardware_solutions_revenue':960,'ubiquitous_revenue':160,'revenue_elimination':-80,'Uvance_revenue':840,'service_adjusted_OP':430,'corporate_adjusted_cost':95,'GAAP_adjustment_cost':10})],
 'Uvance and remaining services are disjoint; Uvance includes non-AI transformation, not pure AI TAM. Demand = enterprise IT expansion × independent AI adoption elasticity; hardware/PC revenues separate. Keep corporate105bn baseline including recurring GAAP adjustment and SBC; no past divestiture gain.',
 ['AI productivity savings may be competed away through lower labor billing','Uvance growth cannibalizes legacy work; enterprise deployment slower than GPU capex','Overseas restructuring and project losses','FY25 parentNI449.4bn included discontinued gains; excluded from forecast anchor'],
 'Q1 diluted EPS ~1.7404bn implied; 2028/29 economic diluted1.70–1.76bn after announced-program calibration, not a guaranteed future buyback.')
for y in YEARS:
 t=y-2026
 for i in range(3):
  adoption=(MACRO[y][i]/1000)**[.20,.40,.55][i]*(1+[.02,.06,.10][i])**t
  ss=[seg('Uvance within Service Solutions',840,adoption,1,[.17,.22,.26][i],anchor_kind='company_FY26_plan_NOT_AI_only'),seg('Other Service Solutions excluding Uvance',1630,(1+[-.01,.025,.04][i])**t,1,[.14,.175,.20][i]),seg('Hardware Solutions',960,(1+[-.04,-.02,.02][i])**t,1,[.04,.065,.08][i]),seg('Ubiquitous Solutions',160,(1+[-.06,-.02,.02][i])**t,1,[.07,.10,.13][i]),seg('Intersegment revenue elimination',-80,(1+.02)**t,1,0)]
  row(c,y,i,ss,105*(1+[.03,.05,.07][i])**t,[2,4,6][i],.29,{2028:[1.75,1.72,1.70],2029:[1.76,1.71,1.70]}[y][i],minority=3,capex_share_of_revenue=.035,AI_demand_link='enterprise deployment elasticity, not direct infrastructure-spend share')
companies.append(c)
c=company('6701.T','NEC','JPY','medium_low',[16,22,28],[fact('nec','Q1FY27/3 actual and revised full-year company forecast, JPYbn',{'Q1_revenue':819.774,'Q1_GAAP_OP':58.770,'Q1_nonGAAP_OP':74.738,'Q1_parent_NI':49.698,'Q1_EPS':37.47,'average_ordinary_shares_bn':1.326343019,'FY_revenue_guide':3540,'FY_nonGAAP_OP_guide':430,'FY_nonGAAP_parent_NI_guide':290}),fact('necdeck','company annual segment guide excludes CSG acquisition; JPYbn',{'BluStellar_domestic_IT':760,'legacy_domestic_IT':1415,'international_IT':450,'social_infrastructure':780,'other':135,'corporate_nonGAAP_cost':54,'CSG_not_in_annual_guide':True})],
 'BluStellar inside IT services is disjoint from legacy; not AI-only. Latest company full-year forecast excludes newly consolidated CSG, so add separate independently assumed200bn steady-year CSG revenue (not company guidance). Social infrastructure includes defense and submarine cable; no blanket AI growth applied. Subtract corporate cost and recurring acquisition amortization/SBC.',
 ['CSG full-year allocation and integration uncertainty; company annual guide not yet revised for acquisition','BluStellar includes migration of legacy business, not all incremental AI revenue','NonGAAP company guide excludes SBC/acquisition amortization; future model retains them','Defense/cable order cycles and project execution'],
 '2025 five-for-one split reflected; Q1 average1.326343bn. Forecast1.34–1.37bn diluted retains SBC; old pre-split EPS not used.')
for y in YEARS:
 t=y-2026
 for i in range(3):
  ad=(MACRO[y][i]/1000)**[.15,.35,.50][i]*(1+[.01,.07,.12][i])**t
  ss=[seg('BluStellar domestic IT (not pure AI)',760,ad,1,[.16,.20,.24][i]),seg('Legacy domestic IT',1415,(1+[-.05,-.03,-.01][i])**t,1,[.12,.14,.16][i]),seg('International IT before CSG',450,(1+[.02,.06,.09][i])**t,1,[.10,.125,.15][i]),seg('CSG acquired business',200,(1+[.01,.04,.07][i])**t,1,[.09,.13,.16][i],anchor_kind='independent_full_year_acquisition_bridge_NOT_issuer_guide'),seg('Social infrastructure defense cable telecom',780,(1+[.02,.06,.10][i])**t,1,[.11,.145,.17][i]),seg('Other',135,1,1,.03)]
  corp=54*(1+.05)**t;amort_sbc=63.872*(1+[.03,.08,.12][i])**t
  row(c,y,i,ss,corp+amort_sbc,[-8,-8,-10][i],.29,{2028:[1.34,1.35,1.36],2029:[1.35,1.36,1.37]}[y][i],minority=4,corporate_cost_bn=corp,recurring_acquisition_amortization_SBC_bn=amort_sbc,capex_share_of_revenue=.045)
companies.append(c)
# Server/platform manufacturers. Gross booked revenue is not additive across OEM and ODM.
def srv_company(sym,name,ccy,quality,pe,facts,method,risks,shares):
 co=company(sym,name,ccy,quality,pe,facts,method,risks,shares);co['double_count_warning']='OEM/ODM gross booked sales often include GPU/memory vendor cost and may be purchases from another covered ODM. Do NOT sum companies as independent AI final demand. Procurement/consignment changes can reduce revenue without reducing unit shipment or economic profit.';return co
c=srv_company('DELL','Dell Technologies','USD','medium',[10,15,20],[fact('dell','Q2FY27 consolidated GAAP actual and full-year issuer guide',{'Q2_revenue_bn':46.971,'Q2_OP_bn':5.385,'Q2_parent_NI_bn':4.133,'Q2_diluted_shares_bn':.652,'Q2_AI_servers_bn':16.401,'Q2_traditional_server_network_bn':10.531,'Q2_storage_bn':4.850,'Q2_CSG_bn':15.034,'Q2_CFO_bn':2.225,'Q2_unadjusted_FCF_bn':.986,'FY27_revenue_guide_bn':192,'FY27_AI_server_guide_bn':74,'FY27_GAAP_EPS_guide':24.37,'AI_orders_bn':60.9,'AI_backlog_bn':95})],
 'AI74bn uses FY27 management guide as forward calibration, not FY2026 actual. Other ISG and CSG use Q2×4. AI revenue follows independent server/storage opportunity pool and market capture; AI margin is our estimate because issuer discloses ISG aggregate margin only. Corporate costs retain SBC and acquisition amortization.',
 ['Backlog is not guaranteed cash; Q2 FCF0.986bn vs adjustedFCF8.149bn dominated financing adjustments','GPU pass-through inflates revenue; AI-alone margin not disclosed','ODM competition and Nvidia reference-design bargaining','Customer financing and working capital needs constrain buybacks'],
 'Q2 diluted652m; future630–660m, modest buyback assumption offset by SBC.')
for y in YEARS:
 t=y-2026
 for i in range(3):
  ss=[seg('AI-optimized servers',74,SERVER[y][i]/500,[.80,.95,1.05][i],[.045,.105,.135][i],anchor_kind='FY27_issuer_guide_forward_calibration'),seg('Traditional servers networking storage',61.524,(1+[.00,.055,.10][i])**t,1,[.13,.18,.21][i]),seg('Client Solutions',60.136,(1+[-.02,.025,.05][i])**t,1,[.055,.075,.085][i]),seg('Other corporate revenue',.620,1,1,0)]
  row(c,y,i,ss,[2.4,3.0,4.0][i]*(1.05**(t-2)),[-1.2,-1.1,-1][i],.23,{2028:[.660,.640,.630],2029:[.660,.630,.620]}[y][i],capex_share_of_revenue=.025,working_capital_days_assumption=[40,35,30][i])
companies.append(c)
c=srv_company('HPE','Hewlett Packard Enterprise','USD','medium_low',[10,14,18],[fact('hpe','Q3FY26 issuer results and outlook; Cloud&AI includes nonAI',{'Q3_revenue_bn':12.213,'Q3_GAAP_OP_margin':.114,'Q3_networking_revenue_bn':2.9,'Q3_cloud_AI_revenue_bn':9.0,'Q3_all_servers_bn':6.8,'Q3_storage_bn':1.3,'Q3_financial_services_bn':.9,'FY26_GAAP_EPS_guide':[2.93,3.03],'FY27_revenue_growth_guide':[.13,.17],'FY27_nonGAAP_OP_margin_guide':[.14,.15]}),fact('hpefs','Q3 GAAP actual/reconciliation',{'OP_bn':1.393,'net_earnings_bn':1.540,'equity_sale_gain_bn':.444,'SBC_bn':.165,'intangibles_amort_bn':.315,'diluted_shares_bn':1.449,'CFO_bn':1.6,'FCF_bn':1.0})],
 'Q3 server27.2bn annualized split40%AI/60%traditional independently; Cloud&AI segment is not all AI. Networking includes acquired Juniper; growth is not wholly organic. Apply segment operating margins, then retain corporate/SBC/intangible amortization2.8bn baseline. Exclude H3C/equity-sale gain from recurring finance.',
 ['AI server split not disclosed and customer shipment timing lumpy','Juniper acquisition integration, debt, and purchased-intangible amortization','Networking competition and server component pricing','Financing receivables and customer capital demand'],
 'Q3 diluted1.449bn includes if-converted effects. Forecast1.46–1.52bn after preferred conversion: no double subtraction of preferred dividends on if-converted earnings.')
for y in YEARS:
 t=y-2026
 for i in range(3):
  ss=[seg('AI server estimated part',10.88,SERVER[y][i]/500,[.90,1.05,1.20][i],[.08,.14,.17][i],anchor_kind='own40pct_split_of_Q3_server_annualized'),seg('Traditional server storage financing',25.12,(1+[.00,.045,.07][i])**t,1,[.14,.18,.20][i]),seg('Networking incl Juniper',11.6,(1+[.03,.12,.18][i])**t,1,[.20,.24,.27][i]),seg('Corporate investments and other',1.252,1,1,-.24)]
  row(c,y,i,ss,2.8*(1+[.02,.035,.05][i])**t,[-.45,-.35,-.25][i],.22,{2028:[1.46,1.48,1.50],2029:[1.47,1.50,1.52]}[y][i],capex_share_of_revenue=.045,working_capital_days_assumption=[45,40,35][i],preferred_dividends_bn=0)
companies.append(c)
c=srv_company('SMCI','Super Micro Computer','USD','low',[8,12,18],[fact('smci','FY26 preliminary unaudited actual and FY27 company guide',{'FY_revenue_bn':39.063072,'FY_GAAP_OP_bn':2.770486,'FY_parent_common_NI_bn':2.217365,'FY_EPS':3.26,'Q4_revenue_bn':11.119777,'Q4_GAAP_OP_bn':1.488064,'Q4_net_income_bn':1.178217,'Q4_diluted_shares_bn':.705001,'FY_SBC_bn':.412115,'FY_CFO_bn':-6.809886,'FY_inventory_bn':12.895949,'FY27_revenue_guide_bn':[65,72],'Q1FY27_revenue_guide_bn':[14.5,15.5],'Q1FY27_GAAP_diluted_shares_guide_bn':.745}),fact('smci10k','audited FY26 filed8/31 confirms results; updated governance status supersedes preliminary8/11',{'FY_revenue_bn':39.063072,'FY_GAAP_OP_bn':2.770486,'FY_NI_bn':2.230453,'FY_CFO_bn':-6.809886,'financial_statement_audit':'unqualified','internal_control_audit':'material_weakness_IT_general_controls','internal_export_investigation':'completed; no basis found to question prior financial statements','government_inquiries':'ongoing'})],
 'FY27 company revenue guide midpoint68.5bn is forward calibration (not FY26 actual). Independently allocate80% to AI servers and20% other. AI gross booked revenue follows server/storage pool with share erosion in base; full GAAP-like operating margin retains SBC, R&D and depreciation. No adjustment of quarter-specific profit to remove SBC.',
 ['FY26 audited8/31 with unqualified financial-statement opinion; IT general-control material weakness remains. Independent export review completed without finding basis to question financial statements; government inquiries continue','FY26 CFO−6.81bn despite positive NI; inventory and customer collection require financing','FY27 midpoint forecast is79% above FY26 and may fail; backlog is not revenue','Mandatory convertible preferred and convertible notes materially dilute economic EPS','Large enterprise mix may not sustain Q4 gross17.5%'],
 '2024年1:10分割後。6/30普通株656.882499m＋優先株4.3125m×転換率30.3040〜36.3640＝130.689〜156.819750m＋既存CB全転換73.803045m。潜在株合計は最小861.374544m、最大887.505294m。現金決済の資金手当を仮定せず最大側に将来株式報酬を上乗せし、2028年930/950/980m、2029年950/980/1020m（弱/基準/強）の経済的希薄化株数を使用する。優先株は転換済み相当として配当を重複控除せず、CB利息は加戻さず金融費用全額を残す保守的経済EPSで、厳密なGAAP希薄化EPSではない。')
for y in YEARS:
 t=y-2026
 for i in range(3):
  ss=[seg('AI servers and rack solutions estimated',54.8,SERVER[y][i]/500,[.60,.85,1.10][i],[.025,.065,.095][i],anchor_kind='own80pct_of_FY27_guide_midpoint'),seg('Other enterprise server storage edge',13.7,(1+[-.02,.04,.08][i])**t,1,[.05,.075,.09][i])]
  row(c,y,i,ss,[.25,.35,.5][i],[-.30,-.25,-.20][i],.22,{2028:[.930,.950,.980],2029:[.950,.980,1.020]}[y][i],capex_share_of_revenue=.008,working_capital_days_assumption=[100,75,55][i],preferred_dividends_bn=0,source_quality_caveat='Audited FY26 available8/31; low model confidence reflects forward guide, AI revenue split and execution/funding/control risk, not absence of audit')
companies.append(c)
c=srv_company('0992.HK','Lenovo','USD','medium_low',[8,11,15],[fact('lenovo','Q1FY26/27 issuer segment actual',{'group_revenue_bn':26.943,'IDG_bn':17.1,'ISG_bn':8.5,'SSG_bn':2.9,'ISG_OP_bn':.777,'SSG_OP_bn':.697,'AI_related_bn':9.3,'AI_pipeline_bn':54}),fact('lenovofs','HKFRS Q1 reconciliation and dilution',{'reported_OP_bn':.019202,'reported_parent_NI_bn':-.608600,'warrant_FV_loss_bn':1.690299,'financial_asset_FV_gain_bn':.250083,'M_A_amortization_bn':.016524,'basic_denominator_bn':12.077851410,'issued_warrant_instruments_bn':1.150,'ordinary_issued_shares_bn':12.404659302,'2029_CB_adjusted_potential_shares_bn':.421385398,'2028_CB_adjusted_potential_shares_bn':1.667342582,'2033_CB_adjusted_potential_shares_bn':.438343592,'warrants_adjusted_potential_shares_bn':1.229930495,'fully_issued_plus_all_potential_bn':16.161661369})],
 'IDG/ISG/SSG gross segment sales include intersegment revenue: subtract elimination1.557bn×4 and scale with SSG. ISG34bn annualized split18bnAI/16bntraditional independently; AI9.3bn reported includes NPU PCs/phones and services, not pure server sales. Remove warrant fair-value loss AND investment fair-value gain; retain SBC, recurring R&D and M&A amortization. Use fully diluted economic share count for positive future earnings.',
 ['Q1reported HKFRS loss reflects1.690bn warrant fair-value remeasurement; simply extending reported EPS invalid','Removing both financial gains and losses does not justify removing SBC or ordinary amortization','Full warrant/convertible dilution vs cash settlement uncertain','Thin hardware margin, inventory/customer finance; SSG not pure AI'],
 'Q1会計赤字の分母12.077851410bnは逆希薄化証券を含まない。8/8条件調整後は普通株12.404659302bn＋2029CB0.421385398bn＋2028CB1.667342582bn＋2033CB0.438343592bn＋ワラント最大転換1.229930495bn＝16.161661369bn。2033CBは通常2032年まで転換不可だが、長期の経済的希薄化として前倒し保守計上する。将来株式報酬を上乗せし16.2〜16.5bnを使用。現金決済・発行代金による買戻しを仮定しない。EPSはUSD×USDHKD7.84719992で一度だけHKD換算し、0992普通株と比較する。')
for y in YEARS:
 t=y-2026
 for i in range(3):
  service_growth=(1+[.03,.06,.09][i])**t*(MACRO[y][i]/1000)**[.10,.25,.40][i]
  ss=[seg('IDG PCs smartphones',68.4,(1+[-.015,.03,.06][i])**t,1,[.05,.065,.075][i]),seg('ISG AI server estimated',18,SERVER[y][i]/500,[.80,.95,1.10][i],[.035,.075,.10][i]),seg('ISG traditional server storage',16,(1+[.01,.05,.08][i])**t,1,[.055,.09,.11][i]),seg('SSG services gross',11.6,service_growth,1,[.18,.22,.24][i]),seg('Intersegment revenue elimination',-6.228,service_growth,1,0)]
  row(c,y,i,ss,4.914*(1+[.015,.045,.07][i])**t,[-.60,-.45,-.35][i],.24,{2028:[16.2,16.3,16.4],2029:[16.3,16.4,16.5]}[y][i],minority=[.08,.12,.20][i],capex_share_of_revenue=.025,working_capital_days_assumption=[65,55,45][i])
companies.append(c)
# Taiwan: latest Sep sales + Q3 repeated for Q4 = independent 2026 calibration, NOT company forecast.
TW={
 '2382.TW':dict(name='Quanta Computer',nine=2961.358288,h1=1845.813767,op=57.268079,parent=49.843907,eps=12.93,shares=4.107627432,ai=.65,trad=.15,other=.20,cap=[.80,1,1.05],aim=[.018,.033,.043],tm=[.035,.055,.065],om=[.03,.045,.055],finance=[-4,0,4],tax=.23,mi=.005,pe=[10,15,20]),
 '6669.TW':dict(name='Wiwynn',nine=989.278016,h1=554.660326,op=37.676176,parent=29.083507,eps=156.38,shares=.560199772,ai=.80,trad=.20,other=0,cap=[.85,1.05,1.15],aim=[.04,.065,.08],tm=[.05,.075,.085],om=[0,0,0],finance=[-4,-4,-5],tax=.23,mi=0,pe=[12,18,24]),
 '2317.TW':dict(name='Hon Hai Precision',nine=7669.772510,h1=4645.427824,op=170.451721,parent=109.893220,eps=7.84,shares=14.075746497,ai=.45,trad=.15,other=.40,cap=[.85,.95,1.05],aim=[.027,.042,.050],tm=[.03,.045,.05],om=[.027,.035,.04],finance=[-35,-35,-40],tax=.25,mi=.13,pe=[9,13,17])
}
for sym,p in TW.items():
 extra=[]
 if sym=='2382.TW':
  extra=[fact('quanta','Q2 results event confirmed; numerical PDF fetch blocked by site protection',{'event_date':'2026-08-13','numbers_from_exchange_primary_API_instead':True})]
 elif sym=='6669.TW':
  extra=[fact('wiwynn','Q2 actual and operating model',{'Q2_revenue_bn':278.153,'Q2_PAT_bn':14.969,'Q2_OP_margin':.073,'Q2_pre_stock_dividend_EPS':80.43,'procurement_agency_from_April':'specified customer memory excluded from revenue and COGS','H2_capex_budget_USD_bn':.942,'proposed_CB_TWD_bn':15,'syndicated_loan_USD_bn':1.5}),fact('wiwynnstock','stock dividend',{'stock_dividend_TWD_per_old_share':19.8279460,'par_value_TWD':10,'share_multiplier':2.9827946,'ex_rights':'2026-09-02','stock_distribution':'2026-10-14'})]
 else:
  extra=[fact('honhai','Q2 actual; company outlook',{'Q2_revenue_TWD_bn':2530,'Q2_OP_TWD_bn':94.8,'Q2_parent_NI_TWD_bn':60,'Q2_EPS':4.27,'cloud_networking_Q2_revenue_share':'>50%','full_year_AI_rack_unit_growth':'more_than_double_company_expectation'}),fact('honhaitrans','cash and gross revenue recognition',{'H1_CFO_TWD_bn':-69.1,'H1_FCF_TWD_bn':-150.0,'net_cash_TWD_bn':219.8,'midlongterm_OP_margin_target':'>3%','ASIC_projects':'mostly_consignment_customer_components_may_not_enter_revenue'})]
 facts=[fact('twsefs','Q2 cumulative Jan-Jun2026, TWD bn; EPS is then-current share basis',{'H1_revenue_bn':p['h1'],'H1_operating_income_bn':p['op'],'H1_parent_NI_bn':p['parent'],'H1_basic_EPS':p['eps']}),fact('twsemonths','latest September cumulative sales; original release occurred before10/18, API export10/17',{'JanSep_sales_TWD_bn':p['nine'],'Q3_sales_derived_TWD_bn':p['nine']-p['h1']}),fact('twseshares','10/17 issued ordinary shares',{'ordinary_shares_bn':p['shares']})]+extra
 note='Current ordinary shares from exchange, not H1 weighted average. Forecast grows share count for employee/convertible dilution.'
 if sym=='6669.TW':note+=' Q2EPS80.43 is before stock dividend; old shares×2.9827946; current560.199772m issued is used. Additional proposed15bnTWD CB may dilute.'
 if sym=='2382.TW':note+=' 4.107627432bn current differs from H1EPS-implied~3.855bn; latest issued basis used.'
 method='2026 calibration = Jan-Sep actual revenue + independently assumed Q4 equal to Q3 (not company FY guidance). Independently allocate AI/traditional/other product shares; product ratios not issuer audited AI segments. AI revenue follows common server/storage pool and independent capture; nonAI ordinary unit/mix growth. All segment margins include SBC, R&D, ordinary depreciation; only normal net finance retained. '
 if sym=='6669.TW':method+='Revenue basis uses post-April memory procurement agency recognition; no grossing up of customer-supplied memory. '
 risks=['AI/product revenue allocation is independent, not separately disclosed segment fact','GPU/ASIC component pass-through vs consignment changes distort gross revenue comparisons','US production localization, yields, component constraints and trade restrictions','Customer concentration, inventory/receivable financing and capex; profit is not distributable cash']
 if sym=='6669.TW':risks+=['NRE raised Q2 margin; base uses6.5% AI operating margin rather than extrapolating all7.3%','Stock dividend and CB conversion materially affect per-share comparison']
 c=srv_company(sym,p['name'],'TWD','medium_low',p['pe'],facts,method,risks,note)
 anchor=2*p['nine']-p['h1'];c['calibration_2026']={'status':'independent_run_level_NOT_company_guide','revenue_bn':anchor,'formula':'JanSep actual + Q3 actual repeated as own Q4 assumption','AI_fraction_independent':p['ai'],'traditional_fraction_independent':p['trad'],'other_fraction_independent':p['other']}
 for y in YEARS:
  t=y-2026
  for i in range(3):
   ss=[seg('AI GPU ASIC server rack estimated',anchor*p['ai'],SERVER[y][i]/500,p['cap'][i],p['aim'][i],anchor_kind='independent_product_split_of_2026_calibration'),seg('Traditional server networking estimated',anchor*p['trad'],(1+[.01,.05,.08][i])**t,1,p['tm'][i])]
   if p['other']:ss.append(seg('PC smart consumer and other estimated',anchor*p['other'],(1+[-.02,.03,.06][i])**t,1,p['om'][i]))
   sh=p['shares']*(1+[.010,.012,.020][i])**t
   row(c,y,i,ss,0,p['finance'][i],p['tax'],sh,minority_rate=p['mi'],capex_share_of_revenue=.025 if sym=='2317.TW' else (.035 if sym=='6669.TW' else .015),working_capital_days_assumption=[65,50,40][i],revenue_recognition_warning='consignment/procurement-agency products remain net of customer-supplied component cost')
 companies.append(c)
# Japanese UI descriptions. Source titles/scopes remain in their original language.
JA={
'AMD':{
 'method':'AIアクセラレータ売上はNVIDIA・Broadcomと共有する電子部品売上プール×独自の実効捕捉係数。会社開示のデータセンター売上をInstinctとEPYC等へ独自に分け、PC・ゲーム・組込みを別計算する。部門利益から株式報酬・買収償却・本社費用を残して正常利益を算出する。',
 'risks':['2029年基準のAIプール捕捉7.5%は独自仮定で、現在の観測シェアではない','CUDA・NVIDIA・専用ASICとの競争でGPU採用が伸びない可能性','HBM・実装能力、顧客の導入時期、中国輸出規制','顧客向け最大3.2億株の条件付きワラントと継続的な株式報酬による希薄化'],
 'key_condition':'MI450以降の顧客採用が進みAIプールの取り分が増えることが必要で、CUDA・ASICとの競争と最大3.2億株の条件付き希薄化が主要リスク。'},
'000660.KS':{
 'method':'HBM・汎用DRAM・NANDを重複なく分け、2026年4〜6月の校正売上×出荷ビット数×単価×独自の製品構成・捕捉係数で予測する。数量とビット原価から製造費を計算し、研究開発・減価償却・株式報酬等の固定費を残す。NANDの数量・単価経路は既存キオクシア試算と統一した。製品別売上・原価の内訳は独自配賦で、会社開示値ではない。',
 'risks':['Q2純利益には多額の配当・金融商品評価益があり、将来の反復利益へ延長しない','HBM4の歩留まり・顧客集中、Samsung・Micronへの取り分流出','HBMと汎用DRAMの単価・利益率は異なり、HBM比率だけで収益改善を保証しない','汎用DRAM/NANDの値下がりと新工場・先端実装の償却負担。保有金融資産の価値は別評価が必要'],
 'key_condition':'金融評価益を除いてもHBM量産と汎用DRAMの利益が残ることが成立条件で、価格調整・競合増産・新工場の償却負担でEPSが大きく振れる。'},
'005930.KS':{
 'method':'HBM・汎用DRAM・NANDの数量、単価、ビット原価を別計算し、ファウンドリ等と端末・ディスプレー等を加える。部門間売上の重複を消去し、株式報酬・償却・研究開発費を残す。普通株と参加型優先株の利益分配を考慮した株数でEPSを計算する。10月8日のQ3速報は会社の予備見通しで、詳細費用の校正はQ2を使う。',
 'risks':['Q3速報の高利益をそのまま恒常利益として年率換算しない','メモリ製品別の売上・費用配分は独自仮定で、HBM認定と歩留まりも不確実','端末部門のメモリ調達費と半導体部門の利益が逆方向に動く場合がある','大型設備投資・株式報酬、普通株と優先株の配分、中国メモリメーカーの増産'],
 'key_condition':'HBMの顧客認定・量産を進めつつ汎用メモリの価格調整を吸収する必要があり、ファウンドリの赤字と大型投資が利益回復を妨げる可能性。'},
'MU':{
 'method':'HBM・汎用DRAM・NAND・その他を分離し、共通の2026年4〜6月の校正売上に出荷数量・単価・費用を掛ける。最新8月期四半期と会社の2027/28年供給不足見通しは別の実績・会社見通しとして示し、独自基準には2028/29年の単価調整を置く。株式報酬・研究開発・通常償却は除外しない。',
 'risks':['会社は2027/28年も供給不足を予想するが、独自基準はその見通しを全面延長していない','HBMの内訳は独自配賦で、共通Q2校正と最新四半期には価格・期間の差がある','複数年契約の価格バンドは一部収益を守るが、具体的な下限・製品構成は非公開','新工場・実装投資、中国競争、顧客前受金の2029〜31年返済と運転資金負担'],
 'key_condition':'価格バンド付き契約とHBM・企業向けSSDが利益を支えることが必要で、メモリ単価正常化と新工場投資・顧客前受金返済が主要リスク。'},
'SNDK':{
 'method':'NANDブランド売上にSSDを含め、出荷ビット数×単価×独自の取り分変化から売上を予測する。JVのウェハ製造をブランド売上へ二重加算しない。株式報酬と研究開発費を残し、株式評価益を除く。会社のFY2028〜30調整後営業利益率75%という長期枠組みより、独自基準は慎重な単価・利益率を置く。',
 'risks':['直近四半期の株式評価益0.804bnUSDを反復利益に含めない','企業向けSSD・NBM契約は支えになるが、NANDの単価循環は残る','JV投資と顧客前受金は現金の自由度に影響する','独自基準は会社の長期調整後利益率75%を下回る。HBFの追加利益は織り込まない'],
 'key_condition':'NBM契約と企業向けSSDでNAND価格・利益率を維持できるかが核心で、会社の長期75%調整後営業利益率を下回る独自基準では割安度が縮む。'},
'6702.T':{
 'method':'Service Solutions内のUvanceと残りのサービスを重複なく分け、ハードウェア・端末と部門間売上消去を加える。Uvance全体をAI売上とは扱わず、企業IT需要とAI導入の弾性を別に置く。本社費用・株式報酬・通常償却を残し、過去の事業売却利益を除く。',
 'risks':['AIによる生産性改善分が人月単価の低下として顧客へ還元される可能性','Uvanceには既存業務からの移行があり、すべてが新規AI需要ではない','海外再編と不採算プロジェクト','前期の非継続事業利益を将来EPSの起点にしない'],
 'key_condition':'AI導入で工数を削減し価値に応じた価格を維持することが必要で、既存業務の置換と値下げで増益効果が相殺されるリスク。'},
'6701.T':{
 'method':'国内ITをBluStellarと既存業務に分け、海外IT・CSG・社会インフラ等を別に計算する。会社の年間見通しはCSGを含まないため、CSG通年売上2000億円を独自の橋渡し仮定として追加する。本社費用と通常の買収償却・株式報酬を控除し、会社Non-GAAP利益をそのままEPSにしない。',
 'risks':['CSG通年寄与と統合費用は独自仮定で、会社の年間見通しは買収後へ未更新','BluStellarには既存業務の移行が含まれ、すべてが新規AI売上ではない','会社Non-GAAP見通しで除外する株式報酬・買収償却を当モデルでは費用に残す','防衛・海底ケーブルの受注循環、案件損失・納期リスク'],
 'key_condition':'BluStellarの単価・生産性改善とCSG統合が成立する必要があり、CSGの独自寄与仮定と買収償却・案件損失で利益が下振れし得る。'},
'DELL':{
 'method':'AIサーバーはFY27会社見通し740億USDを将来校正に用い、従来型ISGとPCは最新四半期を年換算する。AI売上はサーバー工程の市場規模×独自の取り分へ連動させる。AI単独の利益率は非開示のため独自仮定とし、本社費用・株式報酬・買収償却を残す。',
 'risks':['受注残は売上・回収を保証しない。Q2通常FCF0.986bnUSDと調整後8.149bnUSDには顧客金融等の差がある','GPU等の仕入高を含む売上拡大とAI単独の利益率を混同しない','ODMとの競争とNVIDIA標準設計による交渉力の制約','顧客金融・売掛金・在庫の資金需要が買戻し余力を制限する'],
 'key_condition':'受注残の売上化に加えAIサーバーの利益率と代金回収が維持される必要があり、GPU仕入高だけの売上成長と運転資金増が主要リスク。'},
'HPE':{
 'method':'最新四半期のサーバー売上を独自にAI40%・従来型60%へ分け、ストレージ・金融・Juniperを含む通信等を計算する。Cloud&AI部門全体をAIとは扱わず、買収による売上増と有機成長を区別する。株式報酬・無形資産償却等を残し、H3C等の売却益を反復金融利益から除く。',
 'risks':['AIサーバー売上割合は会社非開示で、出荷・検収の時期も変動する','Juniperの統合、負債と買収無形資産の償却負担','通信機器競争とサーバー部材価格','金融債権と顧客の設備資金需要'],
 'key_condition':'Juniperを含む通信部門の採算とAIサーバーの売上化が維持される必要があり、買収負債・無形資産償却と顧客金融が利益・現金の伸びを抑える。'},
'SMCI':{
 'method':'FY27会社売上見通し650〜720億USDの中点を将来校正に使い、AI80%・その他20%へ独自配分する。AI売上はサーバー市場×独自の取り分に連動し、基準ではシェア低下を置く。株式報酬・研究開発・償却を費用に残す。8月31日の監査済み10-Kで通期の売上・利益・営業CFが8月11日速報と一致することを確認した。',
 'risks':['監査済み財務諸表は無限定適正意見だが、IT全般統制の重大な不備が残る。独立輸出調査は完了、政府照会は継続','FY26は黒字でも営業CFが−6.81bnUSD。在庫・売掛金増には外部資金が必要','FY27会社見通し中点は前期比約75%増で、需要・検収・納期の未達リスクが大きい','強制転換優先株・転換社債・株式報酬による希薄化','Q4粗利益率17.5%は顧客・製品構成に左右され、通期の維持を保証しない'],
 'key_condition':'高いFY27会社見通しと回収・利益率の維持が必要で、営業CF赤字による資金調達・転換株式の希薄化、内部統制の重大な不備と政府照会が大きなリスク。'},
'0992.HK':{
 'method':'IDG・ISG・SSGを分け、部門間売上の重複を消去する。ISG年換算340億USDを独自にAI180億・従来型160億へ配分する。ワラント評価損と投資評価益の両方を除き、株式報酬・通常買収償却・研究開発を残す。将来黒字時の転換社債・ワラントを含む経済的希薄化株数を用い、USDのEPSをHKDへ一度だけ換算する。',
 'risks':['Q1会計赤字にはワラント再評価損1.690bnUSDが大きく、実績EPSの単純延長は不適切','評価損益の除外は株式報酬・通常償却の除外を意味しない','ワラント・転換社債の現金決済/株式決済によって経済的希薄化が変わる','薄いハードウェア利益率、在庫・顧客金融。SSGやAI関連売上にはAI PC等も含まれる'],
 'key_condition':'ISGの利益率とサービス成長が維持される必要があり、ワラント評価損益を除いても転換社債・ワラント希薄化と薄利ハードウェアの資金負担が残る。'},
'2382.TW':{
 'method':'2026校正は1〜9月実績売上＋Q4をQ3と同額とする独自仮定。AI65%・従来型サーバー15%・その他20%へ独自配分し、AI売上をサーバー工程の市場規模と取り分に連動させる。製品別割合は会社開示値ではない。株式報酬・通常償却・研究開発を利益率に残す。最新財務・株数は台湾証券取引所の一次APIで確認した。',
 'risks':['AI製品別売上割合65%は独自推定で、会社の監査済みAI部門開示ではない','顧客支給GPU/メモリと売上総額計上の変更により、売上と出荷数量が乖離する','米国生産の立上げ、部品不足、貿易規制','顧客集中、在庫・売掛金の資金需要。現株数4.1076bnを使用し旧EPS分母を流用しない'],
 'key_condition':'AIサーバーの増産を3%台以上の営業利益率で回収できることが必要で、独自AI売上割合・顧客支給部品の計上変更・運転資金が不確実。'},
'6669.TW':{
 'method':'1〜9月実績売上＋Q4をQ3と同額とする独自校正をAI80%・従来型20%へ配分する。4月以降の一部顧客のメモリ代理調達を反映した純額売上を使い、顧客支給部品を総額へ戻さない。Q2のNRE収入による利益率上振れを恒常化せず、株式報酬・償却等を費用に残す。9月権利落の株式配当後株数でEPSを計算する。',
 'risks':['AI80%の売上内訳は独自仮定で、特定顧客・案件への集中がある','代理調達・顧客支給方式で売上総額が減っても出荷量・利益が同率で減るとは限らない','Q2のNRE収入は利益率を押し上げたが、基準のAI営業利益率は6.5%に抑えた','大型設備投資、最大150億TWDの転換社債と15億USD融資による資金・希薄化リスク','株式配当19.827946TWD/旧株、倍率2.9827946を反映。旧Q2EPS80.43を現株価へ直接割らない'],
 'key_condition':'代理調達後の売上でもAI増産を6%台の営業利益率で利益へ変えることが必要で、顧客集中・大型投資と転換社債の希薄化が主要リスク。'},
'2317.TW':{
 'method':'2026校正は1〜9月実績売上＋Q4をQ3と同額とする独自仮定。AI45%・従来型通信等15%・端末等40%へ独自配分し、AIラック/ASIC増産と一般電子機器を分ける。顧客支給型ASICの部材を重複加算せず、株式報酬・償却・研究開発、通常金融費用、税・非支配持分を引いて親会社EPSを算出する。',
 'risks':['AI45%の製品配分は独自仮定で、Cloud&Networkingの全売上をAIとは扱わない','ASICの委託・顧客支給方式では売上総額と利益成長率が一致しない','米国等への生産移転、部品不足、貿易規制','上期営業CF−691億TWD・FCF−1500億TWD。増産に伴う在庫・売掛金と設備投資の資金負担','連結利益から非支配株主分を引く必要がある'],
 'key_condition':'AIラック増産を3〜4%台の営業利益率と回収につなげる必要があり、部材計上方式・生産移転・増産時の資金負担が売上成長の利益化を左右する。'}
}
for c in companies:
 c.update(JA[c['symbol']])

# Point-in-time fully-issued shares, not the fiscal weighted-average EPS denominator.
for c in companies:
 if c['symbol']=='SMCI':
  c['dilution_bridge']={'source_url':S['smci10k'][2],'source_date':'2026-08-31','period_end':'2026-06-30','ordinary_issued_bn':.656882499,'mandatory_preferred_issued_bn':.0043125,'preferred_conversion_rate_min':30.3040,'preferred_conversion_rate_max':36.3640,'preferred_potential_common_min_bn':.130689,'preferred_potential_common_max_bn':.156819750,'existing_CB_all_conversion_common_bn':.073803045,'minimum_total_potential_common_bn':.861374544,'maximum_total_potential_common_bn':.887505294,'forecast_basis':'maximum_total_potential_common_plus_future_SBC_no_cash_settlement_assumption','CB_interest_addback_bn':0,'net_finance_treatment':'既存の各ケース金融費用を全額維持。CB転換利息の税後加戻しを行わない保守的経済EPS。'}
  for r in c['rows']:
   r['share_count_bridge']={'all_existing_potential_common_bn':.887505294,'future_SBC_and_other_dilution_buffer_bn':r['diluted_shares_bn']-.887505294}
   r['CB_interest_addback_bn']=0
   r['net_finance_treatment']='既存金融費用全額を保持し、CB転換による利息節減を加戻さない保守的経済EPS。優先株転換相当の配当は重複控除しない。'
 if c['symbol']=='0992.HK':
  c['dilution_bridge']={'source_url':S['lenovofs'][2],'source_date':'2026-08-13','conversion_terms_effective':'2026-08-08','ordinary_issued_bn':12.404659302,'2029_CB_potential_common_bn':.421385398,'2028_CB_potential_common_bn':1.667342582,'2033_CB_potential_common_bn':.438343592,'warrant_potential_common_bn':1.229930495,'all_existing_potential_common_bn':16.161661369,'economic_basis_note':'2033CBは通常2032年まで転換不可だが、経済EPSでは潜在株に含める保守的仮定。現金決済の資金手当・発行代金による買戻しは仮定しない。'}
  for r in c['rows']:
   r['share_count_bridge']={'all_existing_potential_common_bn':16.161661369,'future_SBC_and_other_dilution_buffer_bn':r['diluted_shares_bn']-16.161661369}

# Recompute every row independently and test dimensions, completeness and shared capture budget.
assert len(companies)==14
for c in companies:
 assert len(c['rows'])==6
 assert {(r['year'],r['case']) for r in c['rows']}=={(y,k) for y in YEARS for k in CASES}
 for r in c['rows']:
  rv=sum(x['market_or_revenue_anchor_bn']*x['growth_factor']*x['share_factor'] for x in r['segments'])
  op=sum(x['revenue_bn']*x['operating_margin'] for x in r['segments'])-r['unallocated_cost_bn']
  ni=op+r['net_finance_bn']-max(op+r['net_finance_bn'],0)*r['tax_rate']-r['minority_bn']
  assert math.isclose(rv,r['revenue_bn'],rel_tol=1e-10)
  assert math.isclose(op,r['operating_income_bn'],rel_tol=1e-10)
  assert math.isclose(ni,r['normal_net_income_bn'],rel_tol=1e-10)
  assert math.isclose(ni/r['diluted_shares_bn']*r['fx_quote_per_financial_currency'],r['eps_quote_currency'],rel_tol=1e-10)
  assert r['diluted_shares_bn']>0 and all(math.isfinite(r[k]) for k in ['eps_quote_currency','revenue_bn','operating_income_bn','normal_net_income_bn'])
checks=[]
prior={2028:[.78,.93,.93],2029:[.76,.88,.90]}
for r in companies[0]['rows']:
 i=CASES.index(r['case']);a=r['segments'][0]['share_factor'];s=prior[r['year']][i]+a
 checks.append({'year':r['year'],'case':r['case'],'NVDA_AVGO_capture_from_existing_model':prior[r['year']][i],'AMD_capture':a,'total_capture':s,'other_vendor_residual':1-s,'passes':s<=1});assert s<=1
out={'as_of':'2026-10-18','generated_by':'inputs/compute.py','money_unit':'billion of financial_currency','shares_unit':'billion','forecast_basis':'CY2028/CY2029 full-year-equivalent independent scenario, not strict fiscal-quarter roll-up','all_future_values_status':'independent_scenario_NOT_company_guidance_or_consensus','common_macro_USD_bn':{str(y):dict(zip(CASES,MACRO[y])) for y in YEARS},'fx_fixed_2026_10_16':FX,'common_server_storage_pool_USD_bn':{str(y):dict(zip(CASES,SERVER[y])) for y in SERVER},'memory_scenario_parameters':{'NAND_reference_Q2_annualized_market_USD_bn':NAND0,'NAND_bit_CAGR':dict(zip(CASES,NAND_BITS)),'NAND_ASP_index':{str(y):dict(zip(CASES,NAND_ASP[y])) for y in YEARS},'nonHBM_DRAM_bit_CAGR':dict(zip(CASES,DRAM_BITS)),'nonHBM_DRAM_ASP_index':{str(y):dict(zip(CASES,DRAM_ASP[y])) for y in YEARS},'HBM_bit_CAGR':dict(zip(CASES,HBM_BITS)),'HBM_ASP_index':{str(y):dict(zip(CASES,HBM_ASP[y])) for y in YEARS},'status':'ALL independent scenario assumptions; HBM/nonHBM split not issuer disclosure'},'double_count_warning':'AI final-demand capex is not the sum of chip + memory + OEM + ODM revenue. Shared pool capture is only enforced for directly substitutable AMD+NVDA+AVGO electronic capture; OEM and ODM gross sales not additive. Memory bit/ASP includes nonAI markets.', 'capture_checks':checks,'companies':companies,'source_register':{k:{'date':v[0],'type':v[1],'url':v[2]} for k,v in S.items()},'checks':{'companies':len(companies),'rows':sum(len(c['rows']) for c in companies),'all_math_recomputed':True,'no_prices_used_to_fit_scenarios':True}}
OUT.with_suffix('.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
lines=['# AI46社拡張：担当14社の2028/29年EPS試算（2026-10-18）','','全84ケースは独自の将来シナリオ。会社予想・市場予想ではない。金額・株数はそれぞれ財務通貨の十億単位・十億株、EPSは現地普通株1株。LenovoだけUSD利益を固定USDHKD7.84719992で一度HKDへ換算する。株価を使って利益を逆算・調整していない。','','`python3 research/themes/ai-valuation-ranking/2026-10-18/inputs/compute.py` でJSONと本メモを再生成できる。','','## 主要結果（EPS、弱気／基準／強気）','','|企業|通貨|2028弱|基準|強|2029弱|基準|強|モデル確度|','|---|---|---:|---:|---:|---:|---:|---:|---|']
for c in companies:
 vals=[r['eps_quote_currency'] for r in c['rows']]
 lines.append('|'+c['name']+'|'+c['quote_currency']+'|'+'|'.join(f'{v:,.2f}' for v in vals)+'|'+c['model_quality']+'|')
lines+=['','## 読み方・共通の限界','','- 2028/29は暦年相当の通年利益水準。厳密な決算期積上げではない。基準ケースに確率は付けない。','- AI支出2028=1.0/1.4/1.9兆USD、2029=0.95/1.7/2.5兆USD。サーバー/ストレージ工程の売上機会は独自に2028=500/800/1150bnUSD、2029=475/1050/1600bnUSD。ODM売上とOEM売上、GPU/メモリ売上は費用を内包するため合計しない。','- メモリのNAND数量・ASPは既存キオクシアと同じ経路。DRAM/HBMは別の数量・単価を置く。HBMが汎用DRAMより高収益だと固定しない。2026の汎用DRAM価格急騰はHBMの利益率を超えるため、HBM比率上昇だけで利益率改善とは限らない。','- メモリの基準2028/29にはASP調整を置き、MU等の「2027/28供給不足」という会社見通しを全面延長していない。基準でも高収益が残る仮定で、循環中立利益と同義ではない。','- HBM/汎用DRAM/NANDの製品別費用は未開示のため独自配賦。Korean現地通貨アンカーとUSD市場推計には平均為替・期間の差がある。将来の量/ASP指数を比較するための校正値で、将来の金額シェアと混同しない。','- SBC、通常償却、研究開発費を費用に残す。金融資産評価益、持分売却益、ワラント評価損益、例外税便益を反復利益へ延長しない。既存保有資産価値はゼロとみなすわけではなく、利益倍率とは別評価。','- capexと運転資金はEPSから重複控除せず、費用に残す償却と資金負担の注意を分けて保存した。MU等の顧客前受金は将来返済義務があり恒久的余剰資金ではない。','- PE仮定は独自の事前設定。将来EPS×仮定PEの価格条件は実績PER/会社予想PERやDCFではない。','','## 企業別の根拠と仮定']
for c in companies:
 lines+=['',f"### {c['name']}（{c['symbol']}）",'',c['method'],'',f"株数・通貨：{c['share_basis']}",'',f"仮定終点PER（弱/基準/強）：{c['terminal_pe']['weak']}/{c['terminal_pe']['base']}/{c['terminal_pe']['strong']}倍。",'','一次アンカー（実績/会社予想は各scope/typeで区別）：']
 for f in c['anchor_facts']:
  lines.append(f"- [{f['date']} {f['scope']}]({f['url']})：`{json.dumps(f['values'],ensure_ascii=False,separators=(',',':'))}`")
 lines+=['','成立条件：'+c['key_condition'],'','反証・監視点：'+'／'.join(c['risks'])]
OUT.with_suffix('.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(out['checks'],ensure_ascii=False))
for c in companies:
 print(c['symbol'],c['quote_currency'],[round(r['eps_quote_currency'],2) for r in c['rows']])
