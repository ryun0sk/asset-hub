"""Read public Yahoo chart data for the fixed 46-company research universe."""
from concurrent.futures import ThreadPoolExecutor
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

BASE = Path(__file__).resolve().parent
ITEMS = json.loads((BASE / 'universe.json').read_text())
CUTOFF = datetime.now(timezone.utc)
PARSER = argparse.ArgumentParser()
PARSER.add_argument('--symbols', default='')
PARSER.add_argument('--output', default='prices.json')
PARSER.add_argument('--raw-directory', default='prices')
ARGS = PARSER.parse_args()
if Path(ARGS.output).name != ARGS.output or Path(ARGS.raw_directory).name != ARGS.raw_directory:
    raise ValueError('output and raw-directory must be simple names')
if ARGS.symbols:
    requested = set(ARGS.symbols.split(','))
    ITEMS = [item for item in ITEMS if item['symbol'] in requested]
    if {item['symbol'] for item in ITEMS} != requested:
        raise ValueError('unknown symbols')

def fetch(item):
    symbol = item['symbol']
    params = {'period1': int(datetime(2026, 10, 15, tzinfo=timezone.utc).timestamp()),
              'period2': int(CUTOFF.timestamp()), 'interval': '1d',
              'events': 'div,splits', 'includeAdjustedClose': 'true'}
    url = 'https://query1.finance.yahoo.com/v8/finance/chart/' + quote(symbol) + '?' + urlencode(params)
    try:
        raw = urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=35).read()
        result = json.loads(raw)['chart']['result'][0]
        meta = result['meta']
        if meta['currency'] != item['currency']:
            raise ValueError('currency mismatch: ' + str(meta.get('currency')))
        tz = ZoneInfo(meta['exchangeTimezoneName'])
        rows = [{'date': datetime.fromtimestamp(t, tz).date().isoformat(), 'close': c}
                for t, c in zip(result['timestamp'], result['indicators']['quote'][0]['close'])
                if c is not None and t <= CUTOFF.timestamp()]
        completed = [r for r in rows if r['date'] <= '2026-11-05']
        if not completed:
            raise ValueError('no completed daily prices')
        market_time = datetime.fromtimestamp(meta['regularMarketTime'], timezone.utc)
        current = {'price': meta['regularMarketPrice'], 'time_utc': market_time.isoformat(),
                   'time_local': market_time.astimezone(tz).isoformat(),
                   'kind': 'provider regular-market observation, may be delayed or intraday'}
        if market_time > CUTOFF:
            current = None
        destination = BASE / 'working' / ARGS.raw_directory / (symbol + '.json')
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
        old_day = [r for r in rows if r['date'] == '2026-10-16']
        return {**item, 'status': 'ok', 'current': current, 'last_completed': completed[-1],
                'oct16_on_current_split_basis': old_day[-1] if old_day else None,
                'history': rows, 'events': result.get('events', {}),
                'source': url, 'history_url': 'https://finance.yahoo.com/quote/' + quote(symbol) + '/history/',
                'retrieved_at_utc': datetime.now(timezone.utc).isoformat(),
                'raw_sha256': hashlib.sha256(raw).hexdigest()}
    except Exception as error:
        return {**item, 'status': 'failed', 'error': str(error), 'source': url}

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(fetch, ITEMS))
    output = {'as_of': '2026-11-06 JST', 'cutoff_utc': CUTOFF.isoformat(),
              'provider': 'Yahoo Finance public chart API; no credentials',
              'basis': 'Local currency. Current observation and completed daily close are distinct. Daily closes split-adjusted, not dividend-adjusted.',
              'items': rows}
    (BASE / ARGS.output).write_text(json.dumps(output, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    for row in rows:
        print(row['symbol'], row['status'], row.get('current'), row.get('last_completed'), row.get('error', ''))
