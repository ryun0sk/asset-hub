"""Fetch fixed-cutoff (2026-10-02) EPS/P-E histories and FX used by the valuation charts.

Raw provider responses are cached in working/fundamentals/ (Git-ignored).
All EPS rows are aligned to the same post-split share basis as the price history
(see SPLITS_NOT_IN_PROVIDER_EPS and align_split_basis)."""
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
END = "2026-10-02"
PERIOD1 = int(dt.datetime(2010, 1, 1, tzinfo=dt.timezone.utc).timestamp())
PERIOD2 = int(dt.datetime(2026, 10, 3, tzinfo=dt.timezone.utc).timestamp())
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
KIOXIA_Q1_FY2026 = {
    "periodEnd": "2026-06-30",
    "publishedDate": "2026-07-31",
    "dilutedEps": 1525.09,
    "priorYearQuarterDilutedEps": 33.75,
    "priorAnnualTtmDilutedEps": 1009.15,
    "source": "https://ssl4.eir-parts.net/doc/285A/tdnet/2859908/00.pdf",
    # Official values above are on the pre-split basis. Kioxia split 1:3
    # effective 2026-10-01 (ex-date 2026-09-29 in the price events).
    "splitRatio": 3,
}
# Splits after the previous snapshot that the provider's EPS series had not yet
# reflected at retrieval (checked 2026-10-03: Yahoo EPS still matched the
# pre-split share count, while prices were split-adjusted). All EPS rows are
# divided once by the ratio so EPS and price use the same share basis.
SPLITS_NOT_IN_PROVIDER_EPS = {
    "285A.T": {"exDate": "2026-09-29", "ratio": 3, "note": "1:3 split effective 2026-10-01"},
    "8035.T": {"exDate": "2026-09-29", "ratio": 5, "note": "1:5 split effective 2026-10-01"},
    "4062.T": {"exDate": "2026-09-29", "ratio": 2, "note": "1:2 split effective 2026-10-01"},
}
# Older splits: the provider's annual EPS is restated to the post-split basis,
# but some TTM / quarterly rows remain on the old basis. Splits whose ratio is
# at least this large are checked row by row against surrounding annual EPS.
MATERIAL_SPLIT = 1.5


def read_url(url):
    for attempt in range(5):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            return urllib.request.urlopen(request, timeout=30).read()
        except Exception:
            if attempt == 4:
                raise
            time.sleep(1.5 * (attempt + 1))


def split_events(company):
    events = []
    for value in (company.get("events") or {}).get("splits", {}).values():
        ratio = value["numerator"] / value["denominator"]
        date = dt.datetime.fromtimestamp(value["date"], dt.timezone.utc).date().isoformat()
        if max(ratio, 1 / ratio) >= MATERIAL_SPLIT:
            events.append({"exDate": date, "ratio": ratio})
    return sorted(events, key=lambda e: e["exDate"])


def _log_distance(value, low, high):
    if value <= 0 or low <= 0:
        return None
    v = math.log(value)
    lo, hi = math.log(low), math.log(high)
    return 0.0 if lo <= v <= hi else min(abs(v - lo), abs(v - hi))


def align_split_basis(annual_rows, rows, events, scale, kind):
    """Divide rows that are still on a pre-split basis.

    For each row before a split ex-date, compare the row (x scale, i.e. 4 for a
    quarter) with the surrounding restated annual EPS (within 15 months). If
    dividing by the cumulative split ratio brings it closer, divide. Rows with
    no positive annual reference are left unchanged and reported.
    """
    fixed, unchecked = [], []
    out = []
    for row in rows:
        later = [e for e in events if e["exDate"] > row["periodEnd"]]
        if not later or row["eps"] == 0:
            out.append(row)
            continue
        d = dt.date.fromisoformat(row["periodEnd"])
        refs = [abs(a["eps"]) for a in annual_rows
                if a["eps"] and abs((dt.date.fromisoformat(a["periodEnd"]) - d).days) <= 460
                and (a["eps"] > 0) == (row["eps"] > 0)]
        same_date = [abs(a["eps"]) for a in annual_rows
                     if a["periodEnd"] == row["periodEnd"] and a["eps"] and (a["eps"] > 0) == (row["eps"] > 0)]
        if same_date and scale == 1:
            refs = same_date  # a TTM row at a fiscal year end must equal that year's restated EPS
        if not refs:
            unchecked.append(row["periodEnd"])
            out.append(row)
            continue
        low, high = min(refs), max(refs)
        value = abs(row["eps"]) * scale
        best_factor, best = 1.0, _log_distance(value, low, high)
        factor = 1.0
        for event in reversed(later):
            factor *= event["ratio"]
            dist = _log_distance(value / factor, low, high)
            if dist is not None and best is not None and dist + 0.15 < best:
                best_factor, best = factor, dist
        if best_factor != 1.0:
            fixed.append({"kind": kind, "periodEnd": row["periodEnd"], "providerEps": row["eps"], "divisor": round(best_factor, 6)})
            row = {**row, "eps": round(row["eps"] / best_factor, 8)}
        out.append(row)
    return out, fixed, unchecked


def fetch_eps(company):
    symbol = company["symbol"]
    params = urllib.parse.urlencode(
        {
            "symbol": symbol,
            "type": (
                "annualDilutedEPS,annualBasicEPS,"
                "quarterlyDilutedEPS,quarterlyBasicEPS,"
                "trailingDilutedEPS,trailingBasicEPS,"
                "trailingPeRatio,trailingForwardPeRatio"
            ),
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

    def eps_rows(diluted_key, basic_key):
        diluted = series.get(diluted_key) or []
        basic = series.get(basic_key) or []
        source_rows = diluted if diluted else basic
        basis = "diluted" if diluted else "basic"
        rows = []
        for row in source_rows:
            value = row.get("reportedValue", {}).get("raw")
            date = row.get("asOfDate")
            if not date or date > END or value is None or not math.isfinite(value):
                continue
            rows.append({"periodEnd": date, "eps": round(value, 8)})
        currencies = {
            row.get("currencyCode")
            for row in source_rows
            if row.get("currencyCode") and row.get("asOfDate") <= END
        }
        return rows, basis, currencies

    def ratio_rows(key):
        rows = []
        for row in series.get(key) or []:
            value = row.get("reportedValue", {}).get("raw")
            date = row.get("asOfDate")
            if not date or date > END or value is None or not math.isfinite(value) or value <= 0:
                continue
            rows.append({"date": date, "value": round(value, 8)})
        return rows

    rows, basis, currencies = eps_rows("annualDilutedEPS", "annualBasicEPS")
    quarterly_rows, quarterly_basis, quarterly_currencies = eps_rows(
        "quarterlyDilutedEPS", "quarterlyBasicEPS"
    )
    ttm_rows, ttm_basis, ttm_currencies = eps_rows(
        "trailingDilutedEPS", "trailingBasicEPS"
    )
    trailing_pe_rows = ratio_rows("trailingPeRatio")
    forward_pe_rows = ratio_rows("trailingForwardPeRatio")
    assert len(rows) >= 2, (symbol, len(rows))
    for values in (rows, quarterly_rows, ttm_rows):
        assert len({r["periodEnd"] for r in values}) == len(values)
    currencies |= quarterly_currencies | ttm_currencies
    assert len(currencies) == 1, (symbol, currencies)
    eps_currency = currencies.pop()

    def divide_eps(values, ratio):
        return [{**row, "eps": round(row["eps"] / ratio, 8)} for row in values]

    # Yahoo had adjusted Wiwynn's price history for the 2026-09-02 stock
    # dividend at the cutoff, while its EPS series still used the old share
    # count. Apply the recorded 2.9827947:1 event once and retain the audit note.
    adjustments = []
    if symbol == "6669.TW":
        ratio = 2.9827947
        rows = divide_eps(rows, ratio)
        quarterly_rows = divide_eps(quarterly_rows, ratio)
        ttm_rows = divide_eps(ttm_rows, ratio)
        adjustments.append({
            "reason": "2026-09-02 stock dividend / split alignment",
            "ratio": ratio,
            "source": "working/prices/6669.TW.json (events.splits)",
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
    if symbol in SPLITS_NOT_IN_PROVIDER_EPS:
        split = SPLITS_NOT_IN_PROVIDER_EPS[symbol]
        rows = divide_eps(rows, split["ratio"])
        quarterly_rows = divide_eps(quarterly_rows, split["ratio"])
        ttm_rows = divide_eps(ttm_rows, split["ratio"])
        adjustments.append({
            "reason": "Split after the previous snapshot not yet reflected in provider EPS; all EPS rows divided once",
            "exDate": split["exDate"],
            "ratio": split["ratio"],
            "note": split["note"],
            "source": "working/prices/" + symbol + ".json (events.splits)",
        })
    older_events = [
        e for e in split_events(company)
        if e["exDate"] <= "2026-09-04" and not (symbol == "6669.TW" and e["exDate"] == "2026-09-02")
    ]
    if older_events:
        quarterly_rows, fixed_q, unchecked_q = align_split_basis(rows, quarterly_rows, older_events, 4, "quarterly")
        ttm_rows, fixed_t, unchecked_t = align_split_basis(rows, ttm_rows, older_events, 1, "ttm")
        if fixed_q or fixed_t:
            adjustments.append({
                "reason": "Provider TTM/quarterly rows still on a pre-split share basis; divided by the cumulative later split ratio after comparison with restated annual EPS",
                "rows": fixed_q + fixed_t,
                "uncheckedRows": sorted(set(unchecked_q + unchecked_t)),
                "source": "working/prices/" + symbol + ".json (events.splits)",
            })
    if symbol == "285A.T":
        correction = KIOXIA_Q1_FY2026
        r = correction["splitRatio"]
        ttm_eps = round(
            (correction["priorAnnualTtmDilutedEps"]
             - correction["priorYearQuarterDilutedEps"]
             + correction["dilutedEps"]) / r,
            8,
        )
        quarterly_rows = [
            row for row in quarterly_rows if row["periodEnd"] != correction["periodEnd"]
        ]
        quarterly_rows.append({
            "periodEnd": correction["periodEnd"],
            "eps": round(correction["dilutedEps"] / r, 8),
        })
        quarterly_rows.sort(key=lambda row: row["periodEnd"])
        ttm_rows = [row for row in ttm_rows if row["periodEnd"] != correction["periodEnd"]]
        ttm_rows.append({"periodEnd": correction["periodEnd"], "eps": ttm_eps})
        ttm_rows.sort(key=lambda row: row["periodEnd"])
        for ratio_row in trailing_pe_rows:
            if ratio_row["date"] < correction["publishedDate"]:
                continue
            prices = [row for row in company["rows"] if row["date"] <= ratio_row["date"]]
            if not prices:
                continue
            price = prices[-1]
            ratio_row["providerValue"] = ratio_row["value"]
            ratio_row["value"] = round(price["close"] / ttm_eps, 8)
            ratio_row["priceDate"] = price["date"]
        adjustments.append({
            "reason": "Yahoo TTM EPS lagged the FY2026 Q1 release; inserted official diluted EPS (converted to the post-1:3-split basis) and recalculated post-release trailing P/E snapshots with split-adjusted closes",
            "periodEnd": correction["periodEnd"],
            "publishedDate": correction["publishedDate"],
            "quarterlyDilutedEpsPreSplit": correction["dilutedEps"],
            "quarterlyDilutedEps": round(correction["dilutedEps"] / r, 8),
            "splitRatio": r,
            "ttmDilutedEps": ttm_eps,
            "source": correction["source"],
        })

    path = BASE / "working" / "fundamentals" / f"{symbol}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return {
        "symbol": symbol,
        "name": company["name"],
        "priceCurrency": company["currency"],
        "epsCurrency": eps_currency,
        "epsBasis": basis,
        "quarterlyEpsBasis": quarterly_basis,
        "ttmEpsBasis": ttm_basis,
        "source": url,
        "retrievedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "adjustments": adjustments,
        "rows": rows,
        "quarterlyRows": quarterly_rows,
        "ttmRows": ttm_rows,
        "trailingPeRows": trailing_pe_rows,
        "forwardPeRows": forward_pe_rows,
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
    path = BASE / "working" / "fundamentals" / f"{symbol}.json"
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
        "methodology": (
            "Annual, quarterly and trailing-twelve-month reported EPS at fiscal "
            "period end; diluted EPS, or basic EPS only when diluted is unavailable. "
            "Trailing and forward P/E ratios are provider-reported historical snapshots."
        ),
        "companies": companies,
        "fx": fx,
    }
    (BASE / "fundamentals.json").write_text(
        json.dumps(output, ensure_ascii=False, separators=(",", ":"))
    )
    print("Saved", len(companies), "companies and", len(fx), "FX series")
