"""Read-only public daily prices; fixed 2026-10-02 cutoff, history trimmed to START to keep index.html small. No credentials required.
Raw provider responses are cached in working/prices/ (Git-ignored)."""
from pathlib import Path
import sys
import concurrent.futures, datetime as dt, hashlib, json, math, time, urllib.parse, urllib.request
from zoneinfo import ZoneInfo
BASE=Path(__file__).resolve().parent
START='2016-01-01'; END='2026-10-02'
# Some exchanges were closed on END (local holidays). Accept a last trading day on or after this date.
MIN_LAST='2026-09-30'
COMPANIES=[
('4063.T','信越化学','日本','JPY'),('3436.T','SUMCO','日本','JPY'),('6488.TWO','GlobalWafers','台湾','TWD'),('WAF.DE','Siltronic','ドイツ','EUR'),
('8035.T','東京エレクトロン','日本','JPY'),('LRCX','Lam Research','米国','USD'),('ASML','ASML','オランダ','USD'),
('NVDA','NVIDIA','米国','USD'),('AMD','AMD','米国','USD'),('AVGO','Broadcom','米国','USD'),
('2330.TW','TSMC','台湾','TWD'),('3711.TW','ASE Technology','台湾','TWD'),('2802.T','味の素','日本','JPY'),('4062.T','イビデン','日本','JPY'),('3037.TW','Unimicron','台湾','TWD'),('6146.T','ディスコ','日本','JPY'),
('6857.T','アドバンテスト','日本','JPY'),('TER','Teradyne','米国','USD'),('000660.KS','SK hynix','韓国','KRW'),('MU','Micron','米国','USD'),('005930.KS','Samsung Electronics','韓国','KRW'),('285A.T','キオクシアHD','日本','JPY'),('SNDK','Sandisk','米国','USD'),
('6702.T','富士通','日本','JPY'),('6701.T','NEC','日本','JPY'),('DELL','Dell Technologies','米国','USD'),('HPE','Hewlett Packard Enterprise','米国','USD'),('SMCI','Super Micro Computer','米国','USD'),('0992.HK','Lenovo Group','香港','HKD'),('2382.TW','Quanta Computer','台湾','TWD'),('6669.TW','Wiwynn','台湾','TWD'),('2317.TW','Hon Hai Precision','台湾','TWD'),('ANET','Arista Networks','米国','USD'),('5803.T','フジクラ','日本','JPY'),('COHR','Coherent','米国','USD'),('LITE','Lumentum','米国','USD'),('6501.T','日立製作所','日本','JPY'),('ETN','Eaton','アイルランド登記','USD'),('VRT','Vertiv','米国','USD'),('6367.T','ダイキン工業','日本','JPY'),('AMZN','Amazon','米国','USD'),('GOOGL','Alphabet','米国','USD'),('AAPL','Apple','米国','USD')]

def fetch(item):
 symbol,name,country,currency=item
 params={'period1':int(dt.datetime(1900,1,1,tzinfo=dt.timezone.utc).timestamp()),'period2':int(dt.datetime(2026,10,3,tzinfo=dt.timezone.utc).timestamp()),'interval':'1d','events':'div,splits','includeAdjustedClose':'true'}
 url='https://query1.finance.yahoo.com/v8/finance/chart/'+urllib.parse.quote(symbol)+'?'+urllib.parse.urlencode(params)
 raw=None
 cached=BASE/'working'/'prices'/(symbol+'.json')
 if '--from-cache' in sys.argv: raw=cached.read_bytes()
 for attempt in range(3):
  if raw is not None: break
  try:
   raw=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=30).read(); break
  except Exception:
   if attempt==2: raise
   time.sleep(2)
 parsed=json.loads(raw); result=parsed['chart']['result'][0]; meta=result['meta']
 assert meta['symbol']==symbol,(symbol,meta['symbol'])
 assert meta['currency']==currency,(symbol,meta['currency'])
 zone=ZoneInfo(meta['exchangeTimezoneName']); ts=result['timestamp']; close=result['indicators']['quote'][0]['close']; adj=result['indicators']['adjclose'][0]['adjclose']
 rows=[]; invalid_adjusted=[]
 for stamp,c,a in zip(ts,close,adj):
  date=dt.datetime.fromtimestamp(stamp,zone).date().isoformat()
  if not START<=date<=END or c is None or a is None: continue
  assert math.isfinite(c) and c>0,(symbol,date,'invalid close',c)
  if not math.isfinite(a) or a<=0:
   invalid_adjusted.append(date);a=None
  rows.append({'date':date,'close':round(c,6),'adjusted':round(a,6) if a is not None else None})
 assert len(rows)>100,(symbol,len(rows))
 assert len({r['date'] for r in rows})==len(rows)
 assert MIN_LAST<=rows[-1]['date']<=END,(symbol,rows[-1])
 path=BASE/'working'/'prices'/(symbol+'.json'); path.parent.mkdir(parents=True,exist_ok=True)
 if '--from-cache' not in sys.argv: path.write_bytes(raw)
 return {'symbol':symbol,'name':name,'country':country,'domestic':country=='日本','currency':currency,'exchange':meta.get('fullExchangeName',meta['exchangeName']),'timezone':meta['exchangeTimezoneName'],'providerName':meta.get('longName',meta.get('shortName')),'source':url,'historyUrl':'https://finance.yahoo.com/quote/'+symbol+'/history/','retrievedAt':dt.datetime.fromtimestamp(path.stat().st_mtime,dt.timezone.utc).isoformat(),'invalidAdjustedDates':invalid_adjusted,'sha256':hashlib.sha256(raw).hexdigest(),'events':result.get('events',{}),'historyStart':rows[0]['date'],'lastTradingDate':rows[-1]['date'],'providerFirstTradeDate':meta.get('firstTradeDate'),'rows':rows}

if __name__=='__main__':
 data=[]; errors=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  jobs={pool.submit(fetch,c):c[0] for c in COMPANIES}
  for job in concurrent.futures.as_completed(jobs):
   symbol=jobs[job]
   try:
    r=job.result(); data.append(r); print(symbol,len(r['rows']),r['rows'][-1],flush=True)
   except Exception as e: errors.append((symbol,str(e)));print('ERROR',symbol,str(e),flush=True)
 if errors: raise SystemExit(json.dumps(errors,ensure_ascii=False))
 order={c[0]:i for i,c in enumerate(COMPANIES)};data.sort(key=lambda c:order[c['symbol']])
 output={'provider':'Yahoo Finance chart endpoint','storedFrom':START,'start':min(c['rows'][0]['date'] for c in data),'end':END,'retrievedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'companies':data}
 (BASE/'prices.json').write_text(json.dumps(output,ensure_ascii=False,separators=(',',':')))
 print('Saved',len(data),'companies')
