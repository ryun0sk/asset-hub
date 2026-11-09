"""Fetch two public FX observations for explicit quote/EPS currency conversion."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

BASE = Path(__file__).resolve().parent
items = []
for symbol, meaning in [('EURUSD=X', 'USD per EUR'), ('HKD=X', 'HKD per USD')]:
    url = 'https://query1.finance.yahoo.com/v8/finance/chart/' + quote(symbol) + '?range=5d&interval=1d'
    raw = urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=35).read()
    meta = json.loads(raw)['chart']['result'][0]['meta']
    items.append({'symbol': symbol, 'meaning': meaning, 'rate': meta['regularMarketPrice'],
                  'time_utc': datetime.fromtimestamp(meta['regularMarketTime'], timezone.utc).isoformat(),
                  'source': url, 'retrieved_at_utc': datetime.now(timezone.utc).isoformat(),
                  'raw_sha256': hashlib.sha256(raw).hexdigest()})
    p = BASE / 'working' / 'prices' / (symbol + '.json')
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(raw)
(BASE / 'fx.json').write_text(json.dumps({'items': items, 'note': 'FX observation timestamps differ from equity closes.'}, indent=2) + '\n')
for item in items:
    print(item['meaning'], item['rate'], item['time_utc'])
