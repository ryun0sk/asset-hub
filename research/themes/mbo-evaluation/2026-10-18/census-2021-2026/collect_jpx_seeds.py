"""Save public JPX annual MBO delisting seeds, without inferring announcement years."""
from pathlib import Path
from urllib.request import Request, urlopen
import re
import json
import html
import unicodedata

ROOT = Path(__file__).resolve().parent
WORK = ROOT / 'working'
WORK.mkdir(exist_ok=True)
rows = []
for suffix in ['', 'archives-01.html', 'archives-02.html', 'archives-03.html', 'archives-04.html', 'archives-05.html']:
    url = 'https://www.jpx.co.jp/listing/stocks/delisted/' + suffix
    raw = urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=40).read()
    (WORK / (suffix or 'current.html')).write_bytes(raw)
    for tr in re.findall(r'<tr\b[^>]*>(.*?)</tr>', raw.decode('utf-8'), re.S | re.I):
        cols = [unicodedata.normalize('NFKC', html.unescape(re.sub('<[^>]+>', ' ', x))).strip()
                for x in re.findall(r'<td\b[^>]*>(.*?)</td>', tr, re.S | re.I)]
        cols = [' '.join(x.split()) for x in cols]
        if len(cols) >= 5 and 'MBO' in cols[4]:
            rows.append({'code': cols[2], 'name': cols[1], 'delisting_date': cols[0].replace('/', '-'),
                         'market': cols[3], 'reason': cols[4], 'source_url': url})
data = {'schema_version': 1, 'as_of': '2026-10-18',
        'description': '上場廃止理由MBOの探索入口。初回正式公表年・当初取引の成立はこの一覧だけでは確定しない。未来の廃止予定と2020初回案件を含む。',
        'items': rows}
(ROOT / 'jpx-delisting-seeds.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
print(len(rows), 'MBO delisting seeds')
print(json.dumps({y: sum(x['delisting_date'].startswith(str(y)) for x in rows) for y in range(2021, 2027)}))
url = 'https://www.jpx.co.jp/equities/follow-up/nlsgeu000006gevo-att/t13vrt000000njd5.pdf'
(WORK / 'jpx-mbo-2026-01-26.pdf').write_bytes(urlopen(url, timeout=40).read())
