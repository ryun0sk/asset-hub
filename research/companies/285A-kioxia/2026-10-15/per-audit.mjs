// Low-PER research audit, 2026-10-15 evening JST. All Kioxia prices/EPS post split.
// Calculations use published data and explicitly labelled hypothetical sensitivities.
import assert from 'node:assert/strict';

const shares = (548639034 - 16134027) * 3; // 2026-08-31, ex treasury, split-adjusted.
const facts = {
  closeJpy: 12880, closeDate: '2026-10-15', hypotheticalPurchasePriceJpy: 12000,
  sharesExTreasury: shares, sharesDate: '2026-08-31',
  ifisConsensusNetIncomeTrn: 5.648790, ifisConsensusAsOf: '2026-10-14',
  providerEPS: { currentFYMarch2027: 3443, followingFYMarch2028: 4834.4, oneYearAhead: 4197.8,
    source: 'https://scouter.monex.co.jp/report/theoryDps/285A', displayedAsOf: '2026-10-15 19:20 JST' },
  ifisConsensusRevenueTrn: 10.209959, ifisConsensusOperatingProfitTrn: 8.077118,
  q1IFRS: { revenueTrn: 1.767117, operatingProfitTrn: 1.270017, netIncomeTrn: 0.842165 },
  q2IFRSGuidance: { revenueTrn: 2.39, operatingProfitTrn: 1.89, pretaxProfitTrn: 1.87, netIncomeTrn: 1.27 },
  // Diluted EPS published before the 3-for-1 split. TTM constructed by annual + latest Q1 - prior Q1.
  dilutedEPSPreSplit: { fyMarch2026: 1009.15, q1June2026: 1525.09, q1June2025: 33.75 },
  q1CashMillionJpy: { operatingCashFlow: 866337, purchasePPE: 51176, purchaseIntangibles: 1226,
    proceedsSalePPE: 1217, governmentGrants: 12026, leasePrincipal: 7929,
    strategicNanyaInvestment: 78220, otherInvestingInflow: 61, netInvestingCashFlow: -117318,
    incomeTaxExpense: 392549, incomeTaxPaid: 100533, receivablesCashOutflow: 472052 },
};
const derivedIndependentEPS = facts.ifisConsensusNetIncomeTrn * 1e12 / shares;
const dilutedTTMEPS = (1009.15 + 1525.09 - 33.75) / 3;
const prices = [12000, 12880];
const epsComparisons = [
  { label: 'TTM diluted EPS (constructed from published annual and Q1 EPS)', epsJpy: dilutedTTMEPS },
  { label: 'FY March 2027 provider consensus EPS', epsJpy: facts.providerEPS.currentFYMarch2027 },
  { label: 'FY March 2027 net income divided by latest known ex-treasury shares (independent approximation)', epsJpy: derivedIndependentEPS },
  { label: 'FY March 2028 provider consensus EPS', epsJpy: facts.providerEPS.followingFYMarch2028 },
].map(row => ({ ...row, perAt12000: 12000 / row.epsJpy, perAt12880: 12880 / row.epsJpy }));
const c = facts.q1CashMillionJpy;
const q1CoreFCFMillion = c.operatingCashFlow - c.purchasePPE - c.purchaseIntangibles + c.proceedsSalePPE + c.governmentGrants;
const q1AfterLeaseMillion = q1CoreFCFMillion - c.leasePrincipal;
const h2RevenueTrn = facts.ifisConsensusRevenueTrn - facts.q1IFRS.revenueTrn - facts.q2IFRSGuidance.revenueTrn;
const h2OperatingProfitTrn = facts.ifisConsensusOperatingProfitTrn - facts.q1IFRS.operatingProfitTrn - facts.q2IFRSGuidance.operatingProfitTrn;
const h2NetIncomeTrn = facts.ifisConsensusNetIncomeTrn - facts.q1IFRS.netIncomeTrn - facts.q2IFRSGuidance.netIncomeTrn;
// Follow-up captured after 22:26 JST. Earlier inputs above remain the 19:20 snapshot.
// All following statement amounts are million JPY; EPS is split-adjusted JPY.
const priorFY = { revenue: 2337628, operatingProfit: 870369, netIncome: 554490,
  basicEPSPreSplit: 1024.07, dilutedEPSPreSplit: 1009.15, averageSharesPreSplit: 541455417 };
const priorCumulative = [
  { end: '2025-06-30', revenue: 342799, operatingProfit: 44899, netIncome: 18284 },
  { end: '2025-09-30', revenue: 791145, operatingProfit: 130820, netIncome: 58946 },
  { end: '2025-12-31', revenue: 1334776, operatingProfit: 273574, netIncome: 146756 },
  { end: '2026-03-31', revenue: 2337628, operatingProfit: 870369, netIncome: 554490 },
];
const priorQuarters = priorCumulative.map((row, i) => ({
  end: row.end,
  revenue: row.revenue - (priorCumulative[i - 1]?.revenue ?? 0),
  operatingProfit: row.operatingProfit - (priorCumulative[i - 1]?.operatingProfit ?? 0),
  netIncome: row.netIncome - (priorCumulative[i - 1]?.netIncome ?? 0),
}));
const latestQ1 = { revenue: 1767117, operatingProfit: 1270017, netIncome: 842165,
  basicEPSPreSplit: 1539.91, dilutedEPSPreSplit: 1525.09, averageSharesPreSplit: 546890636 };
const latestIfis = { consensusDate: '2026-10-15', revenue: 10077737,
  operatingProfit: 7911895, pretaxProfit: 8046647, netIncome: 5557290,
  source: 'https://kabuyoho.jp/sp/reportAnalyst?bcode=285A' };
const q2Company = { revenue: 2390000, operatingProfit: 1890000, netIncome: 1270000 };
const inferredCurrentEPS = 3443 * latestIfis.netIncome / 5648790;
const currentH2 = Object.fromEntries(['revenue', 'operatingProfit', 'netIncome'].map(key =>
  [key, latestIfis[key] - latestQ1[key] - q2Company[key]]));
const perGapFollowup = {
  capturedAt: '2026-10-15 after 22:26 JST', fixedSharePriceJpy: 12880,
  priceBasis: '2026-10-15 Tokyo close; not a fresh night-session quote',
  units: 'Statement amounts: million JPY. EPS: JPY after 3-for-1 split.',
  priorFY, priorCumulative, priorQuarters, latestQ1, q2Company, latestIfis,
  statementBasedEPS: {
    priorAnnualBasic: priorFY.basicEPSPreSplit / 3,
    priorAnnualBasicPER: 12880 / (priorFY.basicEPSPreSplit / 3),
    q1AnnualizedBasic: latestQ1.basicEPSPreSplit / 3 * 4,
    q1AnnualizedBasicPER: 12880 / (latestQ1.basicEPSPreSplit / 3 * 4),
    q1AnnualizedDiluted: latestQ1.dilutedEPSPreSplit / 3 * 4,
    note: 'Annualization is a constant-quarter hypothetical, not company full-year guidance. Published EPS uses each period average shares; do not sum quarterly EPS as exact annual EPS.',
  },
  profitBridge: {
    priorAverageQuarterNI: priorFY.netIncome / 4,
    latestQ1VsPriorAverage: latestQ1.netIncome / (priorFY.netIncome / 4),
    forecastVsLatestQ1Annualized: latestIfis.netIncome / (latestQ1.netIncome * 4),
    forecastVsPriorFY: latestIfis.netIncome / priorFY.netIncome,
    priorQ4ShareOfAnnualProfit: priorQuarters[3].netIncome / priorFY.netIncome,
  },
  currentH2: { ...currentH2, averageQuarterNI: currentH2.netIncome / 2,
    averageQuarterVsQ2Company: currentH2.netIncome / 2 / q2Company.netIncome - 1,
    operatingMargin: currentH2.operatingProfit / currentH2.revenue,
    netMargin: currentH2.netIncome / currentH2.revenue },
  forecastDataTiming: {
    earlierIfisNetIncome: 5648790, latestVsEarlier: latestIfis.netIncome / 5648790 - 1,
    monexDisplayedEPS: 3443, monexDisplayedTime: '2026-10-15 19:20:27 JST',
    inferredCurrentEPS, inferredCurrentPER: 12880 / inferredCurrentEPS,
    inferenceBasis: 'Independent approximation: update net income only, preserve denominator implicit in earlier EPS. Not a newly published IFIS EPS.',
    minkabu: { date: '2026-10-15', revenue: 10130625, netIncome: 5617829,
      publishedEPS: 3515.58, calculatedPER: 12880 / 3515.58,
      source: 'https://minkabu.jp/stock/285A/analyst_consensus' },
  },
  q4ToQ1OperatingBridge: {
    revenueIncrease: latestQ1.revenue - priorQuarters[3].revenue,
    operatingProfitIncrease: latestQ1.operatingProfit - priorQuarters[3].operatingProfit,
    netOperatingCostsIncrease: (latestQ1.revenue - latestQ1.operatingProfit)
      - (priorQuarters[3].revenue - priorQuarters[3].operatingProfit),
    roundedCOGSBillions: { q4: 359.9, q1: 387.1 },
    roundedDABillions: { q4: 76.4, q1: 76.1 },
    note: 'Rounded COGS and D&A are published IFRS deck figures. Incremental revenue is not pure price contribution; volume, FX, mix and costs also change.',
  },
};
for (const key of ['revenue', 'operatingProfit', 'netIncome']) {
  assert.equal(priorQuarters.reduce((sum, row) => sum + row[key], 0), priorFY[key]);
}
assert(Math.abs(priorFY.netIncome * 1e6 / (priorFY.averageSharesPreSplit * 3)
  - perGapFollowup.statementBasedEPS.priorAnnualBasic) < .01);
assert(Math.abs(latestQ1.netIncome * 1e6 / (latestQ1.averageSharesPreSplit * 3)
  - latestQ1.basicEPSPreSplit / 3) < .01);
assert.equal(currentH2.netIncome, 3445125);
assert(Math.abs(perGapFollowup.profitBridge.latestQ1VsPriorAverage *
  perGapFollowup.profitBridge.forecastVsLatestQ1Annualized -
  perGapFollowup.profitBridge.forecastVsPriorFY) < 1e-10);
const peerInputs = [
  { name: 'Kioxia', price: 12880, currency: 'JPY', priceAsOf: '2026-10-15 15:30 JST', eps: 3443, period: 'FY ending 2027-03-31', basis: 'IFRS-related consensus', source: 'https://scouter.monex.co.jp/report/theoryDps/285A' },
  { name: 'Micron', price: 914.13, currency: 'USD', priceAsOf: '2026-10-14 16:00:01 EDT', eps: 176.15, period: 'FY ending 2027-09-02', basis: 'adjusted/non-GAAP forecast, prior-year basis reconciled', source: 'https://finance.yahoo.com/quote/MU/analysis/' },
  { name: 'Sandisk', price: 1403.34, currency: 'USD', priceAsOf: '2026-10-14 15:59 EDT (late-session, not exact close)', eps: 214.82, period: 'FY ending 2027-07-02', basis: 'adjusted/non-GAAP forecast, prior-year basis reconciled', source: 'https://twelvedata.com/markets/542904/stock/nasdaq/sndk/analysis' },
  { name: 'SK hynix', price: 1262000, currency: 'KRW', priceAsOf: '2026-10-15 15:30 KST', eps: 355218.90, period: 'FY ending 2026-12-31', basis: 'adjusted/non-GAAP forecast (S&P Global)', source: 'https://stockanalysis.com/quote/krx/000660/forecast/' },
  { name: 'Samsung', price: 210000, currency: 'KRW', priceAsOf: '2026-10-15 15:30 KST', eps: 47826.95, period: 'FY ending 2026-12-31', basis: 'adjusted/non-GAAP forecast (S&P Global)', source: 'https://stockanalysis.com/quote/krx/005930/forecast/' },
];
const reverseEarnings = prices.flatMap(price => [8, 10, 12].map(multiple => {
  const netIncomeTrn = price * shares / 1e12 / multiple;
  return { priceJpy: price, assumedNormalizedPER: multiple, requiredNetIncomeTrn: netIncomeTrn,
    declineFromConsensus: 1 - netIncomeTrn / facts.ifisConsensusNetIncomeTrn };
}));
const aspStress = [0, -0.3, -0.4, -0.5, -0.6, -0.7].map(change => {
  // Mechanical only: volume, mix, FX, total costs and effective tax rate are fixed.
  const revenueTrn = 2.39 * 4 * (1 + change);
  const pretaxTrn = revenueTrn - (2.39 - 1.89) * 4 - (1.89 - 1.87) * 4;
  const netIncomeTrn = pretaxTrn * (1.27 / 1.87);
  return { change, revenueTrn, netIncomeTrn, perAt12000: 12000 * shares / 1e12 / netIncomeTrn };
});
const explicitCF = [5, 4, 3];
const r = 0.13;
const nearPVTrn = explicitCF.reduce((sum, cf, i) => sum + cf / (1 + r) ** (i + 1), 0);
const result = {
  asOf: '2026-10-15 evening JST', facts, derivedIndependentEPS, epsComparisons, perGapFollowup,
  providerVsIndependentEPSDifference: derivedIndependentEPS / facts.providerEPS.currentFYMarch2027 - 1,
  followingYearEPSGrowth: 4834.4 / 3443 - 1,
  cashAudit: { q1CoreFCFMillion, q1AfterLeaseMillion,
    q1FullInvestingAndLeaseAfterOperatingMillion: c.operatingCashFlow + c.netInvestingCashFlow - c.leasePrincipal,
    q1AfterLeaseToNetIncome: q1AfterLeaseMillion / 842165,
    annualizedQ1AfterLeaseTrn: q1AfterLeaseMillion * 4 / 1e6,
    note: 'Core FCF excludes strategic Nanya investment. Cash-flow amounts are before debt principal repayment and buybacks, not ending cash or fully distributable cash. Annualized Q1 is not a forecast; tax timing, receivables and CAPEX differ across quarters.' },
  impliedSecondHalf: { h2RevenueTrn, h2OperatingProfitTrn, h2NetIncomeTrn,
    operatingMargin: h2OperatingProfitTrn / h2RevenueTrn, netMargin: h2NetIncomeTrn / h2RevenueTrn,
    averageQuarterlyNetIncomeVsQ2: h2NetIncomeTrn / 2 / 1.27 - 1 },
  mechanicalAnnualizations: [facts.q1IFRS.netIncomeTrn * 4, 1.27 * 4].map(netIncomeTrn => ({ netIncomeTrn, perAt12000: 12000 * shares / 1e12 / netIncomeTrn })),
  peers: peerInputs.map(p => ({ ...p, per: p.price / p.eps })),
  reverseEarnings, aspStress,
  reverseDCF: prices.map(priceJpy => ({ priceJpy, requiredLongTermAnnualEquityCFTrn: (priceJpy * shares / 1e12 - nearPVTrn) * (1 + r) ** 3 * r,
    assumptions: 'Independent scenario: first 3 years CF [5,4,3] trillion JPY; required equity return 13%; zero growth. Not a market-implied probability.' })),
  illustrativeNormalizedCashBridgeTrn: { netIncome: 3.2, depreciation: 0.30, capex: -0.47, leasePrincipal: -0.03, workingCapitalChange: 0, equityCashFlow: 3 },
  historyExample: { company: 'Micron', priceDate: '2018-09-21', priceUsd: 44.74, fy2018GaapEPSUsd: 11.51,
    trailingPER: 44.74 / 11.51, fy2019GaapEPSUsd: 5.51, epsDecline: 1 - 5.51 / 11.51,
    note: 'Historical trailing PER; not directly comparable with current forward PER. Not a forecast of the present cycle.' },
};
assert.equal(shares, 1597515021);
assert.equal(q1AfterLeaseMillion, 819249);
assert(Math.abs(result.epsComparisons[1].perAt12000 - 3.485332558814987) < 1e-10);
assert(Math.abs(result.impliedSecondHalf.operatingMargin - 0.812) < .001);
assert(result.aspStress.every((s, i, arr) => i === 0 || s.netIncomeTrn < arr[i - 1].netIncomeTrn));
console.log(JSON.stringify(result, null, 2));
