"""Merge saved company research and quote observations without external access."""
import csv
from collections import Counter
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent

def checked_symbols(rows, source):
    counts = Counter(row['symbol'] for row in rows)
    duplicates = sorted(symbol for symbol, count in counts.items() if count > 1)
    if len(rows) != 46 or duplicates:
        raise ValueError(f'{source}: expected 46 unique company symbols; '
                         f'got {len(rows)} rows; duplicates: {duplicates}')
    return set(counts)

def plain(value):
    if value is None:
        return ''
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))

def main():
    universe = json.loads((BASE / 'universe.json').read_text())
    prices = json.loads((BASE / 'prices.json').read_text())
    expected = checked_symbols(universe, 'universe.json')
    checked_symbols(prices['items'], 'prices.json.items')
    quotes = {c['symbol']: c for c in prices['items']}
    research = {}
    for source in sorted((BASE / 'parts').glob('*.json')):
        content = json.loads(source.read_text())
        rows = content if isinstance(content, list) else content['companies']
        for company in rows:
            symbol = company['symbol']
            if symbol in research:
                raise ValueError('duplicate company: ' + symbol)
            research[symbol] = {**company, 'research_file': source.relative_to(BASE).as_posix()}
    if set(research) != expected or set(quotes) != expected:
        raise ValueError({'missing_research': sorted(expected - set(research)),
                          'extra_research': sorted(set(research) - expected),
                          'missing_quotes': sorted(expected - set(quotes))})
    combined = []
    for item in universe:
        symbol = item['symbol']
        quote = quotes[symbol]
        if quote['status'] != 'ok' or not quote.get('current'):
            raise ValueError('quote unavailable: ' + symbol)
        company = research[symbol]
        old = quote.get('oct16_on_current_split_basis')
        change = (quote['current']['price'] / old['close'] - 1) * 100 if old else None
        combined.append({**company, 'quote_currency': item['currency'],
                         'quote': quote['current'], 'quote_source': quote['source'],
                         'quote_history_url': quote['history_url'],
                         'last_completed_daily_bar': quote['last_completed'],
                         'oct16_on_current_split_basis': old,
                         'change_since_oct16_pct': change})
    payload = {'as_of': '2026-11-06 JST', 'quote_fetch_cutoff_utc': prices['cutoff_utc'],
               'scope': '46-company current review; not a recalculation of the old 2028/29 ranking',
               'companies': combined}
    (BASE / 'review.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    columns = ['symbol', 'name', 'quote_currency', 'price', 'price_time_local',
               'change_since_oct16_pct', 'latest_report_date', 'latest_period',
               'status', 'actuals', 'guidance', 'key_change', 'profit_durability',
               'risks', 'independent_profit_range', 'sources']
    with (BASE / 'review.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for company in combined:
            row = {key: plain(company.get(key)) for key in columns}
            row.update(price=company['quote']['price'], price_time_local=company['quote']['time_local'],
                       change_since_oct16_pct=round(company['change_since_oct16_pct'], 2)
                       if company['change_since_oct16_pct'] is not None else '')
            writer.writerow(row)
    status = Counter(c.get('status', 'unspecified') for c in combined)
    print('Merged', len(combined), 'companies; research status:', dict(status))
    print('Wrote review.json and review.csv')

if __name__ == '__main__':
    main()
