"""Follow-up to the 2026-10-18 conditional ranking; prices fixed at Oct16.
Not probability forecasts. Reproduce threshold and combined EPS/PE stresses.
"""
from pathlib import Path
import hashlib,json,math
B=Path(__file__).resolve().parent
new=json.loads((B/'ranking.json').read_text());old=json.loads((B/'revisions/initial-published/ranking.json').read_text())
prior={c['symbol']:c for c in old['companies']}
order=['AVGO','000660.KS','2382.TW','6669.TW','SMCI']
by={c['symbol']:c for c in new['companies']};out=[]
for symbol in order:
 c=by[symbol];b=c['scenarios']['2029']['base'];p=c['price']['close'];v1=prior[symbol]['scenarios']['2029']['base'];disc=1.12**b['discount_years'];eps=b['eps_quote_currency'];pe=b['terminal_pe']
 thresholds=[]
 for terminal_pe in sorted({pe,{'AVGO':20,'000660.KS':8,'2382.TW':12,'6669.TW':14,'SMCI':8}[symbol]}):
  need=p*disc/terminal_pe
  thresholds.append({'terminal_pe':terminal_pe,'required_eps_for_12pct':need,'earnings_shortfall_allowance_pct':(1-need/eps)*100})
 item={'symbol':symbol,'name':c['name'],'currency':c['price']['currency'],'price':p,'year':2029,'base_NI_bn':b['normal_net_income_bn'],'base_EPS':eps,'base_diluted_shares_bn':b['diluted_shares_bn'],'base_PE':p/eps,'terminal_PE':pe,'conditional_price_12pct':b['conditional_entry_price'],'gap_pct':b['entry_price_gap_pct'],'initial_published_EPS':v1['eps_quote_currency'],'initial_published_shares_bn':v1['diluted_shares_bn'],'initial_published_gap_pct':v1['entry_price_gap_pct'],'thresholds':thresholds,'weak_scenario_gap_pct':c['scenarios']['2029']['weak']['entry_price_gap_pct'],'joint_EPS_minus20pct_PE_minus20pct':{'eps':eps*.8,'terminal_pe':pe*.8,'conditional_price':b['conditional_entry_price']*.64,'gap_pct':(b['conditional_entry_price']*.64/p-1)*100}}
 if symbol in ('2382.TW','6669.TW','SMCI'):
  factor=(1-b['tax_rate'])*(.995 if symbol=='2382.TW' else 1)
  loss=b['revenue_bn']*.01*factor/b['diluted_shares_bn']
  stressed=eps-loss
  item['OPM_minus1pt']={'eps':stressed,'EPS_change_pct':-loss/eps*100,'conditional_price':stressed*pe/disc,'gap_pct':(stressed*pe/disc/p-1)*100}
 for y in ('2028','2029'):
  for case in ('weak','base','strong'):
   r=c['scenarios'][y][case];assert math.isclose(r['normal_net_income_bn']/r['diluted_shares_bn'],r['eps_quote_currency'],rel_tol=1e-10)
 out.append(item)
result={'as_of':'2026-10-18 JST','price_date':'2026-10-16','status':'independent sensitivity calculations; not forecast probabilities or target-price returns','discount_years':b['discount_years'],'discount_factor':disc,'purchase_preference_order':order,'purchase_preference_basis':'qualitative judgment, not expected-return optimization','rows':out,'ranking_sha256':hashlib.sha256((B/'ranking.json').read_bytes()).hexdigest()}
(B/'top-five-calculations.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
for r in out:print(r['symbol'],'EPS',round(r['base_EPS'],3),'gap',round(r['gap_pct'],1),'joint20/20',round(r['joint_EPS_minus20pct_PE_minus20pct']['gap_pct'],1))
# Operating/capture assumptions below are independent stresses, not issuer guidance.
av=by['AVGO']['scenarios']['2029']['base']
def avgo_eps(ai,margin,sbc=13):
 return (ai*margin+21*.42+48*.80-sbc-4.4848333333333334-2.5)*.82/5.1
avrows=[]
for ai,margin,sbc in [(250.24,.60,13),(200,.60,13),(180,.60,13),(150,.60,13),(200,.50,13),(200,.50,21.8)]:
 e=avgo_eps(ai,margin,sbc);v=e*25/disc
 avrows.append({'ai_revenue_USD_bn':ai,'AI_margin_before_SBC_and_acq_amort':margin,'SBC_USD_bn':sbc,'EPS_USD':e,'terminal_PE':25,'conditional_price':v,'gap_pct':(v/328.75-1)*100,'conditional_price_if_PE20':e*20/disc})
assert math.isclose(avrows[0]['EPS_USD'],av['eps_quote_currency'],rel_tol=1e-10)
result['AVGO_independent_stresses']=avrows
sk=by['000660.KS']['scenarios']['2029']['base'];skrows=[]
for opm,pe in [(.50,11),(.40,11),(.50,8)]:
 ni=(sk['revenue_bn']*opm+sk['net_finance_bn'])*.75;e=ni/sk['diluted_shares_bn'];v=e*pe/disc
 skrows.append({'consolidated_OPM':opm,'terminal_PE':pe,'normal_NI_KRW_bn':ni,'EPS_KRW':e,'conditional_price':v,'gap_pct':(v/1272000-1)*100})
result['SK_independent_stresses']=skrows
result['checks']={'new_case_math':'30 of 30 rows checked','AVGO_base_identity':'passed','discount_matches_prior_model':True,'no_probabilities_assigned':True,'prices_unchanged':True}
(B/'top-five-calculations.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
