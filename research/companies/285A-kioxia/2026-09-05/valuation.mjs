// Reproducible arithmetic for the accompanying Japanese research note.
// Monetary inputs are JPY trillions unless the variable name says otherwise.
// No API requests, network access, or file writes are performed by this script.
import assert from 'node:assert/strict';

const facts = {
  priceJpy: 54460, // 2026-09-04 Tokyo close, pre 3-for-1 split.
  issuedSharesAtJune30: 548015088,
  treasurySharesAtJune30: 450,
  sharesRepurchasedAugust: 16133500,
  repurchaseCostJpy: 799997689000,
  q1NetIncome: 0.842165,
  q2RevenueGuidance: 2.39,
  q2OperatingProfitGuidance: 1.89,
  q2PretaxProfitGuidance: 1.87,
  q2NetIncomeGuidance: 1.27,
  consensusEpsFYMarch2027Jpy: 10406.64,
  consensusEpsFYMarch2028Jpy: 14253.12,
};

const shares = facts.issuedSharesAtJune30 - facts.treasurySharesAtJune30
  - facts.sharesRepurchasedAugust;
const cap = shares * facts.priceJpy / 1e12;
const runRateNet = facts.q2NetIncomeGuidance * 4;
const taxRate = 1 - facts.q2NetIncomeGuidance / facts.q2PretaxProfitGuidance;

// Mechanical ASP sensitivity, NOT a NAND price forecast.
// Quantity, product mix, FX, all operating costs, and net finance costs stay fixed.
// Applying an ASP shock to all revenue is an approximation, including JV/other revenue.
const aspStress = [0, -0.2, -0.4, -0.5].map(change => {
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
// working capital and lease principal payments. Existing borrowings assumed refinanced
// at a broadly stable principal, not counted as new cash income. No separate debt
// subtraction is made from this equity-CF value. No existing excess cash/securities are
// added, since an up-to-date post-buyback balance sheet is unavailable.
// Years are the next rolling 12-month periods, not Kioxia's fiscal years.
const assumptions = {
  discountRate: 0.12,
  perpetualGrowthRate: 0,
  scenarios: [
    { name: 'bear', annualEquityCF: [3.5, 2.5, 1.5], terminalAnnualEquityCF: 1.5 },
    { name: 'base', annualEquityCF: [4.5, 4.5, 3.5], terminalAnnualEquityCF: 3.5 },
    { name: 'bull', annualEquityCF: [5.5, 6.0, 6.5], terminalAnnualEquityCF: 5.0 },
  ],
};

function equityValue(scenario, rate = assumptions.discountRate) {
  const flowPV = scenario.annualEquityCF.reduce((sum, cf, i) => sum + cf / (1 + rate) ** (i + 1), 0);
  const terminalPV = scenario.terminalAnnualEquityCF / rate / (1 + rate) ** 3;
  const value = flowPV + terminalPV;
  return { name: scenario.name, rate, annualEquityCF: scenario.annualEquityCF,
    terminalAnnualEquityCF: scenario.terminalAnnualEquityCF,
    flowPV, terminalPV, equityValueTrn: value, valuePerShareJpy: value * 1e12 / shares,
    gapToPrice: value / cap - 1, terminalShareOfValue: terminalPV / value };
}

const base = assumptions.scenarios[1];
const basePVWithoutTerminal = base.annualEquityCF.reduce((sum, cf, i) =>
  sum + cf / (1 + assumptions.discountRate) ** (i + 1), 0);
const impliedTerminalCF = (cap - basePVWithoutTerminal)
  * (1 + assumptions.discountRate) ** 3 * assumptions.discountRate;

const result = {
  asOf: '2026-09-05', priceDate: '2026-09-04', splitBasis: 'pre-split', facts, shares,
  marketCapExTreasuryTrn: cap,
  averageRepurchasePriceJpy: facts.repurchaseCostJpy / facts.sharesRepurchasedAugust,
  actualRepurchaseSharePercent: 100 * facts.sharesRepurchasedAugust
    / (facts.issuedSharesAtJune30 - facts.treasurySharesAtJune30),
  consensusPERFYMarch2027: facts.priceJpy / facts.consensusEpsFYMarch2027Jpy,
  consensusPERFYMarch2028: facts.priceJpy / facts.consensusEpsFYMarch2028Jpy,
  q2AnnualizedNetIncomeTrn: runRateNet,
  q2AnnualizedEPSJpy: runRateNet * 1e12 / shares,
  q2AnnualizedPER: cap / runRateNet,
  fullYearNetIfRemainingQuartersEqualQ2Trn: facts.q1NetIncome + 3 * facts.q2NetIncomeGuidance,
  assumptions, aspStress,
  valuations: assumptions.scenarios.map(s => equityValue(s)),
  rateSensitivity: [0.10, 0.12, 0.14].map(rate => equityValue(base, rate)),
  impliedTerminalCFTrnAtCurrentPrice: impliedTerminalCF,
  purchaseThresholdAt20PercentMarginOfSafetyJpy: equityValue(base).valuePerShareJpy * 0.8,
  valueOfOneTrillionAdditionalExcessCashPerShareJpy: 1e12 / shares,
};

assert.equal(shares, 531881138);
assert(Math.abs(aspStress[0].netIncome - 5.08) < 1e-10);
assert(result.valuations[0].equityValueTrn < result.valuations[1].equityValueTrn);
assert(result.valuations[1].equityValueTrn < result.valuations[2].equityValueTrn);
assert(result.rateSensitivity[0].equityValueTrn > result.rateSensitivity[1].equityValueTrn);
assert(result.rateSensitivity[1].equityValueTrn > result.rateSensitivity[2].equityValueTrn);
console.log(JSON.stringify(result, null, 2));
