// JPY, post 3-for-1 split effective 2026-10-01. No network or file writes.
// Annualized quarterly EPS and independent profit stress are not full-year guidance.
const inputs = {
  observedPriceJpy: 8708,
  observedPriceTimeJst: '2026-11-06T11:30:00+09:00',
  previousCloseJpy: 9324,
  tradingUnitShares: 100,
  quoteSources: [
    'https://finance.yahoo.co.jp/quote/285A.T',
    'https://quote.nomura.co.jp/nomura/cgi-bin/parser.pl?MKTN=T&QCODE=285A&TEMPLATE=nomura_tp_kabu_01',
  ],
  financialSource: 'https://ssl4.eir-parts.net/doc/285A/tdnet/2902676/00.pdf',
  financialPublicationDate: '2026-10-30',
  sharesAsOf: '2026-09-30',
  issuedSharesPostSplit: 1646307702,
  treasurySharesPostSplit: 48402168,
  q2ActualBasicEpsJpy: 838.31,
  q3CompanyGuidanceBasicEpsJpy: 851.11,
  companyFullYearGuidanceEpsJpy: null,
  independentAnnualProfitStressJpy: [2e12, 1e12],
};
const sharesExTreasury = inputs.issuedSharesPostSplit - inputs.treasurySharesPostSplit;
const q2AnnualizedEpsJpy = inputs.q2ActualBasicEpsJpy * 4;
console.log(JSON.stringify({
  asOf: '2026-11-06',
  inputs,
  sharesExTreasury,
  priceChangeJpy: inputs.observedPriceJpy - inputs.previousCloseJpy,
  priceChangePct: (inputs.observedPriceJpy / inputs.previousCloseJpy - 1) * 100,
  tradingUnitCostBeforeFeesJpy: inputs.observedPriceJpy * inputs.tradingUnitShares,
  q2AnnualizedEpsJpy,
  priceDividedByQ2AnnualizedEps: inputs.observedPriceJpy / q2AnnualizedEpsJpy,
  stress: inputs.independentAnnualProfitStressJpy.map(profit => ({
    kind: 'independent hypothetical annual profit, not company or consensus guidance',
    netIncomeJpy: profit,
    epsJpy: profit / sharesExTreasury,
    referencePER: inputs.observedPriceJpy / (profit / sharesExTreasury),
  })),
}, null, 2));
