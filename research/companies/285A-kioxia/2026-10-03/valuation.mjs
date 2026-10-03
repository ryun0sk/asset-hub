// Reproducible arithmetic for the accompanying Japanese research note (2026-10-03 edition).
// Copied from ../2026-09-05/valuation.mjs and updated.
// ALL per-share figures are on a POST 3-for-1 split basis (split effective 2026-10-01,
// ex-rights 2026-09-29). Pre-split equivalents are shown only for comparison (x3).
// Monetary inputs are JPY trillions unless the variable name says otherwise.
// No API requests, network access, or file writes are performed by this script.
import assert from 'node:assert/strict';

const SPLIT_RATIO = 3;

const facts = {
  priceJpy: 19300, // 2026-10-02 Tokyo close, post-split (Yahoo Finance chart API).
  previousEditionPricePreSplitJpy: 54460, // 2026-09-04 close used in 2026-09-05 edition.
  previousEditionBaseValuePreSplitJpy: 58014.31087235664, // 2026-09-05 edition base case.
  // Share count: June 30 issued - treasury - August buyback (pre-split), then x3.
  // Pro forma; Sept 30 actual share count is not yet published.
  issuedSharesAtJune30PreSplit: 548015088,
  treasurySharesAtJune30PreSplit: 450,
  sharesRepurchasedAugustPreSplit: 16133500,
  q1NetIncome: 0.842165, // IFRS, actual, Apr-Jun 2026.
  // Q2 (Jul-Sep 2026) company guidance announced 2026-07-31 (IFRS figures in the
  // earnings release). Not revised as of 2026-10-03.
  q2RevenueGuidance: 2.39,
  q2OperatingProfitGuidance: 1.89,
  q2PretaxProfitGuidance: 1.87,
  q2NetIncomeGuidance: 1.27,
  q2GuidanceUsdJpy: 162,
  q2FxSensitivityOperatingProfitPerYenTrn: 0.013, // quarterly, company estimate.
  // Monthly average USD/JPY (Yahoo Finance JPY=X daily closes; not the company's rates).
  usdJpyAvgAug2026: 158.86,
  usdJpyAvgSep2026: 156.38,
  // IFIS consensus (kabuyoho.jp, as of 2026-10-02), FY ending March 2027, JPY trn.
  consensusFYMarch2027: { revenue: 10.185203, operatingProfit: 8.06364,
    pretaxProfit: 8.202932, netIncome: 5.627401 },
  consensusPretaxFYMarch2027FourWeeksAgo: 8.026891,
  consensusTargetPricePostSplitJpy: 39604, // IFIS, 9 analysts, 2026-10-02.
  // ADR: Bloomberg (2026-09-14) reported >= USD 10bn; company says nothing decided.
  adrReportedSizeUsdBn: 10,
  usdJpyLatest: 157.83,
};

const preSplitShares = facts.issuedSharesAtJune30PreSplit - facts.treasurySharesAtJune30PreSplit
  - facts.sharesRepurchasedAugustPreSplit;
const shares = preSplitShares * SPLIT_RATIO;
const cap = shares * facts.priceJpy / 1e12;
const runRateNet = facts.q2NetIncomeGuidance * 4;
const taxRate = 1 - facts.q2NetIncomeGuidance / facts.q2PretaxProfitGuidance;

// Rough FX drag on Q2 OP vs guidance: July already fixed, so 2/3 of the quarter.
// Analyst estimate only; company's actual conversion rates differ.
const augSepAvg = (facts.usdJpyAvgAug2026 + facts.usdJpyAvgSep2026) / 2;
const q2FxDragOperatingProfitTrn = -facts.q2FxSensitivityOperatingProfitPerYenTrn
  * (facts.q2GuidanceUsdJpy - augSepAvg) * (2 / 3);

// Mechanical ASP sensitivity, NOT a NAND price forecast.
// Quantity, product mix, FX, all operating costs, and net finance costs stay fixed.
// Applying an ASP shock to all revenue is an approximation, including JV/other revenue.
const aspStress = [0.15, 0, -0.2, -0.4, -0.5].map(change => {
  const revenue = 4 * facts.q2RevenueGuidance * (1 + change);
  const operatingCosts = 4 * (facts.q2RevenueGuidance - facts.q2OperatingProfitGuidance);
  const financeCosts = 4 * (facts.q2OperatingProfitGuidance - facts.q2PretaxProfitGuidance);
  const operatingProfit = revenue - operatingCosts;
  const netIncome = (operatingProfit - financeCosts) * (1 - taxRate);
  return { change, revenue, operatingProfit, netIncome,
    epsJpy: netIncome * 1e12 / shares, per: cap / netIncome };
});

// Analyst-selected scenarios, NOT company guidance or consensus estimates.
// CF = prospective cash available to equity after tax, interest, necessary investment,
// working capital and lease principal payments. Existing borrowings assumed refinanced.
// No separate debt subtraction; no excess cash added (post-buyback B/S not yet published).
// Years are rolling 12-month periods from 2026-10, not Kioxia's fiscal years.
// Change vs 2026-09-05 edition: base year-1 CF 4.5 -> 5.0, bull year-2 6.0 -> 6.5.
const assumptions = {
  discountRate: 0.12,
  perpetualGrowthRate: 0,
  scenarios: [
    { name: 'bear', annualEquityCF: [3.5, 2.5, 1.5], terminalAnnualEquityCF: 1.5 },
    { name: 'base', annualEquityCF: [5.0, 4.5, 3.5], terminalAnnualEquityCF: 3.5 },
    { name: 'bull', annualEquityCF: [6.0, 6.5, 6.5], terminalAnnualEquityCF: 5.0 },
  ],
};

function equityValue(scenario, rate = assumptions.discountRate, shareCount = shares, extraTrn = 0) {
  const flowPV = scenario.annualEquityCF.reduce((sum, cf, i) => sum + cf / (1 + rate) ** (i + 1), 0);
  const terminalPV = scenario.terminalAnnualEquityCF / rate / (1 + rate) ** 3;
  const value = flowPV + terminalPV + extraTrn;
  return { name: scenario.name, rate, annualEquityCF: scenario.annualEquityCF,
    terminalAnnualEquityCF: scenario.terminalAnnualEquityCF,
    flowPV, terminalPV, equityValueTrn: value, valuePerShareJpy: value * 1e12 / shareCount,
    valuePerSharePreSplitEquivalentJpy: value * 1e12 / shareCount * SPLIT_RATIO,
    gapToPrice: value * 1e12 / shareCount / facts.priceJpy - 1,
    terminalShareOfValue: terminalPV / value };
}

const base = assumptions.scenarios[1];
const basePVWithoutTerminal = base.annualEquityCF.reduce((sum, cf, i) =>
  sum + cf / (1 + assumptions.discountRate) ** (i + 1), 0);
const impliedTerminalCF = (cap - basePVWithoutTerminal)
  * (1 + assumptions.discountRate) ** 3 * assumptions.discountRate;

// ADR sensitivity: IF the reported USD 10bn were entirely NEW shares sold at today's price.
// It may instead be (partly) a secondary sale by existing holders -> no dilution.
const adrProceedsTrn = facts.adrReportedSizeUsdBn * 1e9 * facts.usdJpyLatest / 1e12;
const adrNewShares = adrProceedsTrn * 1e12 / facts.priceJpy;
const baseAfterHypotheticalPrimaryADR = equityValue(base, assumptions.discountRate,
  shares + adrNewShares, adrProceedsTrn);

const consensusEps = facts.consensusFYMarch2027.netIncome * 1e12 / shares;

const result = {
  asOf: '2026-10-03', priceDate: '2026-10-02', splitBasis: 'post-split (3-for-1, effective 2026-10-01)',
  facts, preSplitShares, shares,
  marketCapExTreasuryTrn: cap,
  priceChangeVsPreviousEdition: facts.priceJpy * SPLIT_RATIO / facts.previousEditionPricePreSplitJpy - 1,
  previousEditionPricePostSplitEquivalentJpy: facts.previousEditionPricePreSplitJpy / SPLIT_RATIO,
  previousEditionBaseValuePostSplitEquivalentJpy: facts.previousEditionBaseValuePreSplitJpy / SPLIT_RATIO,
  consensusFYMarch2027EpsJpy: consensusEps,
  consensusFYMarch2027PER: facts.priceJpy / consensusEps,
  consensusPretaxRevision4w: facts.consensusFYMarch2027.pretaxProfit / facts.consensusPretaxFYMarch2027FourWeeksAgo - 1,
  consensusTargetUpside: facts.consensusTargetPricePostSplitJpy / facts.priceJpy - 1,
  q2AnnualizedNetIncomeTrn: runRateNet,
  q2AnnualizedEPSJpy: runRateNet * 1e12 / shares,
  q2AnnualizedPER: cap / runRateNet,
  fullYearNetIfRemainingQuartersEqualQ2Trn: facts.q1NetIncome + 3 * facts.q2NetIncomeGuidance,
  usdJpyAvgAugSep: augSepAvg,
  q2FxDragOperatingProfitTrnRoughEstimate: q2FxDragOperatingProfitTrn,
  assumptions, aspStress,
  valuations: assumptions.scenarios.map(s => equityValue(s)),
  rateSensitivity: [0.10, 0.12, 0.14].map(rate => equityValue(base, rate)),
  impliedTerminalCFTrnAtCurrentPrice: impliedTerminalCF,
  purchaseThresholdAt20PercentMarginOfSafetyJpy: equityValue(base).valuePerShareJpy * 0.8,
  valueOfOneTrillionAdditionalExcessCashPerShareJpy: 1e12 / shares,
  hypotheticalPrimaryADR: { proceedsTrn: adrProceedsTrn, newShares: adrNewShares,
    dilutionPercent: 100 * adrNewShares / shares,
    baseValuePerShareJpy: baseAfterHypotheticalPrimaryADR.valuePerShareJpy },
};

assert.equal(preSplitShares, 531881138);
assert.equal(shares, 1595643414);
assert(Math.abs(aspStress[1].netIncome - 5.08) < 1e-10);
assert(result.valuations[0].equityValueTrn < result.valuations[1].equityValueTrn);
assert(result.valuations[1].equityValueTrn < result.valuations[2].equityValueTrn);
assert(result.rateSensitivity[0].equityValueTrn > result.rateSensitivity[1].equityValueTrn);
assert(result.rateSensitivity[1].equityValueTrn > result.rateSensitivity[2].equityValueTrn);
console.log(JSON.stringify(result, null, 2));
