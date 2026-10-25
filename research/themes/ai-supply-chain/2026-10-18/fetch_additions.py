"""Fetch the three added companies only; preserve all earlier snapshots.

Public Yahoo Finance daily Close, split-adjusted and excluding dividends.
Raw responses live in working/; extracted inputs retain URL, time and SHA-256.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

BASE = Path(__file__).resolve().parent
COMPANIES = [
    ('7011.T', '三菱重工', '日本', 'JPY'),
    ('GEV', 'GE Vernova', '米国', 'USD'),
    ('ENR.DE', 'Siemens Energy', 'ドイツ', 'EUR'),
]
START, END = '2016-01-01', '2026-10-16'


def fetch(item):
    symbol, name, country, currency = item
    params = {
        'period1': int(datetime(2016, 1, 1, tzinfo=timezone.utc).timestamp()),
        'period2': int(datetime(2026, 10, 17, tzinfo=timezone.utc).timestamp()),
        'interval': '1d', 'events': 'div,splits', 'includeAdjustedClose': 'true',
    }
    url = 'https://query1.finance.yahoo.com/v8/finance/chart/' + quote(symbol) + '?' + urlencode(params)
    raw = urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=40).read()
    result = json.loads(raw)['chart']['result'][0]
    meta = result['meta']
    assert meta['symbol'] == symbol and meta['currency'] == currency
    dates = [datetime.fromtimestamp(t, ZoneInfo(meta['exchangeTimezoneName'])).date().isoformat()
             for t in result['timestamp']]
    closes = result['indicators']['quote'][0]['close']
    adjusted = result['indicators']['adjclose'][0]['adjclose']
    rows = [{'date': d, 'close': round(c, 6), 'adjusted': round(a, 6) if a is not None else None}
            for d, c, a in zip(dates, closes, adjusted) if START <= d <= END and c is not None]
    assert rows and rows[-1]['date'] == END, (symbol, rows[-1] if rows else None)
    assert all(row['close'] > 0 for row in rows)
    assert len({row['date'] for row in rows}) == len(rows)
    target = BASE / 'working' / 'prices' / (symbol + '.json')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    return {
        'symbol': symbol, 'name': name, 'country': country, 'domestic': country == '日本',
        'currency': currency, 'exchange': meta.get('fullExchangeName', meta.get('exchangeName')),
        'timezone': meta['exchangeTimezoneName'], 'source': url,
        'historyUrl': 'https://finance.yahoo.com/quote/' + symbol + '/history/',
        'retrievedAt': datetime.now(timezone.utc).isoformat(),
        'sha256': hashlib.sha256(raw).hexdigest(), 'events': result.get('events', {}),
        'historyStart': rows[0]['date'], 'lastTradingDate': rows[-1]['date'], 'rows': rows,
    }


if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=3) as pool:
        companies = list(pool.map(fetch, COMPANIES))
    output = {'provider': 'Yahoo Finance chart endpoint', 'storedFrom': START, 'end': END,
              'retrievedAt': datetime.now(timezone.utc).isoformat(), 'companies': companies}
    (BASE / 'addition-prices.json').write_text(json.dumps(output, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n')
    for company in companies:
        print(company['symbol'], len(company['rows']), company['rows'][-1])
