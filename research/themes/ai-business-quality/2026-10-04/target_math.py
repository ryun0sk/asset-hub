#!/usr/bin/env python3
"""AI関連銘柄 ビジネスモデルの強さと目標達成の条件（2026-10-04）の再現用計算。

標準ライブラリのみ。Yahoo Finance公開エンドポイント（APIキー不要）から次を取得し working/ に保存する。
  - chart（分割調整済み日足、10年。上場が新しい銘柄は上場以降）→ working/yahoo-chart-<symbol>-10y.json
  - fundamentals-timeseries（売上・利益・CF・負債・現金・株数）  → working/yahoo-fin-<symbol>.json
  - quoteSummary earningsTrend（アナリスト予想EPSの平均）     → working/yahoo-trend-<symbol>.json
    ※ quoteSummary は一時的なセッションcrumbが必要。crumb・cookieは保存しない。

計算内容（すべて【独自計算】。将来の予測や投資助言ではない）
  1. 財務の要約（採点の「財務の健全性」「収益の安定性」の補助）：売上の年次推移と最悪の前年比、
     営業利益率の最小・最大、純現金（現金＋短期投資−有利子負債、直近四半期）、FCF率、設備投資/売上、
     株主還元/FCF、希薄化後平均株式数の変化
  2. 目標（2027-12-30までに株価2倍）の必要条件：
     - PERが不変なら1株利益（EPS）も2倍が必要
     - 各EPS（実績TTM・会社予想・提供元予想PERからの逆算・アナリスト平均の今期/来期）について、
       「株価2倍時のPER＝2×現在株価÷EPS」と、現在の同じEPS基準のPERとの比
  3. 過去10年の「15か月で株価2倍」：分割調整済みの終値で、各取引日を起点に15か月後（暦月。該当日がなければ
     その日以前で直近の取引日）の終値が2倍以上になった起点の割合と、連続する起点をまとめた「回数（局面）」。
     現地通貨と円建て（海外株は同じ日以前で直近の為替で換算）の両方
  4. 2〜3銘柄の均等配分（買い持ち、リバランスなし）で全体+100%に必要な各銘柄の上昇率の機械的な整理と、
     過去の15か月窓で均等配分が+100%以上になった割合（全組み合わせの分布。特定の組み合わせは出さない）
  5. scores.json（事業の採点）がある場合：合計点と、ボラティリティ・PER・予想EPS成長率・過去の2倍達成率との順位相関

使い方:
  python3 target_math.py            # 取得して計算（取得データは working/ に保存）
  python3 target_math.py --offline  # working/ の保存データだけで再計算
出力は標準出力と、同じフォルダの target-math-output.txt・working/target-math-results.json。
"""
import argparse
import bisect
import datetime as dt
import http.cookiejar
import itertools
import json
import math
import os
import statistics
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "working")
OUT_TXT = os.path.join(HERE, "target-math-output.txt")
OUT_JSON = os.path.join(WORK, "target-math-results.json")
SCORES = os.path.join(HERE, "scores.json")

AS_OF = "2026-10-02"          # 直近取引日（株価の基準日）
TARGET_DAY = "2027-12-30"     # 目標の期日（2027年の大納会想定）
HIST_START = "2016-10-03"     # 過去の検証の起点（10年）
TARGET_MULT = 2.0             # 1,000万円→2,000万円
BUDGET = 10_000_000

# (コード, 名前, サブテーマ, 地域, 為替)。サブテーマは既存の比較レポートと同じ分類
UNIVERSE = [
    ("285A.T", "キオクシア", "メモリー", "日本", None),
    ("6857.T", "アドバンテスト", "装置・テスト", "日本", None),
    ("8035.T", "東京エレクトロン", "装置・テスト", "日本", None),
    ("6146.T", "ディスコ", "装置・テスト", "日本", None),
    ("6920.T", "レーザーテック", "装置・テスト", "日本", None),
    ("4062.T", "イビデン", "基板・素材", "日本", None),
    ("4063.T", "信越化学", "基板・素材", "日本", None),
    ("5803.T", "フジクラ", "光・電線", "日本", None),
    ("5801.T", "古河電工", "光・電線", "日本", None),
    ("5802.T", "住友電工", "光・電線", "日本", None),
    ("9984.T", "ソフトバンクG", "投資会社", "日本", None),
    ("6501.T", "日立", "電力・インフラ", "日本", None),
    ("NVDA", "NVIDIA", "設計（GPU・ASIC）", "海外", "JPY=X"),
    ("AVGO", "Broadcom", "設計（GPU・ASIC）", "海外", "JPY=X"),
    ("AMD", "AMD", "設計（GPU・ASIC）", "海外", "JPY=X"),
    ("2330.TW", "TSMC", "受託製造", "海外", "TWDJPY=X"),
    ("MU", "Micron", "メモリー", "海外", "JPY=X"),
    ("000660.KS", "SK hynix", "メモリー", "海外", "KRWJPY=X"),
    ("SNDK", "Sandisk", "メモリー", "海外", "JPY=X"),
    ("ASML", "ASML（米ADR）", "装置・テスト", "海外", "JPY=X"),
    ("LITE", "Lumentum", "光・電線", "海外", "JPY=X"),
    ("VRT", "Vertiv", "電力・インフラ", "海外", "JPY=X"),
]
SYMS = [u[0] for u in UNIVERSE]
NAME = {u[0]: u[1] for u in UNIVERSE}
GROUP = {u[0]: u[2] for u in UNIVERSE}
REGION = {u[0]: u[3] for u in UNIVERSE}
FXOF = {u[0]: u[4] for u in UNIVERSE}
FXS = ["JPY=X", "TWDJPY=X", "KRWJPY=X", "EURUSD=X"]

# ---- 既存の比較レポート（../../ai-year-end-comparison/2026-10-03/report.md 第2-1節）と同じ値 ----
# 実績EPS（TTMまたは直近通期、希薄化後、分割後、現地通貨。ASMLはユーロ建て）
TTM_EPS = {
    "285A.T": 833.50, "6857.T": 515.15, "8035.T": 250.18, "6146.T": 1245.90, "6920.T": 862.26,
    "4062.T": 107.46, "4063.T": 252.49, "5803.T": 94.93, "5801.T": 103.02, "5802.T": 118.44,
    "9984.T": 872.47, "6501.T": 176.63, "NVDA": 7.91, "AVGO": 7.84, "AMD": 3.90, "2330.TW": 85.49,
    "MU": 74.33, "000660.KS": 227575.0, "SNDK": 73.76, "ASML": 25.41, "LITE": -92.96, "VRT": 4.42,
}
EPS_EUR = {"ASML"}  # EPSがユーロ建て（ADRはドル建て、1ADR＝1株）
# 会社予想EPS（今期、分割後）【会社予想】
FORECAST_EPS = {
    "6857.T": (911.64, "2027年3月期（7/29上方修正）"),
    "4062.T": (149.68, "2027年3月期（8/4上方修正）"),
    "6920.T": (1004.12, "2027年6月期（8/6決算短信）"),
    "4063.T": (286.00, "2027年3月期（7/24）"),
    "6501.T": (201.14, "2027年3月期（7/29上方修正）"),
    "5803.T": (196.88, "2027年3月期（8/7）"),
    "5801.T": (149.25, "2027年3月期（8/6）"),
    "5802.T": (108.99, "2027年3月期（7/31）"),
}
# 予想PER（提供元のスナップショット 2026-09-17〜23）【外部予想ベース】
FWD_PER_PROVIDER = {
    "285A.T": 5.8, "6857.T": 35.8, "8035.T": 31.6, "6146.T": 30.9, "4063.T": 18.7, "6501.T": 24.7,
    "NVDA": 24.9, "AVGO": 19.4, "AMD": 39.5, "2330.TW": 18.6, "MU": 7.0, "000660.KS": 3.9,
    "SNDK": 8.0, "ASML": 28.9, "LITE": 42.9, "VRT": 27.8,
}
# 時価総額（兆円、10/2終値×期末株式数×為替）。純現金の比率の分母
MCAP_TRN_YEN = {
    "285A.T": 31.62, "6857.T": 28.03, "8035.T": 27.52, "6146.T": 6.54, "6920.T": 4.13, "4062.T": 6.76,
    "4063.T": 11.20, "5803.T": 9.27, "5801.T": 3.12, "5802.T": 7.65, "9984.T": 35.96, "6501.T": 24.85,
    "NVDA": 892.16, "AVGO": 267.76, "AMD": 163.38, "2330.TW": 321.25, "MU": 191.72, "000660.KS": 153.23,
    "SNDK": 39.66, "ASML": 113.27, "LITE": 15.19, "VRT": 15.33,
}
# アナリスト平均の期の注記（提供元の表示する期末日と値の水準が合わない銘柄）
TREND_NOTES = {
    "MU": "提供元の今期の期末表示は2026-08-31だが、FY2026（2026-09-03終了）の実績GAAP EPSは74.33ドル、FY27 Q1の会社予想は38.15ドル/四半期で、"
          "値の水準からみて「今期」はFY2027（2027年8月期）、「来期」はFY2028とみられる",
}
# 10/1効力の株式分割（1対3・1対5・1対2）。アナリスト予想EPSが分割前の基準のままなら補正する
PENDING_SPLIT = {"285A.T": 3.0, "8035.T": 5.0, "4062.T": 2.0}

FIN_TYPES = [
    "annualTotalRevenue", "annualGrossProfit", "annualOperatingIncome", "annualNetIncome",
    "annualOperatingCashFlow", "annualCapitalExpenditure", "annualFreeCashFlow",
    "annualRepurchaseOfCapitalStock", "annualCashDividendsPaid", "annualTotalDebt",
    "annualCashCashEquivalentsAndShortTermInvestments", "annualDilutedAverageShares", "annualStockholdersEquity",
    "quarterlyTotalDebt", "quarterlyCashCashEquivalentsAndShortTermInvestments",
    "quarterlyTotalRevenue", "quarterlyOperatingIncome", "quarterlyGrossProfit",
]

UA = {"User-Agent": "Mozilla/5.0"}


def fpath(sym, kind):
    safe = sym.replace("^", "_").replace("=", "_")
    return os.path.join(WORK, {"chart": "yahoo-chart-%s-10y.json", "fin": "yahoo-fin-%s.json",
                               "trend": "yahoo-trend-%s.json"}[kind] % safe)


def save(path, d, url):
    d["_retrieved"] = dt.datetime.now(dt.timezone.utc).isoformat()
    d["_url"] = url
    with open(path, "w") as f:
        json.dump(d, f)


def fetch_all(syms):
    os.makedirs(WORK, exist_ok=True)
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    def get(url):
        with op.open(urllib.request.Request(url, headers=UA), timeout=30) as r:
            return json.load(r)

    for s in syms + FXS:
        url = ("https://query1.finance.yahoo.com/v8/finance/chart/%s?range=10y&interval=1d&events=div%%2Csplits"
               % urllib.parse.quote(s))
        save(fpath(s, "chart"), get(url), url)
        time.sleep(0.4)
    for s in syms:
        url = ("https://query1.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/%s?symbol=%s"
               "&type=%s&period1=1262304000&period2=1790985600"
               % (urllib.parse.quote(s), urllib.parse.quote(s), ",".join(FIN_TYPES)))
        save(fpath(s, "fin"), get(url), url)
        time.sleep(0.4)
    # earningsTrend：セッションのcookieとcrumbを取得（保存しない）
    try:
        op.open(urllib.request.Request("https://fc.yahoo.com", headers=UA), timeout=30)
    except Exception:
        pass  # 404でもcookieは付与される
    with op.open(urllib.request.Request("https://query1.finance.yahoo.com/v1/test/getcrumb", headers=UA), timeout=30) as r:
        crumb = r.read().decode()
    for s in syms:
        base = "https://query1.finance.yahoo.com/v10/finance/quoteSummary/%s?modules=earningsTrend" % urllib.parse.quote(s)
        d = get(base + "&crumb=" + urllib.parse.quote(crumb))
        save(fpath(s, "trend"), d, base + "&crumb=<session>")
        time.sleep(0.4)


def load_chart(sym):
    with open(fpath(sym, "chart")) as f:
        d = json.load(f)
    r = d["chart"]["result"][0]
    off = r["meta"].get("gmtoffset", 0)
    q = r["indicators"]["quote"][0]
    rows = {}
    for i, t in enumerate(r["timestamp"]):
        c = q["close"][i]
        if c is None:
            continue
        day = dt.datetime.fromtimestamp(t + off, dt.timezone.utc).date().isoformat()
        if day > AS_OF:
            continue
        if sym == "KRWJPY=X" and c > 1:
            c /= 100.0  # 提供元の一部期間が100ウォン当たりの値で記録されているため1ウォン当たりにそろえる
        rows[day] = c
    return dict(sorted(rows.items())), d.get("_retrieved")


def load_fin(sym):
    with open(fpath(sym, "fin")) as f:
        d = json.load(f)
    out = {}
    for r in d["timeseries"]["result"]:
        t = r["meta"]["type"][0]
        vals = [(x["asOfDate"], x["reportedValue"]["raw"]) for x in (r.get(t) or []) if x]
        out[t] = sorted(vals)
    return out


def load_trend(sym):
    try:
        with open(fpath(sym, "trend")) as f:
            d = json.load(f)
        trend = d["quoteSummary"]["result"][0]["earningsTrend"]["trend"]
    except Exception:
        return {}
    out = {}
    for t in trend:
        e = t.get("earningsEstimate") or {}
        avg = (e.get("avg") or {}).get("raw")
        if avg is None:
            continue
        out[t["period"]] = {"end": t.get("endDate"), "eps": avg, "n": (e.get("numberOfAnalysts") or {}).get("raw"),
                            "ccy": e.get("earningsCurrency"),
                            "rev": ((t.get("revenueEstimate") or {}).get("avg") or {}).get("raw")}
    return out


def add_months(d, m):
    y, mo = d.year + (d.month - 1 + m) // 12, (d.month - 1 + m) % 12 + 1
    for day in (d.day, 30, 29, 28):
        try:
            return dt.date(y, mo, day)
        except ValueError:
            continue


def on_or_before(days, rows, d):
    i = bisect.bisect_right(days, d) - 1
    return rows[days[i]] if i >= 0 else None


def pct(v, nd=1):
    return "—" if v is None else ("%+." + str(nd) + "f%%") % (v * 100)


def num(v, nd=1):
    return "—" if v is None else ("%." + str(nd) + "f") % v


def spearman(x, y):
    pairs = [(a, b) for a, b in zip(x, y) if a is not None and b is not None]
    if len(pairs) < 4:
        return None, len(pairs)

    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(v):
            j = i
            while j + 1 < len(v) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2 + 1
            i = j + 1
        return r
    a, b = ranks([p[0] for p in pairs]), ranks([p[1] for p in pairs])
    ma, mb = statistics.mean(a), statistics.mean(b)
    cov = sum((p - ma) * (q - mb) for p, q in zip(a, b))
    va = math.sqrt(sum((p - ma) ** 2 for p in a))
    vb = math.sqrt(sum((q - mb) ** 2 for q in b))
    return cov / (va * vb), len(pairs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="working/ の保存データだけで再計算")
    args = ap.parse_args()
    if not args.offline:
        fetch_all(SYMS)

    lines = []

    def p(s=""):
        lines.append(s)

    res = {"asOf": AS_OF, "targetDay": TARGET_DAY, "histStart": HIST_START}
    charts, retrieved = {}, {}
    for s in SYMS + FXS:
        charts[s], retrieved[s] = load_chart(s)
    res["retrieved"] = retrieved
    fxdays = {fx: list(charts[fx].keys()) for fx in FXS}

    def to_yen(s, day, v):
        fx = FXOF[s]
        if fx is None:
            return v
        r = on_or_before(fxdays[fx], charts[fx], day)
        return None if r is None else v * r

    usdjpy = charts["JPY=X"][max(charts["JPY=X"])]
    eurusd = charts["EURUSD=X"][max(charts["EURUSD=X"])]
    fx_last = {"JPY=X": usdjpy, "TWDJPY=X": charts["TWDJPY=X"][max(charts["TWDJPY=X"])],
               "KRWJPY=X": charts["KRWJPY=X"][max(charts["KRWJPY=X"])], "EURUSD=X": eurusd}
    res["fxLast"] = fx_last

    p("AI関連銘柄 ビジネスモデルの強さと目標達成の条件（2026-10-04）— 計算出力【独自計算】")
    p("株価基準日 %s（各市場の終値、分割調整後）。目標期日 %s。過去の検証は %s 以降の日足。" % (AS_OF, TARGET_DAY, HIST_START))
    p("出所：Yahoo Finance公開エンドポイント（chart・fundamentals-timeseries・quoteSummary earningsTrend）。将来の予測・投資助言ではない。")
    p()

    # ------------------------------------------------------------------ 1. 財務の要約
    p("=" * 100)
    p("1. 財務の要約（提供元の年次・四半期データ。現地通貨。会計基準・期末は銘柄ごとに異なる）")
    p("   列：年次の期間｜売上の最悪前年比｜営業利益率 最小〜最大（最新）｜純現金（直近四半期、億円換算）と時価総額比｜FCF率｜設備投資/売上｜株主還元/FCF｜希薄化後株数の変化")
    p("-" * 100)
    fin_res = {}
    for s in SYMS:
        f = load_fin(s)
        rev = dict(f.get("annualTotalRevenue", []))
        opi = dict(f.get("annualOperatingIncome", []))
        years = sorted(rev)
        yoy = [rev[b] / rev[a] - 1 for a, b in zip(years, years[1:]) if rev[a]]
        opm = [opi[y] / rev[y] for y in years if y in opi and rev[y]]
        fcf = dict(f.get("annualFreeCashFlow", []))
        capex = dict(f.get("annualCapitalExpenditure", []))
        buy = dict(f.get("annualRepurchaseOfCapitalStock", []))
        div = dict(f.get("annualCashDividendsPaid", []))
        sh = dict(f.get("annualDilutedAverageShares", []))
        ly = years[-1] if years else None
        qd = f.get("quarterlyTotalDebt", []) or f.get("annualTotalDebt", [])
        qc = (f.get("quarterlyCashCashEquivalentsAndShortTermInvestments", [])
              or f.get("annualCashCashEquivalentsAndShortTermInvestments", []))
        netcash, ncday = None, None
        if qc:
            ncday = qc[-1][0]
            debt = dict(qd).get(ncday)
            if debt is None and qd:
                debt = qd[-1][1]
            netcash = qc[-1][1] - (debt or 0.0)
        # 円換算（億円）。ASMLはユーロ
        if netcash is not None:
            if s in EPS_EUR:
                ny = netcash * eurusd * usdjpy
            elif FXOF[s]:
                ny = netcash * fx_last[FXOF[s]]
            else:
                ny = netcash
            nc_oku = ny / 1e8
            nc_ratio = ny / (MCAP_TRN_YEN[s] * 1e12)
        else:
            nc_oku = nc_ratio = None
        fcfm = fcf.get(ly) / rev[ly] if ly in fcf and rev.get(ly) else None
        capr = -capex.get(ly) / rev[ly] if ly in capex and rev.get(ly) else None
        ret = None
        if ly in fcf and fcf[ly] and fcf[ly] > 0:
            ret = (-(buy.get(ly) or 0) - (div.get(ly) or 0)) / fcf[ly]
        shy = sorted(sh)
        shchg = (sh[shy[-1]] / sh[shy[0]] - 1) if len(shy) >= 2 and sh[shy[0]] else None
        fin_res[s] = {"years": [years[0], ly] if years else None, "worstYoY": min(yoy) if yoy else None,
                      "opmMin": min(opm) if opm else None, "opmMax": max(opm) if opm else None,
                      "opmLast": opm[-1] if opm else None, "netCashOku": nc_oku, "netCashDay": ncday,
                      "netCashToMcap": nc_ratio, "fcfMargin": fcfm, "capexToRev": capr, "returnToFcf": ret,
                      "dilutedSharesChg": shchg, "shareYears": [shy[0], shy[-1]] if len(shy) >= 2 else None,
                      "revenueByYear": {y: rev[y] for y in years}}
        p("%-14s %s〜%s｜最悪前年比 %s｜営業利益率 %s〜%s（最新 %s）｜純現金 %s億円（%s、時価総額の%s）｜FCF率 %s｜設備投資/売上 %s｜還元/FCF %s｜株数 %s（%s→%s）" % (
            NAME[s], years[0][:7] if years else "—", ly[:7] if ly else "—", pct(fin_res[s]["worstYoY"]),
            pct(fin_res[s]["opmMin"]), pct(fin_res[s]["opmMax"]), pct(fin_res[s]["opmLast"]),
            "—" if nc_oku is None else "{:,.0f}".format(nc_oku), ncday or "—", pct(nc_ratio),
            pct(fcfm), pct(capr), pct(ret, 0), pct(shchg),
            shy[0][:4] if len(shy) >= 2 else "—", shy[-1][:4] if len(shy) >= 2 else "—"))
    res["financials"] = fin_res
    p("注：純現金＝現金・現金同等物・短期投資−有利子負債（提供元の定義。リース負債の扱いは銘柄で異なる）。ソフトバンクGは通信子会社を含む連結値で、会社の示すLTVとは別物。")
    p()

    # ------------------------------------------------------------------ 2. 必要条件
    p("=" * 100)
    p("2. 目標の必要条件：%s までに株価2倍（現地通貨。円建てでは為替の変化が加わる）" % TARGET_DAY)
    p("   PERが不変なら、どのEPS基準でもEPSが2倍（+100%）必要。以下は「EPSが各予想どおりの場合に、2倍の株価が意味するPER」。")
    p("   列：現在株価｜EPS基準｜EPS｜現在のPER｜2倍時のPER（＝2×現在株価÷EPS）")
    p("-" * 100)
    req = {}
    trends = {s: load_trend(s) for s in SYMS}
    for s in SYMS:
        px = charts[s][AS_OF] if AS_OF in charts[s] else charts[s][max(charts[s])]
        conv = eurusd if s in EPS_EUR else 1.0  # ユーロEPS→ドル
        bases = []
        if TTM_EPS.get(s) is not None:
            bases.append(("実績（TTM/直近通期）", TTM_EPS[s] * conv, "実績"))
        if s in FORECAST_EPS:
            bases.append(("会社予想 " + FORECAST_EPS[s][1], FORECAST_EPS[s][0], "会社予想"))
        if s in FWD_PER_PROVIDER:
            bases.append(("提供元予想PERから逆算（9/17〜23）", px / FWD_PER_PROVIDER[s], "外部予想"))
        tr = trends.get(s, {})
        notes = []
        adj0y = None
        for per_key, lab in (("0y", "アナリスト平均・今期"), ("+1y", "アナリスト平均・来期")):
            t = tr.get(per_key)
            if not t:
                continue
            eps = t["eps"]
            if t.get("ccy") == "EUR" and s in EPS_EUR:
                eps *= eurusd
            # 10/1分割の未反映を検出：参照EPS（今期は会社予想→提供元逆算→実績、来期は今期の平均）の0.8×分割比を超えれば分割前基準とみて補正
            if s in PENDING_SPLIT and eps > 0:
                if per_key == "0y":
                    ref = (FORECAST_EPS[s][0] if s in FORECAST_EPS else
                           (px / FWD_PER_PROVIDER[s] if s in FWD_PER_PROVIDER else TTM_EPS[s]))
                else:
                    ref = adj0y
                if ref and eps / ref > 0.8 * PENDING_SPLIT[s]:
                    eps /= PENDING_SPLIT[s]
                    notes.append("%sのアナリスト平均EPSは分割前基準とみて÷%g" % (per_key, PENDING_SPLIT[s]))
            if per_key == "0y":
                adj0y = eps
            bases.append(("%s（期末%s、%s人）" % (lab, t["end"], t["n"]), eps, "外部予想"))
        rows = []
        for lab, eps, kind in bases:
            cur = px / eps if eps and eps > 0 else None
            need = TARGET_MULT * px / eps if eps and eps > 0 else None
            rows.append({"basis": lab, "kind": kind, "eps": eps, "perNow": cur, "perAtTarget": need})
        g = None
        e0 = [r["eps"] for r in rows if r["basis"].startswith("アナリスト平均・今期")]
        e1 = [r["eps"] for r in rows if r["basis"].startswith("アナリスト平均・来期")]
        if e0 and e1 and e0[0] > 0:
            g = e1[0] / e0[0] - 1
        req[s] = {"price": px, "rows": rows, "consensusGrowthNextYear": g, "notes": notes,
                  "trend": tr}
        p("%s（%s）：株価 %s" % (NAME[s], s, "{:,.2f}".format(px)))
        for r in rows:
            p("   %-46s EPS %12s｜現在PER %6s｜2倍時PER %6s" % (
                r["basis"], "{:,.2f}".format(r["eps"]), num(r["perNow"]), num(r["perAtTarget"])))
        if g is not None:
            p("   来期/今期のアナリスト平均EPSの伸び %s → 今期平均EPS基準のPERが不変なら株価は同率。残りをPERの上昇で賄う場合の必要倍率 %.2f倍" % (pct(g), 2 / (1 + g)))
        if s in TREND_NOTES:
            notes.append(TREND_NOTES[s])
        for n in notes:
            p("   注：" + n)
    res["requirements"] = req
    p("注：海外株のアナリスト平均は多くが調整後（Non-GAAP）EPSで、実績TTM（GAAP）とは定義が異なる。ASMLはユーロEPSを直近のユーロドルでドル換算。")
    p()

    # ------------------------------------------------------------------ 3. 過去の15か月2倍
    p("=" * 100)
    p("3. 過去の「15か月で株価2倍」（起点 %s 以降、15か月後の終値÷起点の終値 ≥ 2）" % HIST_START)
    p("   局面：条件を満たす起点が20営業日以内の間隔で続く範囲を1回と数える。割合は全起点に占める比率（将来の確率ではない）。")
    p("-" * 100)
    hist = {}
    ret15 = {}   # 円建ての15か月リターン（起点日→値）
    for s in SYMS:
        rows = charts[s]
        out = {}
        for cur in ("local", "yen"):
            if cur == "yen" and FXOF[s] is None:
                out["yen"] = out["local"]
                continue
            series = {}
            for d in rows:
                v = rows[d] if cur == "local" else to_yen(s, d, rows[d])
                if v is not None:
                    series[d] = v
            sd = list(series.keys())
            idx = {d: i for i, d in enumerate(sd)}
            r15 = {}
            for d in sd:
                if d < HIST_START:
                    continue
                end = add_months(dt.date.fromisoformat(d), 15).isoformat()
                if end > AS_OF:
                    break
                r15[d] = on_or_before(sd, series, end) / series[d] - 1
            hits = [d for d in r15 if r15[d] >= TARGET_MULT - 1]
            eps_ = []
            for d in hits:
                if eps_ and idx[d] - idx[eps_[-1]["last"]] <= 20:
                    eps_[-1]["last"] = d
                    eps_[-1]["max"] = max(eps_[-1]["max"], r15[d])
                    eps_[-1]["n"] += 1
                else:
                    eps_.append({"first": d, "last": d, "max": r15[d], "n": 1})
            for e in eps_:
                e["endFirst"] = add_months(dt.date.fromisoformat(e["first"]), 15).isoformat()
                e["endLast"] = add_months(dt.date.fromisoformat(e["last"]), 15).isoformat()
            vals = list(r15.values())
            out[cur] = {"nStarts": len(r15), "firstStart": min(r15) if r15 else None,
                        "lastStart": max(r15) if r15 else None, "nHit": len(hits),
                        "share": len(hits) / len(r15) if r15 else None, "episodes": eps_,
                        "sharePre2024H2": (lambda pre: (sum(1 for d in pre if r15[d] >= TARGET_MULT - 1) / len(pre)) if pre else None)(
                            [d for d in r15 if d < "2024-07-01"]),
                        "median": statistics.median(vals) if vals else None,
                        "max": max(vals) if vals else None, "min": min(vals) if vals else None,
                        "shareGE": {str(k): (sum(1 for v in vals if v >= k) / len(vals) if vals else None)
                                    for k in (0.0, 0.5, 1.0, 2.0, 3.0)}}
            if cur == "yen" or FXOF[s] is None:
                ret15[s] = r15
        hist[s] = out
        o, y = out["local"], out["yen"]
        p("%s：起点 %s〜%s（%d日）｜2倍の割合 現地 %s・円 %s｜局面 現地 %d回・円 %d回｜15か月リターン 中央値 %s・最大 %s・最小 %s（円）" % (
            NAME[s], o["firstStart"] or "—", o["lastStart"] or "—", o["nStarts"], pct(o["share"]), pct(y["share"]),
            len(o["episodes"]), len(y["episodes"]), pct(y["median"], 0), pct(y["max"], 0), pct(y["min"], 0)))
        for e in o["episodes"]:
            p("     現地：起点 %s〜%s（終点 %s〜%s、%d日、最大 %s）" % (
                e["first"], e["last"], e["endFirst"], e["endLast"], e["n"], pct(e["max"], 0)))
    res["history15m"] = hist
    p()
    p("参考：起点を2024-06以前に限った場合の2倍の割合（円建て。直近のAI・メモリー相場の起点を除く）")
    for s in SYMS:
        v = hist[s]["yen"].get("sharePre2024H2")
        p("   %-14s %s" % (NAME[s], pct(v)))
    p()
    p("15か月リターンの分布（円建て、全起点に占める割合）：≥0%｜≥+50%｜≥+100%｜≥+200%｜≥+300%")
    for s in SYMS:
        g = hist[s]["yen"]["shareGE"]
        p("   %-14s %s｜%s｜%s｜%s｜%s（起点%d日）" % (NAME[s], pct(g["0.0"], 0), pct(g["0.5"], 0), pct(g["1.0"], 0),
                                              pct(g["2.0"], 0), pct(g["3.0"], 0), hist[s]["yen"]["nStarts"]))
    p()

    # ------------------------------------------------------------------ 4. 均等配分の算術
    p("=" * 100)
    p("4. 2〜3銘柄の均等配分（買い持ち）で全体+100%に必要な上昇率（算術）")
    p("   全体の倍率＝各銘柄の倍率の平均。2銘柄なら上昇率の合計が+200%、3銘柄なら+300%で全体+100%。")
    p("-" * 100)
    p("   2銘柄：Aの上昇率 → Bに必要な上昇率")
    for a in (-0.5, -0.3, 0.0, 0.5, 1.0, 1.5, 2.0):
        p("     A %s → B %s" % (pct(a, 0), pct(2.0 - a, 0)))
    p("   3銘柄：A・Bの上昇率 → Cに必要な上昇率")
    for a, b in ((0.0, 0.0), (-0.3, 0.5), (0.5, 0.5), (1.0, 1.0), (0.3, 0.3), (-0.5, 0.0), (2.0, 0.0)):
        p("     A %s・B %s → C %s" % (pct(a, 0), pct(b, 0), pct(3.0 - a - b, 0)))
    p("   1銘柄が−50%の場合：2銘柄なら残り1銘柄に+250%、3銘柄なら残り2銘柄に平均+175%が必要。")
    p()
    # 全組み合わせの過去の達成率（円建て、全銘柄に共通の起点のみ）
    long_syms = [s for s in SYMS if hist[s]["yen"]["firstStart"] and hist[s]["yen"]["firstStart"] <= "2021-10-04"]
    short_syms = [s for s in SYMS if s not in long_syms]
    p("   過去の15か月窓で均等配分が+100%%以上になった割合（円建て）。起点が2021-10以前からある%d銘柄の組み合わせ。" % len(long_syms))
    p("   対象外（上場が新しく窓が少ない）：%s" % "、".join(NAME[s] for s in short_syms))
    combo_stats = {}
    for k in (2, 3):
        shares, ever = [], 0
        for c in itertools.combinations(long_syms, k):
            common = set(ret15[c[0]])
            for s in c[1:]:
                common &= set(ret15[s])
            if not common:
                continue
            hit = sum(1 for d in common if statistics.mean(ret15[s][d] for s in c) >= 1.0)
            sh = hit / len(common)
            shares.append(sh)
            ever += 1 if hit else 0
        shares.sort()
        combo_stats[k] = {"n": len(shares), "everHit": ever, "median": statistics.median(shares),
                          "p25": shares[len(shares) // 4], "p75": shares[3 * len(shares) // 4], "zero": sum(1 for x in shares if x == 0)}
        p("     %d銘柄：%d通り｜一度でも達成 %d通り｜達成した窓の割合 中央値 %s（四分位 %s〜%s）｜一度も達成なし %d通り" % (
            k, len(shares), ever, pct(combo_stats[k]["median"]), pct(combo_stats[k]["p25"]), pct(combo_stats[k]["p75"]),
            combo_stats[k]["zero"]))
    res["comboStats"] = combo_stats
    p()

    # ------------------------------------------------------------------ 5. 採点との関係
    if os.path.exists(SCORES):
        with open(SCORES) as f:
            sc = json.load(f)
        tot = {s: sc["companies"][s]["total"] for s in SYMS if s in sc.get("companies", {})}
        p("=" * 100)
        p("5. 事業の採点（scores.json）と、値動き・評価・過去の2倍達成率の関係（順位相関、%d銘柄）" % len(tot))
        p("-" * 100)
        # 円建て1年ボラ（2025-10-02→2026-10-02の日次、√250）
        vol1y = {}
        for s in SYMS:
            rows = charts[s]
            ds = [d for d in rows if "2025-10-02" <= d <= AS_OF]
            ys = [to_yen(s, d, rows[d]) for d in ds]
            rets = [b / a - 1 for a, b in zip(ys, ys[1:]) if a and b]
            vol1y[s] = statistics.stdev(rets) * math.sqrt(250) if len(rets) > 20 else None
        fwd = {s: FWD_PER_PROVIDER.get(s) for s in SYMS}
        cg = {s: req[s]["consensusGrowthNextYear"] for s in SYMS}
        share2x = {s: (hist[s]["yen"]["share"] if hist[s]["yen"]["nStarts"] >= 500 else None) for s in SYMS}  # 起点が500日未満（キオクシア・Sandisk）は除外
        need_per = {}
        for s in SYMS:
            r1 = [r for r in req[s]["rows"] if r["basis"].startswith("アナリスト平均・来期")]
            need_per[s] = r1[0]["perAtTarget"] if r1 else None
        keys = [s for s in SYMS if s in tot]
        for lab, dd in (("円建て1年ボラ", vol1y), ("提供元予想PER", fwd), ("来期EPSの伸び（アナリスト平均）", cg),
                        ("過去10年の15か月2倍の割合（円）", share2x), ("2倍時PER（来期アナリスト平均EPS基準）", need_per)):
            rho, n = spearman([tot[s] for s in keys], [dd[s] for s in keys])
            p("   合計点 × %-36s ρ=%s（n=%d）" % (lab, num(rho, 2), n))
        p()
        p("   銘柄別：合計点｜円建て1年ボラ｜提供元予想PER｜来期EPSの伸び｜15か月2倍の割合（円）｜2倍時PER（来期平均EPS）")
        for s in sorted(keys, key=lambda x: SYMS.index(x)):
            p("   %-14s %4.1f｜%s｜%s｜%s｜%s｜%s" % (NAME[s], tot[s], pct(vol1y[s], 0), num(fwd[s]), pct(cg[s], 0),
                                                pct(share2x[s], 1), num(need_per[s])))
        # 合計点の上位・下位で分けた中央値
        med = statistics.median(tot[s] for s in keys)
        hi = [s for s in keys if tot[s] > med]
        lo = [s for s in keys if tot[s] <= med]

        def mm(group, dd):
            v = [dd[s] for s in group if dd[s] is not None]
            return statistics.median(v) if v else None
        p()
        p("   合計点の中央値（%.1f）より上の%d銘柄／以下の%d銘柄の中央値：" % (med, len(hi), len(lo)))
        for lab, dd, f_ in (("円建て1年ボラ", vol1y, pct), ("提供元予想PER", fwd, num), ("来期EPSの伸び", cg, pct),
                            ("15か月2倍の割合（円）", share2x, pct)):
            p("     %-24s 上 %s／下 %s" % (lab, f_(mm(hi, dd)), f_(mm(lo, dd))))
        res["scoreRelation"] = {"vol1yYen": vol1y, "median": med, "upper": hi, "lower": lo}

    txt = "\n".join(lines) + "\n"
    sys.stdout.write(txt)
    with open(OUT_TXT, "w") as f:
        f.write(txt)
    os.makedirs(WORK, exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=str)


if __name__ == "__main__":
    main()
