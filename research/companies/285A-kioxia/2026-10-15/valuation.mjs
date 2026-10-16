// All values are post 3-for-1 split; currency JPY; monetary CF inputs JPY trillions.
// Scenario assumptions are analyst choices, not company or consensus forecasts.
import assert from 'node:assert/strict';

const facts = {
  observedPriceJpy: 13175,
  observedPriceTimeJst: '2026-10-15T10:18:00+09:00',
  previousCloseJpy: 14690,
  splitRatio: 3,
  splitEffectiveDate: '2026-10-01',
  sharesAsOf: '2026-08-31',
  issuedSharesPreSplit: 548639034,
  treasurySharesPreSplit: 16134027,
  shareSource: 'https://disclosure2dl.edinet-fsa.go.jp/searchdocument/pdf/S100Z1UD.pdf',
  q1NetIncomeTrn: 0.842165,
  q2CompanyGuidanceNetIncomeTrn: 1.270,
  companyFullYearNetIncomeGuidanceTrn: null,
  companyGuidancePublishedDate: '2026-07-31',
  ifisConsensus: {
    asOf: '2026-10-14', fiscalYearEnd: '2027-03',
    revenueTrn: 10.209959, operatingProfitTrn: 8.077118,
    pretaxProfitTrn: 8.216647, netIncomeTrn: 5.648790,
    source: 'https://kabuyoho.jp/sp/reportAnalyst?bcode=285A',
  },
};
const shares = (facts.issuedSharesPreSplit - facts.treasurySharesPreSplit) * facts.splitRatio;
const previousShares = 1595643414;
const assumptions = {
  cfDefinition: 'Prospective equity cash flow after tax, interest, necessary investment, working capital and lease principal; existing debt refinanced. No additional excess cash added.',
  yearDefinition: 'Rolling 12-month periods starting October 2026; not fiscal years.',
  requiredEquityReturn: 0.13, perpetualGrowth: 0,
  purchaseMargins: [0.20, 0.25, 0.30],
  // These are alternative scenarios. The old basic case has not been mechanically
  // downgraded on the basis of CXMT DRAM news. No probabilities are estimated.
  scenarios: [
    { name: 'weak', annualEquityCFTrn: [3.5, 2.5, 1.5], terminalAnnualEquityCFTrn: 1.5 },
    { name: 'purchase_cautious', annualEquityCFTrn: [5.0, 4.0, 3.0], terminalAnnualEquityCFTrn: 3.0 },
    { name: 'previous_basic', annualEquityCFTrn: [5.0, 4.5, 3.5], terminalAnnualEquityCFTrn: 3.5 },
    { name: 'strong', annualEquityCFTrn: [6.0, 6.5, 6.5], terminalAnnualEquityCFTrn: 5.0 },
  ],
};
function value(scenario, rate = assumptions.requiredEquityReturn, count = shares) {
  const explicitPVTrn = scenario.annualEquityCFTrn.reduce((sum, cf, i) => sum + cf / (1 + rate) ** (i + 1), 0);
  const terminalPVTrn = scenario.terminalAnnualEquityCFTrn / rate / (1 + rate) ** 3;
  const equityValueTrn = explicitPVTrn + terminalPVTrn;
  const valuePerShareJpy = equityValueTrn * 1e12 / count;
  return {
    name: scenario.name, rate, explicitPVTrn, terminalPVTrn, equityValueTrn,
    valuePerShareJpy, terminalWeight: terminalPVTrn / equityValueTrn,
    upsideVsObservedPrice: valuePerShareJpy / facts.observedPriceJpy - 1,
    marginOfSafetyAtObservedPrice: 1 - facts.observedPriceJpy / valuePerShareJpy,
    purchaseThresholds: assumptions.purchaseMargins.map(margin => ({ margin, priceJpy: valuePerShareJpy * (1 - margin) })),
  };
}
const cautious = assumptions.scenarios[1];
const previousBasic = assumptions.scenarios[2];
const ifisEpsJpy = facts.ifisConsensus.netIncomeTrn * 1e12 / shares;
const result = {
  asOf: '2026-10-15', facts, shares, assumptions,
  marketCapExTreasuryTrn: facts.observedPriceJpy * shares / 1e12,
  consensusDerivedEpsJpy: ifisEpsJpy,
  consensusPERAtObservedPrice: facts.observedPriceJpy / ifisEpsJpy,
  ifisImpliedSecondHalfNetIncomeTrn: facts.ifisConsensus.netIncomeTrn - facts.q1NetIncomeTrn - facts.q2CompanyGuidanceNetIncomeTrn,
  valuations: assumptions.scenarios.map(s => value(s)),
  cautiousRateSensitivity: [0.12, 0.13, 0.14].map(r => value(cautious, r)),
  previousPublishedModel: value(previousBasic, 0.12, previousShares),
  previousBasicWithUpdatedShares: value(previousBasic, 0.12),
  firstYearCFSensitivity: [3.5, 4, 5].map(cf => ({ firstYearCFTrn: cf, ...value({ ...cautious, annualEquityCFTrn: [cf, 4, 3] }) })),
  // Earnings stress is separate from the CF model; cash flow is NOT equated to EPS.
  earningsStress: [facts.ifisConsensus.netIncomeTrn, 2, 1].map(netIncomeTrn => {
    const epsJpy = netIncomeTrn * 1e12 / shares;
    return { netIncomeTrn, kind: netIncomeTrn === facts.ifisConsensus.netIncomeTrn ? 'external consensus' : 'independent hypothetical stress', epsJpy,
      perAt13000: 13000 / epsJpy, perAt12000: 12000 / epsJpy };
  }),
  roundedPurchasePolicy: {
    starterBandJpy: [12500, 13000], preferredPriceJpy: 12000,
    conditionalAddAroundJpy: 11000,
    condition: 'Do not add merely because price fell; recheck SSD demand, cash collection, company guidance and financing terms.',
  },
  weakCaseDownsideFrom12000: value(assumptions.scenarios[0]).valuePerShareJpy / 12000 - 1,
};
assert.equal(shares, 1597515021);
assert(result.valuations[0].valuePerShareJpy < result.valuations[1].valuePerShareJpy);
assert(result.valuations[1].valuePerShareJpy < result.valuations[2].valuePerShareJpy);
assert(result.valuations[2].valuePerShareJpy < result.valuations[3].valuePerShareJpy);
assert(result.cautiousRateSensitivity[0].valuePerShareJpy > result.cautiousRateSensitivity[2].valuePerShareJpy);
assert(Math.abs(result.previousPublishedModel.valuePerShareJpy - 19617.883464467374) < 1);
console.log(JSON.stringify(result, null, 2));
