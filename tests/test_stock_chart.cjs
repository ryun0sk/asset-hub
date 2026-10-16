const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const context=vm.createContext({Date});
vm.runInContext(fs.readFileSync('web/stock-chart-model.js','utf8').replace(/^export /gm,''),context);
const {readPriceHistory,periodRows,priceSummary}=vm.runInContext('({readPriceHistory,periodRows,priceSummary})',context);
const payload=JSON.parse(fs.readFileSync('research/companies/SPCX-spacex/2026-10-05/sources/price-history.json','utf8'));

test('saved series is post-listing SPCX in USD and matches the research price',()=>{
  const history=readPriceHistory(payload);
  assert.equal(history.rows[0].date,'2026-06-12');
  assert.equal(history.rows.at(-1).date,'2026-10-02');
  assert.equal(history.rows.at(-1).close,158.96);
  assert.equal(history.rows.length,78);
});
test('rejects the former ETF, wrong currency, pre-listing dates and duplicate dates',()=>{
  for(const extra of [{symbol:'SPCK'},{currency:'JPY'},{firstTradingDate:'2020-12-17'},{rows:[{date:'2026-06-11',close:20}]},{rows:[{date:'2026-06-12',close:160.95},{date:'2026-06-12',close:160.95}]}]) assert.throws(()=>readPriceHistory({...payload,...extra}));
});
test('calendar ranges anchor to the last stored session and retain only observed dates',()=>{
  const rows=periodRows(payload.rows,30);
  assert.equal(rows[0].date,'2026-09-03');
  assert.equal(rows.at(-1).date,'2026-10-02');
  assert.ok(!rows.some(row=>row.date==='2026-09-07'));
  assert.equal(periodRows(payload.rows).length,78);
});
test('missing prices are retained and never counted as a zero-price return',()=>{
  const rows=[{date:'2026-06-12',close:100},{date:'2026-06-15',close:null},{date:'2026-06-16',close:120}];
  const history=readPriceHistory({...payload,rows});
  assert.equal(history.rows[1].close,null);
  const summary=priceSummary(history.rows);
  assert.equal(summary.change,20);
  assert.ok(Math.abs(summary.periodPercent-20)<1e-10);
});
test('period return uses the selected first close, rather than the IPO offer price',()=>{
  const full=priceSummary(payload.rows), recent=priceSummary(periodRows(payload.rows,30));
  assert.equal(full.first.close,160.95);
  assert.ok(Math.abs(full.periodPercent-(158.96/160.95-1)*100)<1e-10);
  assert.notEqual(full.periodPercent,recent.periodPercent);
});
test('Tesla history is explicitly selected and cannot be substituted for SpaceX',()=>{
  const tesla=JSON.parse(fs.readFileSync('research/companies/TSLA-tesla/2026-10-05/sources/price-history.json','utf8'));
  const history=readPriceHistory(tesla,'TSLA');
  assert.equal(history.rows[0].date,'2025-10-03');
  assert.equal(history.rows.at(-1).date,'2026-10-02');
  assert.equal(history.rows.at(-1).close,370.59);
  assert.equal(history.rows.length,251);
  assert.throws(()=>readPriceHistory(tesla));
  assert.throws(()=>readPriceHistory(payload,'TSLA'));
  assert.throws(()=>readPriceHistory(tesla,'UNKNOWN'));
});
