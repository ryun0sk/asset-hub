"""Fetch fixed-cutoff annual EPS and the FX series needed for reference P/E charts."""
from pathlib import Path
import concurrent.futures
import datetime as dt
import hashlib
import json
import math
import time
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

BASE = Path(__file__).resolve().parent
END = "2026-09-04"
PERIOD1 = int(dt.datetime(2010, 1, 1, tzinfo=dt.timezone.utc).timestamp())
PERIOD2 = int(dt.datetime(2026, 9, 5, tzinfo=dt.timezone.utc).timestamp())
FUND_URL = "https://query1.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/"
CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/"
FX_PAIRS = [
    ("EURUSD=X", "EUR", "USD"),
    ("HKD=X", "USD", "HKD"),
]
MISSING_ANNUAL_EPS = {
    "8035.T": {
        "periodEnd": "2025-03-31",
        "eps": 1179.08,
        "source": "https://www.tel.com/ir/irta3a00000006g5-att/fy25q4tanshin-e.pdf",
    },
    "0992.HK": {
        "periodEnd": "2025-03-31",
        "eps": 0.1062,
        "source": "https://investor.lenovo.com/en/financial/five_year_summary.php",
    },
    "6367.T": {
        "periodEnd": "2025-03-31",
        "eps": 903.65,
        "source": "https://www.daikin.com/-/media/DB861448CF134980AE6819F941132C7D.ashx",
    },
}


def read_url(url):
    for attempt in range(5):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            return urllib.request.urlopen(request, timeout=30).read()
        except Exception:
            if attempt == 4:
                raise
            time.sleep(1.5 * (attempt + 1))


def fetch_eps(company):
    symbol = company["symbol"]
    params = urllib.parse.urlencode(
        {
            "symbol": symbol,
            "type": "annualDilutedEPS,annualBasicEPS",
            "period1": PERIOD1,
            "period2": PERIOD2,
        },
        safe=",",
    )
    url = FUND_URL + urllib.parse.quote(symbol) + "?" + params
    raw = read_url(url)
    parsed = json.loads(raw)["timeseries"]
    assert parsed.get("error") is None, (symbol, parsed.get("error"))
    series = {}
    for result in parsed.get("result") or []:
        kind = result["meta"]["type"][0]
        series[kind] = result.get(kind, [])
    diluted = series.get("annualDilutedEPS") or []
    basic = series.get("annualBasicEPS") or []
    source_rows = diluted if diluted else basic
    basis = "diluted" if diluted else "basic"
    rows = []
    for row in source_rows:
        value = row.get("reportedValue", {}).get("raw")
        date = row.get("asOfDate")
        if not date or date > END or value is None or not math.isfinite(value):
            continue
        rows.append({"periodEnd": date, "eps": round(value, 8)})
    assert len(rows) >= 2, (symbol, len(rows))
    assert len({r["periodEnd"] for r in rows}) == len(rows)
    currencies = {
        row.get("currencyCode")
        for row in source_rows
        if row.get("currencyCode") and row.get("asOfDate") <= END
    }
    assert len(currencies) == 1, (symbol, currencies)
    eps_currency = currencies.pop()

    # Yahoo had adjusted Wiwynn's price history for the 2026-09-02 stock
    # dividend at the cutoff, while its EPS series still used the old share
    # count. Apply the recorded 2.9827947:1 event once and retain the audit note.
    adjustments = []
    if symbol == "6669.TW":
        ratio = 2.9827947
        rows = [{**row, "eps": round(row["eps"] / ratio, 8)} for row in rows]
        adjustments.append({
            "reason": "2026-09-02 stock dividend / split alignment",
            "ratio": ratio,
            "source": "sources/prices/6669.TW.json",
        })
    if symbol in MISSING_ANNUAL_EPS:
        addition = MISSING_ANNUAL_EPS[symbol]
        rows.append({"periodEnd": addition["periodEnd"], "eps": addition["eps"]})
        rows.sort(key=lambda row: row["periodEnd"])
        adjustments.append({
            "reason": "Yahoo series omitted one fiscal year; inserted reported diluted EPS",
            "periodEnd": addition["periodEnd"],
            "source": addition["source"],
        })

    path = BASE / "sources" / "fundamentals" / f"{symbol}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return {
        "symbol": symbol,
        "name": company["name"],
        "priceCurrency": company["currency"],
        "epsCurrency": eps_currency,
        "epsBasis": basis,
        "source": url,
        "retrievedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "adjustments": adjustments,
        "rows": rows,
    }


def fetch_fx(item):
    symbol, source_currency, target_currency = item
    params = urllib.parse.urlencode(
        {
            "period1": PERIOD1,
            "period2": PERIOD2,
            "interval": "1d",
            "events": "div,splits",
            "includeAdjustedClose": "true",
        }
    )
    url = CHART_URL + urllib.parse.quote(symbol) + "?" + params
    raw = read_url(url)
    result = json.loads(raw)["chart"]["result"][0]
    zone = ZoneInfo(result["meta"]["exchangeTimezoneName"])
    values = result["indicators"]["quote"][0]["close"]
    rows = []
    for stamp, value in zip(result["timestamp"], values):
        date = dt.datetime.fromtimestamp(stamp, zone).date().isoformat()
        if date <= END and value is not None and math.isfinite(value) and value > 0:
            rows.append({"date": date, "rate": round(value, 8)})
    assert rows and rows[-1]["date"] == END, (symbol, rows[-1] if rows else None)
    path = BASE / "sources" / "fundamentals" / f"{symbol}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return {
        "symbol": symbol,
        "sourceCurrency": source_currency,
        "targetCurrency": target_currency,
        "source": url,
        "retrievedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "rows": rows,
    }


if __name__ == "__main__":
    prices = json.loads((BASE / "prices.json").read_text())
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        companies = list(pool.map(fetch_eps, prices["companies"]))
        fx = list(pool.map(fetch_fx, FX_PAIRS))
    output = {
        "provider": "Yahoo Finance fundamentals-timeseries and chart endpoints",
        "end": END,
        "retrievedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        "methodology": "Annual reported EPS at fiscal period end; diluted EPS, or basic EPS only when diluted is unavailable.",
        "companies": companies,
        "fx": fx,
    }
    (BASE / "fundamentals.json").write_text(
        json.dumps(output, ensure_ascii=False, separators=(",", ":"))
    )
    print("Saved", len(companies), "companies and", len(fx), "FX series")
