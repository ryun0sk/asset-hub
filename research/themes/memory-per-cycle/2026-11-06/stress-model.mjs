// Independent valuation sensitivities. JPY trillions unless otherwise noted.
const baseline = {
  annualRevenueTrn: 10,
  annualOperatingExpenseTrn: 2.02,
  annualNetNonOperatingExpenseTrn: 0.06,
  afterTaxFactor: 1.36 / 1.98,
  annualizedNetIncomeTrn: 5.44,
  source: 'https://ssl4.eir-parts.net/doc/285A/tdnet/2902676/00.pdf',
  kind: 'Q3 company guidance multiplied by four, not full-year or FY2028 guidance',
};
const priceJpy = 8417;
const shares = 1597905534;
const marketCapTrn = priceJpy * shares / 1e12;
const scenarioInputs = [
  { name: 'guidance_annualization', salesValueFactor: 1, volumeFactor: 1, expenseFactor: 1 },
  { name: 'previous_normalization_center', salesValueFactor: 0.6, volumeFactor: 1.2, expenseFactor: 1.5 },
  { name: 'previous_normalization_lower', salesValueFactor: 0.5, volumeFactor: 1.2, expenseFactor: 1.5 },
  { name: 'deeper_price_decline', salesValueFactor: 0.4, volumeFactor: 1.2, expenseFactor: 1.5 },
  { name: 'deeper_price_and_volume_decline', salesValueFactor: 0.4, volumeFactor: 0.9, expenseFactor: 1.5 },
];
const scenarios = scenarioInputs.map(s => {
  const revenueTrn = baseline.annualRevenueTrn * s.salesValueFactor * s.volumeFactor;
  const operatingExpenseTrn = baseline.annualOperatingExpenseTrn * s.expenseFactor;
  const operatingProfitTrn = revenueTrn - operatingExpenseTrn;
  const netIncomeTrn = (operatingProfitTrn - baseline.annualNetNonOperatingExpenseTrn) * baseline.afterTaxFactor;
  return { ...s, revenueTrn, operatingExpenseTrn, operatingProfitTrn, netIncomeTrn,
    referencePE: netIncomeTrn > 0 ? marketCapTrn / netIncomeTrn : null };
});
const multipleBridge = [7.8, 10].map(newPE => ({
  initialPE: 3, newPE, newEPSAsFractionOfOld: 3 / newPE, epsDeclinePct: (1 - 3 / newPE) * 100,
  assumptions: 'Same share price and share count; net EPS denominator, not operating profit.',
}));
const cashFlowIllustrations = [3, 4, 5].map(years => ({
  annualCashFlow: 100, years, discountRate: 0.12, terminalValue: 0,
  presentValue: Array.from({ length: years }, (_, i) => 100 / 1.12 ** (i + 1)).reduce((a, b) => a + b, 0),
  kind: 'abstract equity cash-flow example; not a forecast for a company',
}));
console.log(JSON.stringify({
  asOf: '2026-11-06', priceJpy, priceTimeJst: '2026-11-06T13:27:19+09:00', shares, marketCapTrn,
  baseline, scenarios, multipleBridge, cashFlowIllustrations,
  caveats: [
    'Sales-value factor is an approximation across consolidated sales, not a pure NAND ASP forecast.',
    'Volume and expenses are independent assumptions, not statistically estimated outcomes.',
    'No customer default, impairment, legal recovery or working-capital changes are modeled.',
    'Accrual net income is not shareholder free cash flow. Scenarios are neither floors nor confidence intervals.',
  ],
}, null, 2));
