#!/usr/bin/env python3
"""保存済み Yahoo Finance Chart API から SpaceX 日次終値を検査・正規化する。

ネットワーク通信は行わない。取得原文は working/raw/（Git 対象外）に置く。
価格スナップショットは 2026-06-12〜2026-10-02 固定で、再取得・更新ではない。
"""
import csv
import datetime as dt
import json
import math
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
RAW = HERE / "working/raw/yahoo-chart-SPCX.json"
SOURCE_URL = (
    "https://query1.finance.yahoo.com/v8/finance/chart/SPCX"
    "?period1=1781222400&period2=1791072000&interval=1d&events=div,splits"
)
START, END = dt.date(2026, 6, 12), dt.date(2026, 10, 2)
HOLIDAYS = {dt.date(2026, 6, 19), dt.date(2026, 7, 3), dt.date(2026, 9, 7)}
NY = ZoneInfo("America/New_York")


def main():
    raw = json.loads(RAW.read_text())
    assert raw["chart"]["error"] is None, "API returned an error"
    series = raw["chart"]["result"][0]
    meta = series["meta"]
    assert meta["symbol"] == "SPCX" and meta["currency"] == "USD"
    assert meta["instrumentType"] == "EQUITY", "Old SPCX ETF must not be used"
    assert meta["longName"] == "Space Exploration Technologies Corp."
    assert meta["fullExchangeName"] == "NasdaqGS"
    first_trade = dt.datetime.fromtimestamp(meta["firstTradeDate"], NY).date()
    assert first_trade == START, "Listing date must be SpaceX IPO, not old ETF"
    timestamps = series["timestamp"]
    quotes = series["indicators"]["quote"][0]
    adjusted = series["indicators"]["adjclose"][0]["adjclose"]
    assert all(len(v) == len(timestamps) for v in quotes.values())
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
        assert values["close"] == adjusted[index], "Unexpected dividend adjustment"
        # API の IEEE 754 表現誤差を除去。価格ヒント 2 桁に合わせる。
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
    assert not series.get("events", {}), "Unexpected split/dividend event"
    assert rows[-1] == {"date": "2026-10-02", "close": 158.96}
    fetched_at = dt.datetime.fromtimestamp(RAW.stat().st_mtime, dt.timezone.utc).isoformat().replace("+00:00", "Z")
    document = {
        "schemaVersion": 1,
        "symbol": "SPCX",
        "currency": "USD",
        "companyName": meta["longName"],
        "exchange": meta["fullExchangeName"],
        "instrumentType": meta["instrumentType"],
        "firstTradingDate": first_trade.isoformat(),
        "through": END.isoformat(),
        "fetchedAt": fetched_at,
        "dateTimezone": "America/New_York",
        "priceField": "indicators.quote[0].close",
        "priceType": "regular-session closing price",
        "priceDecimals": 2,
        "splitBasis": "2026年5月の1対5株式分割後。上場以降の実際の通常終値で、独自の遡及調整なし。",
        "sources": [
            {"label": "Yahoo Finance Chart API（日次通常終値）", "url": SOURCE_URL},
            {"label": "Nasdaq（上場会社名・証券区分の確認）", "url": "https://www.nasdaq.com/market-activity/stocks/spcx/historical"},
            {"label": "Nasdaq（2026年の取引カレンダー）", "url": "https://www.nasdaq.com/market-activity/stock-market-holiday-schedule"},
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
            "oldEtfHistoryExcluded": True,
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
            writer.writerow({**row, "close": f'{row["close"]:.2f}', "currency": "USD", "symbol": "SPCX"})
    print(f"Validated {len(rows)} sessions: {rows[0]} -> {rows[-1]}")


if __name__ == "__main__":
    main()
