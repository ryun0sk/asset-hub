#!/usr/bin/env python3
"""保存済み Yahoo Finance Chart API から Tesla 日次終値を検査・正規化する。

ネットワーク通信は行わない。取得原文は working/raw/（Git 対象外）に置く。
価格スナップショットは 2025-10-03〜2026-10-02 固定で、再取得・更新ではない。
"""
import csv
import datetime as dt
import json
import math
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
RAW = HERE / "working/raw/yahoo-chart-TSLA.json"
SOURCE_URL = (
    "https://query1.finance.yahoo.com/v8/finance/chart/TSLA"
    "?period1=1759449600&period2=1791072000&interval=1d&events=div,splits"
)
START, END = dt.date(2025, 10, 3), dt.date(2026, 10, 2)
HOLIDAYS = {
    dt.date(2025, 11, 27), dt.date(2025, 12, 25),
    dt.date(2026, 1, 1), dt.date(2026, 1, 19), dt.date(2026, 2, 16),
    dt.date(2026, 4, 3), dt.date(2026, 5, 25), dt.date(2026, 6, 19),
    dt.date(2026, 7, 3), dt.date(2026, 9, 7),
}
EARLY_CLOSES = {dt.date(2025, 11, 28), dt.date(2025, 12, 24)}
NY = ZoneInfo("America/New_York")


def main():
    raw = json.loads(RAW.read_text())
    assert raw["chart"]["error"] is None, "API returned an error"
    series = raw["chart"]["result"][0]
    meta = series["meta"]
    assert meta["symbol"] == "TSLA" and meta["currency"] == "USD"
    assert meta["instrumentType"] == "EQUITY"
    assert meta["longName"] == "Tesla, Inc."
    assert meta["fullExchangeName"] == "NasdaqGS"
    first_trade = dt.datetime.fromtimestamp(meta["firstTradeDate"], NY).date()
    assert first_trade == dt.date(2010, 6, 29), "Listing date does not match Tesla IPO"
    timestamps = series["timestamp"]
    quotes = series["indicators"]["quote"][0]
    adjusted = series["indicators"]["adjclose"][0]["adjclose"]
    assert all(len(values) == len(timestamps) for values in quotes.values())
    assert len(adjusted) == len(timestamps)
    rows = []
    for index, timestamp in enumerate(timestamps):
        date = dt.datetime.fromtimestamp(timestamp, NY).date()
        assert START <= date <= END, "Out-of-snapshot date"
        values = {field: values[index] for field, values in quotes.items()}
        assert all(value is not None and math.isfinite(value) for value in values.values())
        assert all(values[field] > 0 for field in ("open", "high", "low", "close"))
        assert values["low"] <= values["open"] <= values["high"]
        assert values["low"] <= values["close"] <= values["high"]
        assert values["volume"] >= 0
        assert values["close"] == adjusted[index], "Unexpected adjusted-close difference"
        rows.append({"date": date.isoformat(), "close": round(values["close"], 2)})
    assert rows == sorted(rows, key=lambda row: row["date"])
    assert len({row["date"] for row in rows}) == len(rows), "Duplicate date"
    expected = set()
    day = START
    while day <= END:
        if day.weekday() < 5 and day not in HOLIDAYS:
            expected.add(day.isoformat())
        day += dt.timedelta(days=1)
    observed = {row["date"] for row in rows}
    assert expected == observed, f"Missing or extra session: {expected ^ observed}"
    assert {day.isoformat() for day in EARLY_CLOSES} <= observed
    assert not series.get("events", {}), "Unexpected split/dividend event"
    assert len(rows) == 251
    assert rows[-1] == {"date": "2026-10-02", "close": 370.59}
    fetched_at = dt.datetime.fromtimestamp(RAW.stat().st_mtime, dt.timezone.utc).isoformat().replace("+00:00", "Z")
    document = {
        "schemaVersion": 1,
        "symbol": "TSLA",
        "currency": "USD",
        "companyName": meta["longName"],
        "exchange": meta["fullExchangeName"],
        "instrumentType": meta["instrumentType"],
        "firstTradingDate": first_trade.isoformat(),
        "from": START.isoformat(),
        "through": END.isoformat(),
        "fetchedAt": fetched_at,
        "dateTimezone": "America/New_York",
        "priceField": "indicators.quote[0].close",
        "priceType": "regular-session closing price",
        "priceDecimals": 2,
        "splitBasis": "2020年の1対5分割・2022年の1対3分割後。取得期間の実際の通常終値で、独自の遡及調整なし。",
        "sources": [
            {"label": "Yahoo Finance Chart API（日次通常終値）", "url": SOURCE_URL},
            {"label": "Tesla IR（IPO日と上場銘柄の確認）", "url": "https://ir.tesla.com/press-release/tesla-announces-pricing-initial-public-offering"},
            {"label": "Nasdaq（2025年の取引カレンダー）", "url": "https://www.nasdaqtrader.com/content/technicalsupport/2025tradingcalendar.pdf"},
            {"label": "Nasdaq（2026年の取引カレンダー）", "url": "https://www.nasdaq.com/market-activity/stock-market-holiday-schedule"},
            {"label": "Nasdaq Dorsey Wright（10月2日終値の照合）", "url": "https://dorseywright.nasdaq.com/chart/performance/symbol/TSLA"},
        ],
        "validation": {
            "rowCount": len(rows),
            "expectedTradingDayCount": len(expected),
            "missingTradingDates": [],
            "unexpectedDates": [],
            "duplicateDates": [],
            "nullPrices": 0,
            "allOhlcRowsConsistent": True,
            "closeEqualsAdjustedClose": True,
            "eventsInPeriod": {},
            "excludedMarketHolidays": sorted(day.isoformat() for day in HOLIDAYS),
            "includedEarlyCloseDates": sorted(day.isoformat() for day in EARLY_CLOSES),
            "lastCloseCrossChecked": {"date": "2026-10-02", "close": 370.59},
        },
        "rows": rows,
    }
    folder = HERE / "sources"
    folder.mkdir(exist_ok=True)
    (folder / "price-history.json").write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n")
    with (folder / "price-history.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["date", "close", "currency", "symbol"], lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "close": f'{row["close"]:.2f}', "currency": "USD", "symbol": "TSLA"})
    changes = [
        {"date": current["date"], "pct": (current["close"] / previous["close"] - 1) * 100}
        for previous, current in zip(rows, rows[1:])
    ]
    print(f"Validated {len(rows)} sessions: {rows[0]} -> {rows[-1]}")
    print(f"Highest close: {max(rows, key=lambda row: row['close'])}; lowest close: {min(rows, key=lambda row: row['close'])}")
    print(f"Largest increase: {max(changes, key=lambda row: row['pct'])}; largest decline: {min(changes, key=lambda row: row['pct'])}")


if __name__ == "__main__":
    main()
