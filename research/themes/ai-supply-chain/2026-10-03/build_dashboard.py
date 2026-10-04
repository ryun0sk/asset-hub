from pathlib import Path
import json
BASE=Path(__file__).resolve().parent
s=(BASE/'dashboard.template.html').read_text()
prices=json.loads((BASE/'prices.json').read_text())
catalog=json.loads((BASE/'catalog.json').read_text())
known={c['symbol'] for c in prices['companies']}
assert len(known)==43
assert all(set(g['symbols']) <= known for g in catalog['groups'])
groups={g['id'] for g in catalog['groups']}
assert all(e[0] in groups and e[1] in groups for e in catalog['edges'])
fundamentals=json.loads((BASE/'fundamentals.json').read_text())
assert {c['symbol'] for c in fundamentals['companies']}==known
valuation=json.loads((BASE/'valuation.json').read_text())
assert {c['symbol'] for c in valuation['companies']}==known
for token,path in [('/*__PRICE_DATA__*/','prices.json'),('/*__VALUATION_DATA__*/','valuation.json'),('/*__FUNDAMENTAL_DATA__*/','fundamentals.json'),('/*__CATALOG_DATA__*/','catalog.json'),('/*__CHART_LIBRARY__*/','sources/chart.umd.min.js')]:
    value=(BASE/path).read_text()
    if path.endswith('.json'): value=value.replace('</','<\\/')
    s=s.replace(token,value)
assert '/*__PRICE_DATA__*/' not in s and '/*__VALUATION_DATA__*/' not in s
assert len(s.encode())<=16*1024*1024,'index.html must stay at or below 16MB'
(BASE/'index.html').write_text(s)
print('Built',len(s.encode()),'bytes;',len(known),'companies;',len(catalog['groups']),'groups')
