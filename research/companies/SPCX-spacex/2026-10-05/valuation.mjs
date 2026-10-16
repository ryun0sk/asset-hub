// 2026-10-05 snapshot. USD; financial amounts in billion USD.
// Inputs are observed values; scenario P/E, margins and returns are author assumptions.
const input = {
  price: 158.96, // 2026-10-02 regular-session close
  sharesA: 7_696_293_669, // 2026-07-28 10-Q cover
  sharesB: 5_485_486_276,
  cursorCommonConsideration: 389_289_254, // 2026-08-14 8-K
  cursorVestedRsuGross: 1_752_426, // before tax withholding
  revenueQ2: 7.814,
  operatingCashflowH1: 3.466,
  ppePurchasesH1: 28.476,
};
const shares = input.sharesA + input.sharesB
  + input.cursorCommonConsideration + input.cursorVestedRsuGross;
const equityValue = input.price * shares / 1e9;
const annualizedRevenue = input.revenueQ2 * 4;
const valuation = {
  asOf: '2026-10-05',
  currency: 'USD',
  financialUnit: 'billion USD',
  shareBasis: 'May 2026 5-for-1 split adjusted',
  sharesProForma: shares,
  shareCaveat: 'July 28 plus August 14 Cursor consideration, before tax withholding; other changes, unvested RSUs and options excluded; not October 5 confirmed shares.',
  equityValue,
  annualizedRevenue,
  psOnAnnualizedQ2: equityValue / annualizedRevenue,
  simpleCfoLessPpeH1: input.operatingCashflowH1 - input.ppePurchasesH1,
  fcfCaveat: 'Author-defined simple CFO minus PPE purchases, not company FCF; product rebates, capitalized interest, intangible assets, acquisitions and other items not adjusted.',
  profitConditions: [30, 40, 50].map(pe => ({
    assumedPe: pe,
    requiredNetProfit: equityValue / pe,
    requiredSalesAt20pctNetMargin: equityValue / pe / 0.20,
    requiredSalesAt25pctNetMargin: equityValue / pe / 0.25,
  })),
  fiveYearReturnCondition: {
    returnAssumption: 0.10,
    years: 5,
    assumedPe: 50,
    sharesConstantNoDividend: true,
    requiredEquityValue: equityValue * 1.10 ** 5,
    requiredNetProfit: equityValue * 1.10 ** 5 / 50,
    requiredSalesAt25pctNetMargin: equityValue * 1.10 ** 5 / 50 / 0.25,
  },
  multipleStress: [40, 30].map(ps => ({
    assumedPs: ps,
    priceWithSharesAndSalesUnchanged: annualizedRevenue * ps * 1e9 / shares,
  })),
};
console.log(JSON.stringify(valuation, null, 2));
