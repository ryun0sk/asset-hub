"""Reproduce conditional price/EPS ranges, using saved quotes and assumptions."""
import csv
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
inputs = json.loads((BASE / 'candidate-inputs.json').read_text())
prices = {c['symbol']: c for c in json.loads((BASE / 'prices.json').read_text())['items']}

def earnings_range(profits, shares, price):
    low, high = profits
    min_shares, max_shares = shares
    eps_low, eps_high = low / max_shares, high / min_shares
    return {'net_income_bn': profits, 'eps_low': eps_low, 'eps_high': eps_high,
            'reference_PE_low': price / eps_high, 'reference_PE_high': price / eps_low}

rows = []
for company in inputs['companies']:
    quote = prices[company['symbol']]
    if company['currency'] != quote['currency']:
        raise ValueError('price/EPS currency mismatch: ' + company['symbol'])
    price = quote['current']['price']
    rows.append({**company, 'price': price, 'price_time_local': quote['current']['time_local'],
                 'near': earnings_range(company['near_net_income_bn'], company['diluted_shares_bn_range'], price),
                 'cautious': earnings_range(company['cautious_net_income_bn'], company['diluted_shares_bn_range'], price)
                 if company['cautious_net_income_bn'] else None})
(BASE / 'candidates.json').write_text(json.dumps({'as_of': '2026-11-06',
    'warning': 'Conditional independent earnings multiples; not current TTM/company forecast PER, fair prices, confidence intervals or numerical buy ranking.',
    'companies': rows}, ensure_ascii=False, indent=2) + '\n')
with (BASE / 'candidates.csv').open('w', newline='') as stream:
    writer = csv.writer(stream)
    writer.writerow(['symbol', 'period', 'currency', 'price', 'price_time_local',
                     'near_profit_low_bn', 'near_profit_high_bn', 'near_EPS_low', 'near_EPS_high',
                     'near_reference_PE_low', 'near_reference_PE_high',
                     'cautious_profit_low_bn', 'cautious_profit_high_bn', 'note'])
    for row in rows:
        near, cautious = row['near'], row['cautious']
        writer.writerow([row['symbol'], row['period'], row['currency'], row['price'], row['price_time_local'],
                         *near['net_income_bn'], near['eps_low'], near['eps_high'],
                         near['reference_PE_low'], near['reference_PE_high'],
                         *(cautious['net_income_bn'] if cautious else [None, None]), row['note']])
for row in rows:
    print(row['symbol'], row['period'], 'conditional PE',
          round(row['near']['reference_PE_low'], 2), round(row['near']['reference_PE_high'], 2))
