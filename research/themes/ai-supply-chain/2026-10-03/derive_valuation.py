"""Derive valuation.json for the 2026-10-03 AI supply-chain dashboard ("EPS・PER" view).

Standard library only. No network access: every number comes from data already saved in the repo.

Inputs (read only)
  - prices.json, fundamentals.json (this folder): daily closes to 2026-10-02 and split-aligned EPS.
  - ../../ai-business-quality/2026-10-04/working/yahoo-trend-<symbol>.json: analyst EPS averages
    (Yahoo Finance quoteSummary earningsTrend, retrieved 2026-10-04). working/ is not tracked by Git,
    so the extracted values are kept in valuation.json together with each file's SHA-256.
  - ../../ai-year-end-comparison/2026-10-03/compare.py: FORECAST_EPS (company forecasts, read with ast).
  - Confirmed earnings dates: transcribed below from ai-year-end-comparison/2026-10-03/report.md section 3
    and research/companies/*/2026-10-03/stock-drivers.md.

Method
  - TTM EPS series = annual EPS (12 months to fiscal year end) merged with provider TTM rows; on the same
    period end the TTM row wins. Each value is treated as known from period end + 45 days (an assumption;
    the provider does not store announcement dates) unless fundamentals.json records the publication date
    (Kioxia FY2026 Q1: 2026-07-31). A value older than 460 days (period end to the price date) is not used.
  - Daily trailing P/E = close / (latest known TTM EPS converted to the price currency with the
    fundamentals.json FX rate of that day). Loss (TTM <= 0) or no usable TTM -> null (line breaks).
  - Price change decomposition (computed in the page for the selected dates; presets stored here for
    checking): ln(P1/P0) = ln(E1/E0) + ln(PE1/PE0), where E is the implied EPS (price / P/E) of that day.

Usage (from the repo root or this folder)
  python3 derive_valuation.py           # write valuation.json
  python3 derive_valuation.py --check   # exit 1 unless the saved valuation.json matches a fresh derivation
"""
import ast
import bisect
import datetime as dt
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
THEMES = BASE.parents[1]
REPO = BASE.parents[3]
TREND_DIR = THEMES / "ai-business-quality" / "2026-10-04" / "working"
COMPARE_PY = THEMES / "ai-year-end-comparison" / "2026-10-03" / "compare.py"
OUTPUT = BASE / "valuation.json"

KNOWN_LAG_DAYS = 45
MAX_AGE_DAYS = 460
PRESETS = {"ytd": "2026-01-01", "1y": "2025-10-02", "3y": "2023-10-02"}

# Company forecast periods and announcement dates for FORECAST_EPS (from the note in compare.py and the
# cited reports). Fujikura: photonics/2026-10-03/report.md (2026-08-07 Q1 release).
FORECAST_META = {
    "6857.T": ("2027-03-31", "2026-07-29"),
    "4062.T": ("2027-03-31", "2026-08-04"),
    "6920.T": ("2027-06-30", "2026-08-06"),
    "4063.T": ("2027-03-31", "2026-07-24"),
    "6501.T": ("2027-03-31", "2026-07-29"),
    "5803.T": ("2027-03-31", "2026-08-07"),
    "5801.T": ("2027-03-31", None),
    "5802.T": ("2027-03-31", None),
}

# Next earnings dates confirmed in primary sources (company IR calendars etc.) as listed in
# ai-year-end-comparison/2026-10-03/report.md section 3. Anything not listed is shown as 未確認.
REPORT3 = "ai-year-end-comparison/2026-10-03/report.md 第3節"
NEXT_EARNINGS = {
    "ASML": ("2026-10-14", "日本時間14:00", "7〜9月期決算", REPORT3 + "（会社）"),
    "2330.TW": ("2026-10-15", "日本時間15:00〜", "7〜9月期決算", REPORT3 + "（TSMC IR）"),
    "LRCX": ("2026-10-21", "米国時間（日本時間10/22朝）", "決算", REPORT3 + "（会社）"),
    "6146.T": ("2026-10-22", "16:00", "Q2決算", REPORT3 + "（会社IRカレンダー）"),
    "4063.T": ("2026-10-27", "15:30", "Q2決算", REPORT3 + "（会社IRカレンダー）"),
    "6857.T": ("2026-10-28", "15:30", "Q2決算", "companies/6857-advantest/2026-10-03/stock-drivers.md（会社IRカレンダー）"),
    "6501.T": ("2026-10-28", "時刻未確認", "Q2決算", REPORT3 + "（会社IRサイト）"),
    "4062.T": ("2026-10-29", "15:20", "Q2決算", "companies/4062-ibiden/2026-10-03/stock-drivers.md（会社IRカレンダー）"),
    "SNDK": ("2026-10-29", "米国時間（日本時間10/30朝）", "決算", REPORT3 + "（会社 9/29）"),
    "8035.T": ("2026-10-30", "時刻未確認", "Q2決算（通期予想を初めて開示）", REPORT3 + "（会社）"),
    "285A.T": ("2026-10-30", "18:45", "Q2決算", "companies/285A-kioxia/2026-10-03/stock-drivers.md（会社）"),
}

# Provider period labels that disagree with the values (see ai-business-quality/2026-10-04/report.md 3-1):
# Micron's "0y" ending 2026-08-31 carries FY2027 values (FY2026 GAAP EPS 74.33 was already reported).
RELABEL = {
    "MU": {"quarterMonths": 3, "yearYears": 1,
           "note": "提供元の期末日表示は1期前（0y=2026-08-31）だが、FY2026実績（GAAP 74.33ドル、9/30発表）とFY27 Q1会社予想（38.15ドル）との水準から、今期＝FY2027（2027-08期）・来期＝FY2028とみなした【独自】（ai-business-quality 2026-10-04 report.md 3-1と同じ扱い）"},
}

# Japanese companies without a full-year company forecast in FORECAST_EPS (report.md 2-1 notes 1, 2, 6).
FORECAST_NONE = {
    "285A.T": "通期の会社予想なし（四半期ごとの予想のみ）",
    "8035.T": "通期予想は10/30のQ2決算で初めて開示",
    "6146.T": "会社予想は1四半期先まで（通期なし）",
}

# Known lags in the provider TTM series that this derivation deliberately does not patch.
TTM_NOTES = {
    "MU": "TTMが1四半期遅れ：提供元のTTMは2026年5月期（44.24ドル）で止まり、9/30発表の6〜8月期を含まない。公式FY2026 GAAP EPS 74.33ドルなら実績PER約14.5倍（参考・report.md）",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path):
    return path.resolve().relative_to(REPO).as_posix()


def day(s):
    return dt.date.fromisoformat(s)


def add_months(s, months):
    d = day(s)
    y, m = divmod(d.month - 1 + months, 12)
    y += d.year
    m += 1
    # keep month-end dates at month end
    nxt = dt.date(y + (m == 12), m % 12 + 1, 1)
    last = (nxt - dt.timedelta(days=1)).day
    is_end = (d + dt.timedelta(days=1)).month != d.month
    return dt.date(y, m, last if is_end else min(d.day, last)).isoformat()


def r(x, nd=6):
    return None if x is None else round(x, nd)


def load_forecasts():
    tree = ast.parse(COMPARE_PY.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "FORECAST_EPS" for t in node.targets):
            return ast.literal_eval(node.value)
    raise SystemExit("FORECAST_EPS not found in compare.py")


class FxTable:
    def __init__(self, fx):
        self.tables = {}
        for item in fx:
            rows = item["rows"]
            self.tables[(item["sourceCurrency"], item["targetCurrency"])] = ([x["date"] for x in rows], [x["rate"] for x in rows], item)

    def rate(self, src, dst, date):
        if src == dst:
            return 1.0
        if (src, dst) in self.tables:
            dates, rates, _ = self.tables[(src, dst)]
            i = bisect.bisect_right(dates, date) - 1
            return rates[i] if i >= 0 else None
        if (dst, src) in self.tables:
            v = self.rate(dst, src, date)
            return None if v is None else 1 / v
        return None

    def symbol(self, src, dst):
        item = self.tables.get((src, dst)) or self.tables.get((dst, src))
        return item[2]["symbol"] if item else None


def ttm_series(f):
    merged = {}
    for row in f.get("rows", []):
        merged[row["periodEnd"]] = (row["eps"], "annual")
    for row in f.get("ttmRows", []):
        merged[row["periodEnd"]] = (row["eps"], "ttm")
    published = {a["periodEnd"]: a["publishedDate"] for a in f.get("adjustments", []) if a.get("periodEnd") and a.get("publishedDate")}
    out = []
    for pe, (eps, src) in sorted(merged.items()):
        known = published.get(pe) or (day(pe) + dt.timedelta(days=KNOWN_LAG_DAYS)).isoformat()
        out.append({"periodEnd": pe, "knownFrom": known, "eps": r(eps, 8), "source": src, **({"publishedDate": published[pe]} if pe in published else {})})
    out.sort(key=lambda x: (x["knownFrom"], x["periodEnd"]))
    return out


def known_ttm(series, date):
    """Latest TTM row known on `date` and not older than MAX_AGE_DAYS; None otherwise."""
    best = None
    for row in series:
        if row["knownFrom"] <= date and (best is None or row["periodEnd"] >= best["periodEnd"]):
            best = row
    if best is None or (day(date) - day(best["periodEnd"])).days > MAX_AGE_DAYS:
        return None
    return best


def quantile(sorted_vals, q):
    if not sorted_vals:
        return None
    pos = (len(sorted_vals) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (pos - lo)


def decompose(rows, pes, start, end):
    """Each company's first trading day >= start and last <= end, using the stored daily P/E."""
    idx = [i for i, row in enumerate(rows) if start <= row["date"] <= end]
    if len(idx) < 2:
        return {"status": "noprice"}
    i0, i1 = idx[0], idx[-1]
    p0, p1, e0, e1 = rows[i0]["close"], rows[i1]["close"], pes[i0], pes[i1]
    out = {"startDate": rows[i0]["date"], "endDate": rows[i1]["date"], "priceStart": p0, "priceEnd": p1, "priceChange": r(p1 / p0 - 1, 8)}
    if e0 is None or e1 is None:
        out["status"] = "unavailable"
        return out
    ln_p, ln_pe = math.log(p1 / p0), math.log(e1 / e0)
    ln_e = ln_p - ln_pe
    out.update(status="ok", peStart=r(e0, 6), peEnd=r(e1, 6), lnPrice=r(ln_p, 10), lnEps=r(ln_e, 10), lnPe=r(ln_pe, 10),
               epsChange=r(math.exp(ln_e) - 1, 8), peChange=r(e1 / e0 - 1, 8))
    return out


def analyst_block(symbol, eps_currency, price, price_currency, fx, asof):
    path = TREND_DIR / f"yahoo-trend-{symbol}.json"
    if not path.exists():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    trend = raw["quoteSummary"]["result"][0]["earningsTrend"]["trend"]
    relabel = RELABEL.get(symbol)
    periods = {}
    currency = None
    for t in trend:
        if t.get("period") not in ("0q", "+1q", "0y", "+1y"):
            continue
        ee, et, rv = t.get("earningsEstimate", {}), t.get("epsTrend", {}), t.get("epsRevisions", {})
        val = lambda d, k: (d.get(k) or {}).get("raw")  # noqa: E731
        end = t.get("endDate")
        if relabel and end:
            end = add_months(end, relabel["quarterMonths"]) if t["period"].endswith("q") else add_months(end, 12 * relabel["yearYears"])
        currency = currency or ee.get("earningsCurrency")
        avg, cur, d90 = val(ee, "avg"), val(et, "current"), val(et, "90daysAgo")
        periods[t["period"]] = {
            "endDate": end, "providerEndDate": t.get("endDate"), "avg": avg, "low": val(ee, "low"), "high": val(ee, "high"),
            "analysts": val(ee, "numberOfAnalysts"), "yearAgoEps": val(ee, "yearAgoEps"),
            "trendCurrent": cur, "trend30daysAgo": val(et, "30daysAgo"), "trend90daysAgo": d90,
            "up30": val(rv, "upLast30days"), "down30": val(rv, "downLast30days"),
            "change90": r(cur / d90 - 1, 8) if cur and d90 else None,
        }
    currency = currency or eps_currency
    rate = fx.rate(currency, price_currency, asof)
    for key in ("0y", "+1y"):
        p = periods.get(key)
        if p and p["avg"]:
            p["avgPriceCurrency"] = r(p["avg"] * rate, 8)
            p["pe"] = r(price / (p["avg"] * rate), 6) if p["avg"] > 0 else None
    y0, y1 = periods.get("0y", {}).get("avg"), periods.get("+1y", {}).get("avg")
    return {
        "retrievedAt": raw.get("_retrieved"), "url": raw.get("_url"), "file": rel(path), "sha256": sha256(path),
        "currency": currency, "fxToPrice": None if currency == price_currency else {"rate": rate, "date": asof, "symbol": fx.symbol(currency, price_currency)},
        "periods": periods, "nextYearGrowth": r(y1 / y0 - 1, 8) if y0 and y1 and y0 > 0 else None,
        "relabelNote": relabel["note"] if relabel else None,
    }


def derive():
    prices = json.loads((BASE / "prices.json").read_text(encoding="utf-8"))
    fund = json.loads((BASE / "fundamentals.json").read_text(encoding="utf-8"))
    fx = FxTable(fund["fx"])
    forecasts = load_forecasts()
    pc = {c["symbol"]: c for c in prices["companies"]}
    companies = []
    for f in fund["companies"]:
        s = f["symbol"]
        p = pc[s]
        rows = p["rows"]
        series = ttm_series(f)
        pcur, ecur = f["priceCurrency"], f["epsCurrency"]
        assert pcur == p["currency"], s
        pes = []
        for row in rows:
            t = known_ttm(series, row["date"])
            if t is None or t["eps"] <= 0:
                pes.append(None)
                continue
            rate = fx.rate(ecur, pcur, row["date"])
            pes.append(row["close"] / (t["eps"] * rate))
        first = next((i for i, v in enumerate(pes) if v is not None), None)
        finite = sorted(v for v in pes if v is not None)
        stats = None
        if finite:
            stats = {"days": len(finite), "from": rows[first]["date"], "to": rows[max(i for i, v in enumerate(pes) if v is not None)]["date"],
                     "median": r(statistics.median(finite), 6), "p10": r(quantile(finite, 0.1), 6), "p90": r(quantile(finite, 0.9), 6),
                     "min": r(finite[0], 6), "max": r(finite[-1], 6)}
        last = rows[-1]
        t = known_ttm(series, last["date"])
        rate = fx.rate(ecur, pcur, last["date"])
        status = "none" if t is None else ("loss" if t["eps"] <= 0 else "ok")
        notes = []
        if s in TTM_NOTES:
            notes.append(TTM_NOTES[s])
        if t is not None:
            later_q = [q["periodEnd"] for q in f.get("quarterlyRows", []) if q["periodEnd"] > t["periodEnd"]]
            if later_q and s not in TTM_NOTES:
                notes.append(f"提供元のTTMは{t['periodEnd']}期まで（四半期EPSは{max(later_q)}期まで保存。TTMは未更新）")
            if t.get("publishedDate"):
                notes.append(f"TTMは公式の{t['periodEnd']}期の希薄化後EPSを反映（{t['publishedDate']}公表、fundamentals.jsonの補正）")
        if ecur != pcur:
            notes.append(f"EPSは{ecur}建て。{fx.symbol(ecur, pcur)}の当日レートで{pcur}に換算してPERを計算")
        snapshot = {
            "date": last["date"], "close": last["close"], "status": status,
            "ttmEps": None if t is None else t["eps"], "ttmPeriodEnd": None if t is None else t["periodEnd"],
            "ttmKnownFrom": None if t is None else t["knownFrom"], "ttmSource": None if t is None else t["source"],
            "ttmEpsPriceCurrency": None if t is None else r(t["eps"] * rate, 8), "fxRate": None if ecur == pcur else rate,
            "pe": r(pes[-1], 6), "notes": notes,
        }
        cf = None
        if s in forecasts:
            eps, label = forecasts[s]
            period_end, announced = FORECAST_META[s]
            cf = {"eps": eps, "periodEnd": period_end, "announced": announced, "label": label, "source": rel(COMPARE_PY) + " FORECAST_EPS",
                  "pe": r(last["close"] / eps, 6)}
        ne = NEXT_EARNINGS.get(s)
        companies.append({
            "symbol": s, "name": f["name"], "priceCurrency": pcur, "epsCurrency": ecur,
            "ttmSeries": series,
            "pe": {"from": rows[first]["date"] if first is not None else None,
                   "values": [r(v, 4) for v in pes[first:]] if first is not None else []},
            "peStats": stats, "snapshot": snapshot,
            "analyst": analyst_block(s, ecur, last["close"], pcur, fx, last["date"]),
            "companyForecast": cf, "companyForecastNote": FORECAST_NONE.get(s),
            "nextEarnings": {"status": "confirmed", "date": ne[0], "time": ne[1], "event": ne[2], "source": ne[3]} if ne else {"status": "unconfirmed"},
            "quarterly": [{"periodEnd": q["periodEnd"], "eps": q["eps"]} for q in f.get("quarterlyRows", [])],
            "annual": [{"periodEnd": a["periodEnd"], "eps": a["eps"]} for a in f.get("rows", [])],
            "decompositionPresets": {k: decompose(rows, pes, v, prices["end"]) for k, v in PRESETS.items()},
        })
    retrieved = sorted(c["analyst"]["retrievedAt"] for c in companies if c["analyst"])
    unused = sorted(k for k in forecasts if k not in pc)
    return {
        "schema": 1,
        "generatedBy": rel(Path(__file__)),
        "asOf": prices["end"],
        "method": {
            "knownLagDays": KNOWN_LAG_DAYS, "maxAgeDays": MAX_AGE_DAYS,
            "ttm": "年次EPS（期末までの12か月）と提供元TTMを期末日で統合（同じ期末はTTMを優先）。期末＋45日から既知とみなす（公表日の記録がある場合はその日）。期末から460日を超えたTTMは使わない。",
            "pe": "日次終値÷その日に既知の最新TTM EPS（EPS通貨が株価と異なる場合はfundamentals.jsonの当日為替で換算）。TTMが0以下・未取得の日はnull。",
            "decomposition": "ln(株価終点/始点)=ln(EPS終点/始点)+ln(PER終点/始点)。EPSは各日の株価÷PER（＝その日に既知のTTM、株価通貨換算後）。",
            "analyst": "Yahoo Finance quoteSummary earningsTrendの平均（2026-10-04取得）。海外株の多くは調整後（Non-GAAP）EPSで、実績TTM（GAAP希薄化後）と基準が異なる場合がある。",
            "companyForecast": "compare.py FORECAST_EPS（分割後、出所注記付き）。43社に含まれない" + "・".join(unused) + "はこのダッシュボードでは表示しない。",
            "presets": PRESETS,
        },
        "analystRetrieved": {"from": retrieved[0], "to": retrieved[-1], "count": len(retrieved)} if retrieved else None,
        "inputs": [{"path": rel(BASE / "prices.json"), "sha256": sha256(BASE / "prices.json")},
                   {"path": rel(BASE / "fundamentals.json"), "sha256": sha256(BASE / "fundamentals.json")},
                   {"path": rel(COMPARE_PY), "sha256": sha256(COMPARE_PY)}],
        "companies": companies,
    }


def main():
    data = derive()
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n"
    if "--check" in sys.argv[1:]:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if current != text:
            print("valuation.json is out of date (run derive_valuation.py)")
            sys.exit(1)
        print("valuation.json is up to date")
        return
    OUTPUT.write_text(text, encoding="utf-8")
    k = next(c for c in data["companies"] if c["symbol"] == "285A.T")["snapshot"]
    print(f"Wrote {OUTPUT.name}: {len(text.encode())} bytes, {len(data['companies'])} companies, "
          f"{sum(1 for c in data['companies'] if c['analyst'])} with analyst estimates; 285A.T PER {k['pe']:.2f} ({k['close']}/{k['ttmEps']:.2f})")


if __name__ == "__main__":
    main()
