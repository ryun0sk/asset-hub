// JPY trillions except shares, EPS and share price. Independent scenarios, not guidance.
// Run offline with Node.js; writes only to stdout.
const source = {
  financials: 'https://ssl4.eir-parts.net/doc/285A/tdnet/2902676/00.pdf',
  presentation: 'https://ssl4.eir-parts.net/doc/285A/ir_material_for_fiscal_ym3/216828/00.pdf',
  qa: 'https://ssl4.eir-parts.net/doc/285A/ir_material_for_fiscal_ym3/216830/00.pdf',
  published: '2026-10-30',
};
const facts = {
  actualH1ParentNetIncomeTrn: 2.197871,
  q3CompanyGuidanceTrn: { revenue: 2.5, operatingProfit: 1.995, pretaxProfit: 1.98, parentNetIncome: 1.36 },
  q3CompanyGuidanceFxJpyPerUsd: 157,
  sharesExTreasury: 1597905534,
  shareBasis: 'post 3-for-1 split effective 2026-10-01; shares as of 2026-09-30',
  referencePriceJpy: 8700,
  referencePriceKind: 'rounded price in user question, not a fresh market observation',
};
const q3 = facts.q3CompanyGuidanceTrn;
const baseline = {
  annualRevenueTrn: q3.revenue * 4,
  annualOperatingExpenseTrn: (q3.revenue - q3.operatingProfit) * 4,
  annualNetNonOperatingExpenseTrn: (q3.operatingProfit - q3.pretaxProfit) * 4,
  afterTaxFactor: q3.parentNetIncome / q3.pretaxProfit,
  annualizedParentNetIncomeTrn: q3.parentNetIncome * 4,
  kind: 'mechanical annualization of one quarter of company guidance, not full-year guidance',
};
function simulate({ name, priceFactor, volumeFactor, operatingExpenseFactor, kind }) {
  const revenueTrn = baseline.annualRevenueTrn * priceFactor * volumeFactor;
  const operatingExpenseTrn = baseline.annualOperatingExpenseTrn * operatingExpenseFactor;
  const operatingProfitTrn = revenueTrn - operatingExpenseTrn;
  const pretaxProfitTrn = operatingProfitTrn - baseline.annualNetNonOperatingExpenseTrn;
  const parentNetIncomeTrn = pretaxProfitTrn * baseline.afterTaxFactor;
  const epsJpy = parentNetIncomeTrn * 1e12 / facts.sharesExTreasury;
  return { name, kind, priceFactor, volumeFactor, operatingExpenseFactor, revenueTrn,
    operatingExpenseTrn, operatingProfitTrn, pretaxProfitTrn, parentNetIncomeTrn,
    epsJpy, referencePER: facts.referencePriceJpy / epsJpy };
}
const nineMonthsActualPlusGuidanceTrn = facts.actualH1ParentNetIncomeTrn + q3.parentNetIncome;
const fy2027 = [1.36, 1.45, 1.65, 1.8].map(q4NetIncomeTrn => ({
  q4NetIncomeTrn,
  kind: q4NetIncomeTrn === 1.36 ? 'Q4 equal to Q3 guidance: independent carry-forward' : 'independent Q4 assumption',
  fullYearParentNetIncomeTrn: nineMonthsActualPlusGuidanceTrn + q4NetIncomeTrn,
}));
const fy2028 = [
  { name: 'lower_central_example', priceFactor: 0.85, volumeFactor: 1.15, operatingExpenseFactor: 1.2 },
  { name: 'central_example', priceFactor: 0.95, volumeFactor: 1.15, operatingExpenseFactor: 1.2 },
  { name: 'upper_central_example', priceFactor: 1, volumeFactor: 1.2, operatingExpenseFactor: 1.2 },
].map(s => simulate({ ...s, kind: 'independent FY2028 scenario, not a confidence interval' }));
const normalized = [0.7, 0.6, 0.5].map(priceFactor => simulate({
  name: `normalization_price_${priceFactor}`,
  kind: 'independent long-run valuation assumption; date of normalization unspecified',
  priceFactor, volumeFactor: 1.2, operatingExpenseFactor: 1.5,
}));
const priceOnlySensitivity = [1, 0.8, 0.7, 0.6, 0.5].map(priceFactor => simulate({
  name: `price_only_${priceFactor}`, kind: 'mechanical sensitivity, not a forecast',
  priceFactor, volumeFactor: 1, operatingExpenseFactor: 1,
}));
console.log(JSON.stringify({
  asOf: '2026-11-06', source, facts, baseline,
  caveats: [
    'Effective sales-value factor is applied to all consolidated sales and is not a pure NAND ASP forecast.',
    'Volume, operating expenses and timing are independent choices; FX and net financial costs are held fixed.',
    'Product mix, JV accounting, fixed and variable cost structure, impairments and tax changes are simplified.',
    'Net income is after accrual tax expense; tax payments must not be subtracted again from net income.',
    'These net-income scenarios do not estimate free cash flow or distributable cash.',
    'Central ranges are judgmental scenario ranges, not probability intervals or profit floors and ceilings.',
  ],
  nineMonthsActualPlusGuidanceTrn, fy2027, fy2028, normalized, priceOnlySensitivity,
  externalConsensus: [
    { provider: 'Minkabu', asOf: '2026-11-06', fiscalYearEnd: '2027-03', parentNetIncomeTrn: 5.397981,
      url: 'https://minkabu.jp/stock/285A/analyst_consensus' },
    { provider: 'IFIS / Kabuyoho Pro', asOf: '2026-11-05', fiscalYearEnd: '2027-03', parentNetIncomeTrn: 5.464233,
      url: 'https://ko5yqxb8d4.execute-api.ap-northeast-1.amazonaws.com/reportAnalyst?bcode=285A' },
  ],
}, null, 2));
