// 調査日2026-10-05。USD、Billion USD。2020/2022株式分割後。
// 株価：10/2通常終値。財務：Q2/2026 SEC 10-Qと7/22決算8-K添付。
// EPSは公表済み四半期の丸め値を合計。将来シナリオは会社予想ではない。
const price = 370.59;
const legalShares = 3_949_547_394 / 1e9; // 7/16、CEO条件付き制限株を含む法定発行済
const assumedDilutedShares = 3.540; // Q2希薄化加重平均。将来を固定する独自仮定
const quarters = [
  {period:'2025Q3', revenue:28.095, net:1.373, eps:.39, nonGaapNet:1.770, nonGaapEps:.50, cfo:6.238, capex:2.248},
  {period:'2025Q4', revenue:24.901, net:.840, eps:.24, nonGaapNet:1.761, nonGaapEps:.50, cfo:3.813, capex:2.393},
  {period:'2026Q1', revenue:22.387, net:.477, eps:.13, nonGaapNet:1.453, nonGaapEps:.41, cfo:3.937, capex:2.493},
  {period:'2026Q2', revenue:28.236, net:1.114, eps:.32, nonGaapNet:1.153, nonGaapEps:.33, cfo:4.697, capex:5.789},
];
const sum = key => quarters.reduce((n,q)=>n+q[key],0);
const ttm = Object.fromEntries(['revenue','net','eps','nonGaapNet','nonGaapEps','cfo','capex'].map(key=>[key,sum(key)]));
ttm.fcf = ttm.cfo - ttm.capex;
const targetPrice = price * 1.1 ** 5;
const requiredEps = targetPrice / 50;
const grossLegalValue = price * legalShares;
const round = n => +n.toFixed(6);
const output = {
  assumptions: {priceUsd:price, legalSharesBillion:legalShares, assumedFutureDilutedSharesBillion:assumedDilutedShares,
    note:'法定株数ベース価値は条件付株を含む参考。35.40億株は将来固定の仮定。両者を同じ株数と扱わない。'},
  ttm: Object.fromEntries(Object.entries(ttm).map(([k,v])=>[k,round(v)])),
  multiples: {priceOverTtmGaapEps:round(price/ttm.eps),priceOverTtmNonGaapEps:round(price/ttm.nonGaapEps),
    grossLegalSharesValueBillion:round(grossLegalValue),grossLegalSharesValueOverTtmRevenue:round(grossLegalValue/ttm.revenue)},
  q2: {operatingMarginPct:round(.398/28.236*100), automotiveGrossMarginPct:round((20.516-17.053)/20.516*100),
    automotiveGrossMarginExCreditsPct:round((20.516-.146-17.053)/(20.516-.146)*100),
    energyGrossMarginPct:round(.640/3.139*100), servicesGrossMarginPct:round(.648/4.581*100),
    nonGaapBridge:round(1.114+.989+.087-.763-.274), netLessOnlySpaceXGainAndCertainTax:round(1.114-.763-.274),
    h1Cfo:8.634,h1Capex:8.282,h1Fcf:round(8.634-8.282), q2Fcf:round(4.697-5.789),
    spaceXInvestment:2.002,h1FcfLessSpaceXInvestment:round(8.634-8.282-2.002),
    cashAndShortInvestments:43.524,debtAndFinanceLeaseCarryingValue:round(1.418+7.924)},
  q3: {deliveries:486532,production:464391,storageGwh:13.7,deliveryYoYPct:round((486532/497099-1)*100),
    deliveryQoQPct:round((486532/480126-1)*100),productionDeliveryGap:464391-486532,
    storageYoYPct:round((13.7/12.5-1)*100),storageQoQPct:round((13.7/13.5-1)*100),
    ytdDeliveries:358023+480126+486532,ytdStorageGwh:round(8.8+13.5+13.7)},
  unchangedPriceRequirements:[30,40,50].map(pe=>({pe,requiredEpsUsd:round(price/pe),
    netBillionAtAssumedShares:round(price/pe*assumedDilutedShares),
    revenueAt15PctNetMargin:round(price/pe*assumedDilutedShares/.15),
    revenueAt20PctNetMargin:round(price/pe*assumedDilutedShares/.20)})),
  fiveYearTenPercentReturnAtPe50: {priceUsd:round(targetPrice),epsUsd:round(requiredEps),
    netBillionAtAssumedShares:round(requiredEps*assumedDilutedShares),
    revenueBillionAt20PctNetMargin:round(requiredEps*assumedDilutedShares/.20),
    netBillionIfSharesGrow10Pct:round(requiredEps*assumedDilutedShares*1.1)},
  priceStressAtUnchangedTtmEps:[100,150,200].map(pe=>({pe,priceUsd:round(pe*ttm.eps)})),
};
console.log(JSON.stringify(output,null,2));
