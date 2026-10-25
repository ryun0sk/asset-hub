"""Fetch public, split-adjusted daily closes; no credentials or private data."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

BASE = Path(__file__).resolve().parent
ITEMS = [
    ("285A.T", "キオクシア", "JPY"), ("6857.T", "アドバンテスト", "JPY"),
    ("TSM", "TSMC・米国ADR", "USD"), ("NVDA", "NVIDIA", "USD"),
    ("AVGO", "Broadcom", "USD"), ("ASML", "ASML・米国上場株", "USD"),
    ("VRT", "Vertiv", "USD"), ("ANET", "Arista", "USD"),
    ("TWD=X", "USD/TWD", "TWD"), ("EURUSD=X", "EUR/USD", "USD"),
    ("JPY=X", "USD/JPY", "JPY"),
]


def fetch(item):
    symbol, name, expected_currency = item
    params = {
        "period1": int(datetime(2026, 10, 9, tzinfo=timezone.utc).timestamp()),
        "period2": int(datetime(2026, 10, 18, tzinfo=timezone.utc).timestamp()),
        "interval": "1d", "events": "div,splits", "includeAdjustedClose": "true",
    }
    url = "https://query1.finance.yahoo.com/v8/finance/chart/" + quote(symbol) + "?" + urlencode(params)
    raw = urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=40).read()
    result = json.loads(raw)["chart"]["result"][0]
    meta = result["meta"]
    if meta["currency"] != expected_currency:
        raise ValueError((symbol, meta["currency"]))
    tz = ZoneInfo(meta["exchangeTimezoneName"])
    closes = result["indicators"]["quote"][0]["close"]
    adjusted = result["indicators"].get("adjclose", [{}])[0].get("adjclose", [None] * len(closes))
    rows = [{"date": datetime.fromtimestamp(t, tz).date().isoformat(),
             "close": round(c, 8), "adjusted_close": round(a, 8) if a is not None else None}
            for t, c, a in zip(result["timestamp"], closes, adjusted) if c is not None]
    rows = [r for r in rows if r["date"] <= "2026-10-16"]
    if not rows or rows[-1]["date"] != "2026-10-16":
        raise ValueError((symbol, "No Oct 16 close", rows[-1:] ))
    destination = BASE / "working" / "prices" / (symbol + ".json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(raw)
    return {"symbol": symbol, "name": name, "currency": expected_currency,
            "exchange": meta.get("fullExchangeName", meta.get("exchangeName")),
            "timezone": meta["exchangeTimezoneName"], "last": rows[-1], "rows": rows,
            "source": url, "history_url": "https://finance.yahoo.com/quote/" + quote(symbol) + "/history/",
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "raw_sha256": hashlib.sha256(raw).hexdigest(), "events": result.get("events", {})}


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(fetch, ITEMS))
    output = {"as_of": "2026-10-18 JST", "price_date": "2026-10-16",
              "provider": "Yahoo Finance public chart API",
              "price_basis": "Daily Close in local trading currency; split adjusted, not dividend adjusted. FX is provider daily close, not same-clock fixing.",
              "items": rows}
    (BASE / "prices.json").write_text(json.dumps(output, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    for row in rows:
        print(row["symbol"], row["currency"], row["last"])
