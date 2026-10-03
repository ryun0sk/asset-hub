#!/usr/bin/env python3
"""AI関連銘柄 年末までの比較材料（2026-10-03）の再現用計算。

標準ライブラリのみ。Yahoo Finance公開エンドポイント（キー不要）から
  - chart（分割調整済み日足、2年）→ working/yahoo-chart-<symbol>-2y.json
  - fundamentals-timeseries（発行済株式数・自己株式・EPS）→ working/yahoo-fund-<symbol>.json
を取得・保存し、次を計算して標準出力と working/compare-results.json に書き出す。
標準出力は working/compare-output.txt に保存してレポートの数値と照合する。

対象は日本株12銘柄＋海外10銘柄（米国・台湾・韓国・オランダのADR等）。円で投資する前提で、
海外株は「現地通貨の終値×同じ日付以前で直近のドル円・台湾ドル円・ウォン円の終値」で円換算する。

  1. 基本表（全22銘柄、円換算）：終値、時価総額、実績PER・予想PER、年初来・1年騰落率（現地・円）、
     1年来高値からの位置、円建ての年率ボラ（60日・1年、日次）、週次βと最大ドローダウン（1年、円建て）、売買代金
  2. 年末（2026-12-30大納会）までの東証営業日数
  3. 60営業日後の価格の幅：対数正規（ドリフト0）の1σ・2σ、過去1年のローリング60営業日リターン（円建て）
  4. 相関：日本株同士は東証の同日の日次相関（60日・1年）。海外を含む全体は時差があるため
     週次（各金曜時点の直近終値、円建て）の相関（1年＝53週、半年＝26週）。サブテーマ・地域別の平均
  5. 2〜3銘柄の均等配分（全組み合わせ）：ボラ＝各銘柄の円建て日次ボラ（1年）×週次相関（1年）。
     1,000万円の損益幅の例示（組み合わせタイプ別に機械的に集計。特定の組み合わせの推奨ではない）
  6. 日本株の日次の特徴：対日経平均β（日次）、日経平均の大幅下落日・上昇日の平均騰落率

使い方:
  python3 compare.py            # 取得して計算（取得データは working/ に保存）
  python3 compare.py --offline  # working/ の保存データだけで再計算

株価・EPSは2026-10-02時点の株式分割後の基準。1年＝2025-10-02終値→2026-10-02終値（日次242本、キオクシア版と同じ窓）。
年率換算は日次√250・週次√52。結果は記載日時点の過去データの統計で、将来の予測や投資助言ではない。
"""
import argparse
import bisect
import datetime as dt
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
SUPPLY_FUND = os.path.join(HERE, "..", "..", "ai-supply-chain", "2026-10-03", "fundamentals.json")
AS_OF = "2026-10-02"
ONE_YEAR_START = "2025-10-03"  # 1年の日次リターンの初日（2025-10-02終値→10-03）
BASE_1Y = "2025-10-02"         # 1年騰落率の基準日
YEAR_END_2025 = "2025-12-31"   # 年初来の基準（各市場の2025年最終取引日の終値）
HORIZON_END = "2026-12-30"     # 2026年の大納会
ANN_D, ANN_W = math.sqrt(250), math.sqrt(52)
BUDGET = 10_000_000            # 例示の投資額（円）
HW = 12                        # 60営業日≒12週

# (コード, 名前, サブテーマ, 地域, 為替)。サブテーマは筆者の分類
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
NAME["^N225"] = "日経平均"
GROUP = {u[0]: u[2] for u in UNIVERSE}
REGION = {u[0]: u[3] for u in UNIVERSE}
FXOF = {u[0]: u[4] for u in UNIVERSE}
JP = [s for s in SYMS if REGION[s] == "日本"]
SEMI = {"メモリー", "装置・テスト", "基板・素材", "設計（GPU・ASIC）", "受託製造"}
FXS = ["JPY=X", "TWDJPY=X", "KRWJPY=X"]
BENCH = "^N225"  # 1306.T（TOPIX連動ETF）は2026-03-31に提供元データの欠損があるため使わない

# 10/1効力の株式分割（取得時点で提供元の株数・EPSに未反映）。過去の分割は提供元が遡って反映済み
PENDING_SPLIT = {"285A.T": 3.0, "8035.T": 5.0, "4062.T": 2.0}

# 会社予想EPS（今期、分割後の基準、現地通貨）。出所はレポートの基本表の注記
FORECAST_EPS = {
    "6857.T": (911.64, "2027年3月期 会社予想（7/29上方修正）"),
    "4062.T": (149.68, "2027年3月期 会社予想（8/4上方修正、10/1分割後）"),
    "6920.T": (1004.12, "2027年6月期 会社予想（2026-08-06 決算短信）"),
    "4063.T": (286.00, "2027年3月期 会社予想（2026-07-24）"),
    "6501.T": (201.14, "2027年3月期 会社予想（2026-07-29 上方修正）"),
    "5803.T": (196.88, "2027年3月期 会社予想（photonics版 report.md、分割後）"),
    "5801.T": (149.25, "2027年3月期 会社予想（photonics版 report.md、分割後）"),
    "5802.T": (108.99, "2027年3月期 会社予想（photonics版 report.md、分割後）"),
}
# 予想PER（提供元が保存した最新スナップショット 2026-09-17〜23）【外部予想ベース】。ai-supply-chain版 report.md 第3節の表と同じ値
FWD_PER_PROVIDER = {
    "285A.T": 5.8, "6857.T": 35.8, "8035.T": 31.6, "6146.T": 30.9, "4062.T": None, "4063.T": 18.7,
    "5803.T": None, "6501.T": 24.7, "NVDA": 24.9, "AVGO": 19.4, "AMD": 39.5, "2330.TW": 18.6, "MU": 7.0,
    "000660.KS": 3.9, "SNDK": 8.0, "ASML": 28.9, "LITE": 42.9, "VRT": 27.8,
}
# 実績EPSの差し替え：Micronは提供元のTTMが2026年5月期で止まっているため公式の2026年8月期通期GAAP EPS（ai-supply-chain版と同じ扱い）
EPS_OVERRIDE = {"MU": (74.33, "2026-08-31", "Micron公式 FY2026 GAAP希薄化後EPS（2026-09-30発表）")}


def fname(sym, kind="chart"):
    safe = sym.replace("^", "_").replace("=", "_")
    return os.path.join(WORK, ("yahoo-chart-%s-2y.json" if kind == "chart" else "yahoo-fund-%s.json") % safe)


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def fetch_chart(sym):
    url = ("https://query1.finance.yahoo.com/v8/finance/chart/%s?range=2y&interval=1d&events=div%%2Csplits"
           % urllib.parse.quote(sym))
    d = get(url)
    d["_retrieved"] = dt.datetime.now(dt.timezone.utc).isoformat()
    d["_url"] = url
    with open(fname(sym), "w") as f:
        json.dump(d, f)
    time.sleep(0.4)


def fetch_fund(sym):
    types = ("quarterlyOrdinarySharesNumber,annualOrdinarySharesNumber,quarterlyShareIssued,"
             "quarterlyTreasurySharesNumber,trailingDilutedEPS,trailingBasicEPS,annualDilutedEPS")
    url = ("https://query1.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/%s?symbol=%s"
           "&type=%s&period1=1640995200&period2=1790985600" % (urllib.parse.quote(sym), urllib.parse.quote(sym), types))
    d = get(url)
    d["_retrieved"] = dt.datetime.now(dt.timezone.utc).isoformat()
    d["_url"] = url
    with open(fname(sym, "fund"), "w") as f:
        json.dump(d, f)
    time.sleep(0.4)


def load_chart(sym):
    with open(fname(sym)) as f:
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
        rows[day] = {"o": q["open"][i], "h": q["high"][i] or c, "l": q["low"][i] or c, "c": c, "v": q["volume"][i] or 0}
    splits = []
    for v in (r.get("events", {}).get("splits") or {}).values():
        day = dt.datetime.fromtimestamp(v["date"] + off, dt.timezone.utc).date().isoformat()
        splits.append((day, v["numerator"] / v["denominator"]))
    return dict(sorted(rows.items())), sorted(splits), r["meta"]


def load_fund(sym):
    with open(fname(sym, "fund")) as f:
        d = json.load(f)
    out = {}
    for r in d["timeseries"]["result"]:
        t = r["meta"]["type"][0]
        out[t] = [(x["asOfDate"], x["reportedValue"]["raw"]) for x in (r.get(t) or []) if x]
    return out


def corr(x, y):
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sx = math.sqrt(sum((a - mx) ** 2 for a in x))
    sy = math.sqrt(sum((b - my) ** 2 for b in y))
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)


def cov(x, y):
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / n


def beta(y, x):
    return cov(y, x) / cov(x, x)


def quantile(xs, p):
    s = sorted(xs)
    k = (len(s) - 1) * p
    f = math.floor(k)
    c = min(f + 1, len(s) - 1)
    return s[f] + (s[c] - s[f]) * (k - f)


def mdd(closes):
    peak, pk_day = -1, None
    best = (0.0, None, None)
    for d, c in closes:
        if c > peak:
            peak, pk_day = c, d
        dd = c / peak - 1
        if dd < best[0]:
            best = (dd, pk_day, d)
    return best


def trading_days(start, end):
    # 2026年10〜12月の東証休業日（土日以外）：スポーツの日10/12、文化の日11/3、勤労感謝の日11/23、12/31
    hol = {"2026-10-12", "2026-11-03", "2026-11-23", "2026-12-31"}
    d, e, out = dt.date.fromisoformat(start), dt.date.fromisoformat(end), []
    while d <= e:
        if d.weekday() < 5 and d.isoformat() not in hol:
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def pct(v, nd=1):
    return ("%+." + str(nd) + "f%%") % (100 * v)


def man(v):
    return "%+d万円" % round(v / 1e4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    a = ap.parse_args()
    os.makedirs(WORK, exist_ok=True)
    allsyms = SYMS + [BENCH] + FXS
    if not a.offline:
        for s in allsyms:
            try:
                fetch_chart(s)
            except Exception as e:  # noqa: BLE001
                print("fetch failed", s, e, file=sys.stderr)
        for s in SYMS:
            try:
                fetch_fund(s)
            except Exception as e:  # noqa: BLE001
                print("fetch failed (fund)", s, e, file=sys.stderr)

    data, splits = {}, {}
    for s in allsyms:
        data[s], splits[s], _ = load_chart(s)
    out = {"asOf": AS_OF, "retrieved": {}}
    for s in allsyms:
        with open(fname(s)) as f:
            out["retrieved"][s] = json.load(f).get("_retrieved")
    fxdays = {x: sorted(data[x]) for x in FXS}

    def fx_on(x, d):
        if x is None:
            return 1.0
        i = bisect.bisect_right(fxdays[x], d) - 1
        return data[x][fxdays[x][i]]["c"]

    def on_or_before(rows, d):
        ks = [k for k in rows if k <= d]
        return ks[-1]

    # 円換算の終値系列（各銘柄の取引日ベース）
    YEN = {s: {d: r["c"] * fx_on(FXOF.get(s), d) for d, r in data[s].items()} for s in SYMS}
    YEN[BENCH] = {d: r["c"] for d, r in data[BENCH].items()}

    # ---- 年末までの営業日
    H = len(trading_days("2026-10-05", HORIZON_END))
    out["horizonDays"] = H
    print("年末まで（10/5〜12/30）の東証営業日: %d日（≒%d週）" % (H, HW))

    # ---- 東証の共通営業日（日本株12銘柄＋日経平均）と日次リターン
    tok = JP + [BENCH]
    days = sorted(set.intersection(*[set(data[s]) for s in tok]))
    R = {s: {} for s in tok}
    for i in range(1, len(days)):
        for s in tok:
            R[s][days[i]] = data[s][days[i]]["c"] / data[s][days[i - 1]]["c"] - 1
    y1 = [d for d in days[1:] if d >= ONE_YEAR_START]
    w60 = days[1:][-60:]
    out["jpWindow"] = {"oneYearReturns": len(y1), "first": y1[0], "last": y1[-1]}
    print("東証の共通営業日 %d日（%s〜%s）、1年の日次リターン %d本（%s〜%s）" % (
        len(days), days[0], days[-1], len(y1), y1[0], y1[-1]))

    # ---- 週次（金曜時点の直近終値、円建て）
    fridays = []
    d = dt.date.fromisoformat(BASE_1Y)
    while d.weekday() != 4:
        d -= dt.timedelta(days=1)
    start_fri = d  # 2025-09-26（1年窓の直前の金曜）
    d = start_fri - dt.timedelta(weeks=HW + 1)
    while d <= dt.date.fromisoformat(AS_OF):
        fridays.append(d.isoformat())
        d += dt.timedelta(weeks=1)
    WV = {}
    for s in SYMS + [BENCH]:
        rows = YEN[s]
        WV[s] = [rows[on_or_before(rows, f)] for f in fridays]
    WR = {s: [WV[s][i] / WV[s][i - 1] - 1 for i in range(1, len(fridays))] for s in WV}
    wdays = fridays[1:]
    i1y = [i for i, f in enumerate(wdays) if f > start_fri.isoformat()]
    w1y = i1y  # 52週
    w26 = i1y[-26:]
    out["weekly"] = {"n1y": len(w1y), "first": wdays[w1y[0]], "last": wdays[w1y[-1]]}
    print("週次（金曜時点の直近終値・円建て）：1年 %d本（%s〜%s）" % (len(w1y), wdays[w1y[0]], wdays[w1y[-1]]))

    # ---- 1. 基本表
    sfund = {}
    if os.path.exists(SUPPLY_FUND):
        with open(SUPPLY_FUND) as f:
            for c in json.load(f)["companies"]:
                sfund[c["symbol"]] = c
    base = {}
    print("\n== 1. 基本表（%s終値。海外は現地通貨と円換算。時価総額・売買代金は円）" % AS_OF)
    print("%-14s %12s %10s %8s %8s %7s %7s %8s %8s %8s %8s %7s %6s %6s %6s %7s %7s %8s" % (
        "銘柄", "現地終値", "円換算", "時価兆円", "実績PER", "会予PER", "外予PER", "年初来現", "年初来円", "1年現", "1年円",
        "高値比", "ボラ60", "ボラ1年", "現ボラ", "週β1年", "MDD円", "代金億円"))
    for s in SYMS + [BENCH]:
        rows, yr = data[s], YEN[s]
        last_d = on_or_before(rows, AS_OF)
        last, last_y = rows[last_d]["c"], yr[last_d]
        yb, ob = on_or_before(rows, YEAR_END_2025), on_or_before(rows, BASE_1Y)
        ytd, ytd_y = last / rows[yb]["c"] - 1, last_y / yr[yb] - 1
        r1, r1_y = last / rows[ob]["c"] - 1, last_y / yr[ob] - 1
        ds = sorted(rows)
        win = [d for d in ds if d >= ONE_YEAR_START]
        hi_d = max(win, key=lambda d: rows[d]["h"])
        lo_d = min(win, key=lambda d: rows[d]["l"])
        ry = [yr[ds[i]] / yr[ds[i - 1]] - 1 for i in range(1, len(ds)) if ds[i] >= ONE_YEAR_START]
        rl = [rows[ds[i]]["c"] / rows[ds[i - 1]]["c"] - 1 for i in range(1, len(ds)) if ds[i] >= ONE_YEAR_START]
        r60 = [yr[ds[i]] / yr[ds[i - 1]] - 1 for i in range(len(ds) - 60, len(ds))]
        v60, v1, vl = statistics.pstdev(r60) * ANN_D, statistics.pstdev(ry) * ANN_D, statistics.pstdev(rl) * ANN_D
        wb = beta([WR[s][i] for i in w1y], [WR[BENCH][i] for i in w1y])
        dd = mdd([(d, yr[d]) for d in [ob] + win])
        tv = [rows[d]["c"] * rows[d]["v"] * fx_on(FXOF.get(s), d) for d in ds]
        b = dict(region=REGION.get(s, ""), group=GROUP.get(s, ""), lastDay=last_d, close=last, closeYen=last_y,
                 ytd=ytd, ytdYen=ytd_y, r1y=r1, r1yYen=r1_y, hi=rows[hi_d]["h"], hiDay=hi_d, lo=rows[lo_d]["l"],
                 loDay=lo_d, fromHi=last / rows[hi_d]["h"] - 1, vol60=v60, vol1y=v1, vol1yLocal=vl, wbeta=wb,
                 mdd=dd[0], mddPeak=dd[1], mddTrough=dd[2], tv20=statistics.mean(tv[-20:]) / 1e8, nRet1y=len(ry))
        if s in R:
            b["beta60"] = beta([R[s][d] for d in w60], [R[BENCH][d] for d in w60])
            b["beta1y"] = beta([R[s][d] for d in y1], [R[BENCH][d] for d in y1])
        if s in NAME and s != BENCH:
            fu = load_fund(s)
            sh = None
            for key in ("quarterlyOrdinarySharesNumber", "annualOrdinarySharesNumber"):
                if fu.get(key):
                    cand = max(fu[key])
                    if sh is None or cand[0] > sh[0]:
                        sh = cand
            mult = PENDING_SPLIT.get(s, 1.0)
            if sh:
                b.update(sharesAsOf=sh[0], shares=sh[1] * mult, mcapYen=sh[1] * mult * last_y)
            if s in EPS_OVERRIDE:
                e, pe, src = EPS_OVERRIDE[s]
                b.update(ttmEps=e, ttmEnd=pe, ttmSrc=src)
            elif s in sfund and sfund[s].get("ttmRows"):
                tr = sfund[s]["ttmRows"][-1]
                b.update(ttmEps=tr["eps"], ttmEnd=tr["periodEnd"], ttmSrc="ai-supply-chain fundamentals.json",
                         epsCcy=sfund[s].get("epsCurrency"))
            else:
                cand = [(d, v, "TTM") for d, v in (fu.get("trailingDilutedEPS") or [])]
                cand += [(d, v, "通期") for d, v in (fu.get("annualDilutedEPS") or [])]
                if cand:
                    # 期末が同じならTTMを優先（住友電工の提供元の通期値296.11は同じ期末のTTM 118.44と食い違うため）
                    pe_day, eps, kind = max(cand, key=lambda t: (t[0], t[2] == "TTM"))
                    b.update(ttmEps=eps / mult, ttmEnd=pe_day, ttmSrc="Yahoo %s（希薄化後）" % kind)
            ccy_ok = b.get("epsCcy") in (None, "JPY", "USD", "TWD", "KRW") and not (s == "ASML")
            if b.get("ttmEps") and b["ttmEps"] > 0 and ccy_ok:
                b["ttmPer"] = last / b["ttmEps"]
            if s in FORECAST_EPS:
                b["fcEps"], b["fcNote"] = FORECAST_EPS[s]
                b["fcPer"] = last / b["fcEps"]
            b["fwdPerProvider"] = FWD_PER_PROVIDER.get(s)
        base[s] = b
        f1 = lambda v: "%.1f" % v if v else "—"  # noqa: E731
        print("%-14s %12.2f %10.0f %8.2f %8s %7s %7s %8s %8s %8s %8s %7s %5.0f%% %5.0f%% %5.0f%% %7.2f %7s %8.0f" % (
            NAME[s], last, last_y, b.get("mcapYen", 0) / 1e12, f1(b.get("ttmPer")), f1(b.get("fcPer")),
            f1(b.get("fwdPerProvider")), pct(ytd), pct(ytd_y), pct(r1), pct(r1_y), pct(b["fromHi"]),
            100 * v60, 100 * v1, 100 * vl, wb, pct(dd[0]), b["tv20"]))
    out["base"] = base
    print("\n-- 補足：1年来高値・安値（日中、現地通貨）、MDD期間（円建て）、株数・EPSの基準、東証日次β")
    for s in SYMS:
        b = base[s]
        print("%-14s 高値 %.2f(%s) 安値 %.2f(%s) MDD %s（%s→%s） 株数 %s（%s時点×%.0f） 実績EPS %s（%s, %s）%s" % (
            NAME[s], b["hi"], b["hiDay"], b["lo"], b["loDay"], pct(b["mdd"]), b["mddPeak"], b["mddTrough"],
            "%.0f" % b["shares"] if b.get("shares") else "—", b.get("sharesAsOf"), PENDING_SPLIT.get(s, 1.0),
            "%.2f" % b["ttmEps"] if b.get("ttmEps") is not None else "—", b.get("ttmEnd"), b.get("ttmSrc"),
            "  日次β 60日 %.2f / 1年 %.2f" % (b["beta60"], b["beta1y"]) if "beta60" in b else ""))
    for x in FXS:
        rows = data[x]
        ds = sorted(rows)
        fr = [rows[ds[i]]["c"] / rows[ds[i - 1]]["c"] - 1 for i in range(1, len(ds)) if ds[i] >= ONE_YEAR_START]
        yb = on_or_before(rows, YEAR_END_2025)
        last = rows[ds[-1]]["c"]
        out.setdefault("fx", {})[x] = dict(last=last, lastDay=ds[-1], ytd=last / rows[yb]["c"] - 1,
                                          r1y=last / rows[on_or_before(rows, BASE_1Y)]["c"] - 1,
                                          vol1y=statistics.pstdev(fr) * ANN_D)
        print("為替 %-9s %.4f（%s） 年初来 %s 1年 %s 年率ボラ %.1f%%" % (
            x, last, ds[-1], pct(out["fx"][x]["ytd"]), pct(out["fx"][x]["r1y"]), 100 * out["fx"][x]["vol1y"]))

    # ---- 3. 60営業日後の幅（円建て）
    print("\n== 3. %d営業日後の価格の幅（円建て。対数正規・ドリフト0、σ=年率ボラ×√(%d/250)）と過去1年の実績" % (H, H))
    rng = {}
    for s in SYMS + [BENCH]:
        b = base[s]
        r = {}
        for lab, v in (("60日", b["vol60"]), ("1年", b["vol1y"])):
            sg = v * math.sqrt(H / 250)
            r[lab] = dict(sigma=sg, m1=math.exp(-sg) - 1, p1=math.exp(sg) - 1, m2=math.exp(-2 * sg) - 1,
                          p2=math.exp(2 * sg) - 1)
        yr = YEN[s]
        ds = sorted(yr)
        hist = [(ds[i], yr[ds[i]] / yr[ds[i - H]] - 1) for i in range(H, len(ds)) if ds[i] >= ONE_YEAR_START]
        vals = [v for _, v in hist]
        wo, be = min(hist, key=lambda t: t[1]), max(hist, key=lambda t: t[1])
        r["hist"] = dict(n=len(vals), min=wo[1], minEnd=wo[0], p10=quantile(vals, 0.1), median=quantile(vals, 0.5),
                         p90=quantile(vals, 0.9), max=be[1], maxEnd=be[0],
                         negShare=sum(1 for v in vals if v < 0) / len(vals))
        rng[s] = r
        r["price1y"] = dict(m1=b["closeYen"] * (1 + r["1年"]["m1"]), p1=b["closeYen"] * (1 + r["1年"]["p1"]),
                            m2=b["closeYen"] * (1 + r["1年"]["m2"]), p2=b["closeYen"] * (1 + r["1年"]["p2"]))
        h = r["hist"]
        print("%-14s 1σ(60日) %s〜%s 2σ %s〜%s | 1σ(1年) %s〜%s 2σ %s〜%s | 実績: 最悪 %s(%s) 10%% %s 中央 %s 90%% %s 最良 %s(%s) マイナス %.0f%%" % (
            NAME[s], pct(r["60日"]["m1"], 0), pct(r["60日"]["p1"], 0), pct(r["60日"]["m2"], 0), pct(r["60日"]["p2"], 0),
            pct(r["1年"]["m1"], 0), pct(r["1年"]["p1"], 0), pct(r["1年"]["m2"], 0), pct(r["1年"]["p2"], 0),
            pct(h["min"], 0), h["minEnd"], pct(h["p10"], 0), pct(h["median"], 0), pct(h["p90"], 0), pct(h["max"], 0),
            h["maxEnd"], 100 * h["negShare"]))
        print("%-14s 円建て価格 1σ(1年) %.0f〜%.0f円 2σ %.0f〜%.0f円" % ("", r["price1y"]["m1"], r["price1y"]["p1"],
                                                                r["price1y"]["m2"], r["price1y"]["p2"]))
    out["range"] = rng

    # ---- 4a. 日本株の日次相関
    short = {s: NAME[s][:4] for s in SYMS + [BENCH]}
    CJ = {}
    for lab, ds in (("60日", w60), ("1年", y1)):
        CJ[lab] = {x: {y: corr([R[x][d] for d in ds], [R[y][d] for d in ds]) for y in tok} for x in tok}
    out["corrJpDaily"] = CJ
    for lab in ("60日", "1年"):
        print("\n== 4a. 日本株の日次相関（東証同日、%s）" % lab)
        print("%-8s" % "", " ".join("%6s" % short[y] for y in tok))
        for x in JP:
            print("%-8s" % short[x], " ".join("%6.2f" % CJ[lab][x][y] for y in tok))

    # ---- 4b. 全体の週次相関（円建て）
    CW = {}
    for lab, idx in (("1年", w1y), ("半年", w26)):
        CW[lab] = {x: {y: corr([WR[x][i] for i in idx], [WR[y][i] for i in idx]) for y in SYMS + [BENCH]}
                   for x in SYMS + [BENCH]}
    out["corrWeekly"] = CW
    for lab in ("1年", "半年"):
        print("\n== 4b. 週次相関（円建て、%s）" % lab)
        print("%-8s" % "", " ".join("%5s" % short[y][:3] for y in SYMS + [BENCH]))
        for x in SYMS:
            print("%-8s" % short[x], " ".join("%5.2f" % CW[lab][x][y] for y in SYMS + [BENCH]))
    groups = []
    for s in SYMS:
        if GROUP[s] not in groups:
            groups.append(GROUP[s])
    gc = {}
    for g1 in groups:
        for g2 in groups:
            vals = {lab: [CW[lab][x][y] for x in SYMS for y in SYMS if x != y and GROUP[x] == g1 and GROUP[y] == g2]
                    for lab in CW}
            if vals["1年"]:
                gc["%s|%s" % (g1, g2)] = {lab: statistics.mean(v) for lab, v in vals.items()}
    out["groupCorrWeekly"] = gc
    print("\n-- サブテーマ間の平均週次相関（円建て、同一銘柄を除く）1年 / 半年")
    print("%-16s" % "", " ".join("%11s" % g[:6] for g in groups))
    for g1 in groups:
        print("%-16s" % g1, " ".join("%11s" % ("%.2f/%.2f" % (gc[k]["1年"], gc[k]["半年"]) if (k := "%s|%s" % (g1, g2)) in gc else "—")
                                      for g2 in groups))
    print("\n-- 地域間の平均週次相関（1年）")
    rc = {}
    for r1n in ("日本", "海外"):
        for r2n in ("日本", "海外"):
            v = [CW["1年"][x][y] for x in SYMS for y in SYMS if x != y and REGION[x] == r1n and REGION[y] == r2n]
            rc["%s|%s" % (r1n, r2n)] = statistics.mean(v)
            print("%s〜%s %.2f" % (r1n, r2n, rc["%s|%s" % (r1n, r2n)]))
    out["regionCorrWeekly"] = rc
    print("\n-- 各銘柄の平均週次相関（1年）：日本株との平均 / 海外株との平均 / 日経平均")
    avgc = {}
    for x in SYMS:
        avgc[x] = dict(jp=statistics.mean(CW["1年"][x][y] for y in SYMS if y != x and REGION[y] == "日本"),
                       ovs=statistics.mean(CW["1年"][x][y] for y in SYMS if y != x and REGION[y] == "海外"),
                       n225=CW["1年"][x][BENCH])
        print("%-14s %.2f / %.2f / %.2f" % (NAME[x], avgc[x]["jp"], avgc[x]["ovs"], avgc[x]["n225"]))
    out["avgCorrWeekly"] = avgc
    # 日次相関と週次相関の比較（日本株同士で、週次化の影響を確認）
    jp_pairs = [(x, y) for x, y in itertools.combinations(JP, 2)]
    out["dailyVsWeeklyJp"] = dict(daily=statistics.mean(CJ["1年"][x][y] for x, y in jp_pairs),
                                  weekly=statistics.mean(CW["1年"][x][y] for x, y in jp_pairs))
    print("参考：日本株同士の平均相関 日次1年 %.2f / 週次1年 %.2f" % (out["dailyVsWeeklyJp"]["daily"],
                                                       out["dailyVsWeeklyJp"]["weekly"]))

    # ---- 6. 日本株：日経平均の大幅下落日・上昇日
    down = [d for d in y1 if R[BENCH][d] <= -0.02]
    up = [d for d in y1 if R[BENCH][d] >= 0.02]
    print("\n== 6. 日経平均が−2%%以下の日（1年で%d日）/ +2%%以上の日（%d日）の平均騰落率（日本株）" % (len(down), len(up)))
    du = {}
    for x in JP:
        du[x] = dict(down=statistics.mean(R[x][d] for d in down), up=statistics.mean(R[x][d] for d in up),
                     downNeg=sum(1 for d in down if R[x][d] < 0))
        print("%-14s 下落日 %s（%d/%d日でマイナス）上昇日 %s" % (NAME[x], pct(du[x]["down"]), du[x]["downNeg"], len(down),
                                                     pct(du[x]["up"])))
    # 海外株：日経平均の週次下落（−4%以下）の週の平均（円建て）
    wdown = [i for i in w1y if WR[BENCH][i] <= -0.04]
    print("-- 日経平均の週次−4%%以下の週（1年で%d週）の平均（円建て）" % len(wdown))
    for x in SYMS:
        du.setdefault(x, {})["wdown"] = statistics.mean(WR[x][i] for i in wdown)
        print("%-14s %s" % (NAME[x], pct(du[x]["wdown"])))
    out["downUp"] = dict(nDown=len(down), nUp=len(up), nWeekDown=len(wdown), weekDown=[wdays[i] for i in wdown], stats=du)

    # ---- 5. ポートフォリオ（均等配分、全組み合わせ）
    vol = {s: base[s]["vol1y"] for s in SYMS}

    def pstats(combo):
        k = len(combo)
        var = sum(vol[x] * vol[y] * (1.0 if x == y else CW["1年"][x][y]) for x in combo for y in combo) / k ** 2
        pv = math.sqrt(var)
        avgv = statistics.mean(vol[x] for x in combo)
        mc = statistics.mean(CW["1年"][x][y] for x, y in itertools.combinations(combo, 2))
        pw = [statistics.mean(WR[x][i] for x in combo) for i in w1y]
        wb = beta(pw, [WR[BENCH][i] for i in w1y])
        # 買い持ち（当初均等）の12週リターン（終点が1年の窓内）
        hh = []
        for i in w1y:
            j = i + 1  # WV の添字（WR[i] は WV[i]→WV[i+1]）
            if j - HW >= 0:
                hh.append(statistics.mean(WV[x][j] / WV[x][j - HW] for x in combo) - 1)
        # 感応度：日本株だけの組み合わせは東証同日の日次相関（1年）でも計算する
        if all(REGION[x] == "日本" for x in combo):
            vd = math.sqrt(sum(vol[x] * vol[y] * (1.0 if x == y else CJ["1年"][x][y]) for x in combo for y in combo) / k ** 2)
        else:
            vd = None
        return dict(vol=pv, volDailyCorr=vd, avgVol=avgv, ratio=pv / avgv, meanCorr=mc, wbeta=wb, histMin=min(hh),
                    histP10=quantile(hh, 0.1), histMed=quantile(hh, 0.5), histP90=quantile(hh, 0.9), histMax=max(hh),
                    histN=len(hh))

    def ttype(combo):
        gs = [GROUP[s] for s in combo]
        if len(set(gs)) == 1:
            return "A 同一サブテーマ"
        if all(g in SEMI for g in gs):
            return "B 半導体内で別サブテーマ"
        if any(g in SEMI for g in gs):
            return "C 半導体＋半導体以外"
        return "D 半導体なし"

    def rtype(combo):
        rs = {REGION[s] for s in combo}
        return "日本のみ" if rs == {"日本"} else ("海外のみ" if rs == {"海外"} else "日本＋海外")

    port = {}
    for k in (2, 3):
        for combo in itertools.combinations(SYMS, k):
            p = pstats(combo)
            p.update(k=k, ttype=ttype(combo), rtype=rtype(combo))
            port["+".join(combo)] = p
    out["portfolios"] = port
    print("\n== 5. 均等配分の全組み合わせ（2銘柄%d通り・3銘柄%d通り）。ボラ＝円建て日次ボラ（1年）×週次相関（1年）" % (
        sum(1 for v in port.values() if v["k"] == 2), sum(1 for v in port.values() if v["k"] == 3)))

    def summarize(label, pred):
        res = {}
        for k in (2, 3):
            vs = [v for key, v in port.items() if v["k"] == k and pred(key, v)]
            if not vs:
                continue
            s = dict(n=len(vs), meanCorr=statistics.mean(v["meanCorr"] for v in vs),
                     volMed=quantile([v["vol"] for v in vs], 0.5), volMin=min(v["vol"] for v in vs),
                     volMax=max(v["vol"] for v in vs), ratioMed=quantile([v["ratio"] for v in vs], 0.5),
                     betaMed=quantile([v["wbeta"] for v in vs], 0.5), histMinMed=quantile([v["histMin"] for v in vs], 0.5))
            res[k] = s
            print("%d銘柄 %-26s n=%4d 平均相関 %.2f ボラ中央 %.0f%%（%.0f〜%.0f%%） 分散比 %.2f 週β中央 %.2f 過去最悪12週の中央 %s" % (
                k, label, s["n"], s["meanCorr"], 100 * s["volMed"], 100 * s["volMin"], 100 * s["volMax"],
                s["ratioMed"], s["betaMed"], pct(s["histMinMed"], 0)))
        return res

    summ = {}
    print("-- サブテーマの組み合わせ方")
    for t in ("A 同一サブテーマ", "B 半導体内で別サブテーマ", "C 半導体＋半導体以外", "D 半導体なし"):
        summ[t] = summarize(t, lambda key, v, t=t: v["ttype"] == t)
    print("-- 地域の組み合わせ方")
    for t in ("日本のみ", "海外のみ", "日本＋海外"):
        summ[t] = summarize(t, lambda key, v, t=t: v["rtype"] == t)
    lowv = {x for x in SYMS if vol[x] < 0.5}
    jo = [v for v in port.values() if v["volDailyCorr"]]
    out["jpDailySensitivity"] = dict(medWeekly=quantile([v["vol"] for v in jo], 0.5),
                                     medDaily=quantile([v["volDailyCorr"] for v in jo], 0.5),
                                     medDiff=quantile([v["volDailyCorr"] - v["vol"] for v in jo], 0.5))
    print("-- 感応度：日本のみの組み合わせ（%d通り）のボラ中央値 週次相関 %.0f%% / 日次相関 %.0f%%（差の中央値 %+.1fポイント）" % (
        len(jo), 100 * out["jpDailySensitivity"]["medWeekly"], 100 * out["jpDailySensitivity"]["medDaily"],
        100 * out["jpDailySensitivity"]["medDiff"]))
    print("-- 円建て1年ボラ50%%未満の銘柄（%s）を含む数" % "・".join(NAME[x] for x in SYMS if x in lowv))
    for n in (0, 1, 2, 3):
        summ["低ボラ%d" % n] = summarize("低ボラ銘柄%d社" % n,
                                       lambda key, v, n=n: len(set(key.split("+")) & lowv) == n)
    out["portSummary"] = summ
    out["lowVol"] = sorted(lowv)

    # 例示（機械的に選ぶ：銘柄数×地域タイプごとに、平均相関が最も高い組と最も低い組。加えて既存調査の2社・3社）
    examples = []
    for k in (2, 3):
        for t in ("日本のみ", "海外のみ", "日本＋海外"):
            vs = sorted([(key, v) for key, v in port.items() if v["k"] == k and v["rtype"] == t],
                        key=lambda kv: kv[1]["meanCorr"])
            examples.append((vs[-1][0], "%s・相関最高" % t))
            examples.append((vs[0][0], "%s・相関最低" % t))
    for key, lab in [("285A.T+6857.T+4062.T", "既存調査の3社"), ("285A.T+6857.T", "既存調査の2社")]:
        if key not in [e for e, _ in examples]:
            examples.append((key, lab))
    print("\n-- 例示：%s円を均等配分、%d営業日（σ幅は対数正規・ドリフト0。実績は過去1年の買い持ち12週）" % (format(BUDGET, ","), H))
    ex_out = []
    for key, lab in examples:
        v = port[key]
        sg = v["vol"] * math.sqrt(H / 250)
        e = dict(key=key, label=lab, names="＋".join(NAME[s] for s in key.split("+")), **v,
                 m1=BUDGET * (math.exp(-sg) - 1), p1=BUDGET * (math.exp(sg) - 1),
                 m2=BUDGET * (math.exp(-2 * sg) - 1), p2=BUDGET * (math.exp(2 * sg) - 1),
                 yMin=BUDGET * v["histMin"], yMed=BUDGET * v["histMed"], yMax=BUDGET * v["histMax"])
        ex_out.append(e)
        print("%-40s %-16s 相関%.2f ボラ%.0f%%%s 分散比%.2f 週β%.2f | 1σ %s〜%s 2σ %s〜%s | 実績 最悪%s 中央%s 最良%s" % (
            e["names"], lab, v["meanCorr"], 100 * v["vol"],
            "（日次相関なら%.0f%%）" % (100 * v["volDailyCorr"]) if v["volDailyCorr"] else "", v["ratio"], v["wbeta"],
            man(e["m1"]), man(e["p1"]), man(e["m2"]), man(e["p2"]), man(e["yMin"]), man(e["yMed"]), man(e["yMax"])))
    out["examples"] = ex_out
    print("\n-- 参考：1銘柄に%s円（円建て1年ボラ、%d営業日の1σ・2σ）" % (format(BUDGET, ","), H))
    single = {}
    for s in SYMS:
        sg = vol[s] * math.sqrt(H / 250)
        single[s] = [BUDGET * (math.exp(-sg) - 1), BUDGET * (math.exp(sg) - 1), BUDGET * (math.exp(-2 * sg) - 1),
                     BUDGET * (math.exp(2 * sg) - 1)]
        print("%-14s 1σ %s〜%s 2σ %s〜%s" % (NAME[s], *[man(x) for x in single[s]]))
    out["single"] = single

    with open(os.path.join(WORK, "compare-results.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=str)
    print("\n保存: working/compare-results.json")


if __name__ == "__main__":
    main()
