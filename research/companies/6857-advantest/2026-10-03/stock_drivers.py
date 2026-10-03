#!/usr/bin/env python3
"""アドバンテスト（6857）株価変動要因レポート（2026-10-03）の再現用計算。

標準ライブラリのみ。Yahoo Finance公開チャートAPI（キー不要、分割調整済み日足）から
日足OHLCVを取得して working/yahoo-chart-<symbol>-2y.json に保存し、次を計算する。
キオクシア版（../../285A-kioxia/2026-10-03/stock_drivers.py）と同じ方法・同じ窓で、
アドバンテスト固有の分析を追加する。

  1. 騰落率（期間別）と値動きの特徴（ボラティリティ、β、大きな日、出来高）
  2. 日経平均への寄与度（株価換算係数×株価変化÷除数）、構成比率、日経平均から6857を除いた指数とのβ
  3. 米国（NVDA・TER・TSM・AVGO・AMD・MU・LRCX・ASML・SOX）の前夜の値動きと翌営業日の6857
  4. 同じ時間帯のアジア（TSMC台湾・SK hynix・Samsung）との同日相関
  5. 決算発表（引け後15:30）翌営業日の反応
  6. 個別イベント日の値動き、テクニカル（移動平均・高値・安値・節目）

使い方:
  python3 stock_drivers.py            # 取得して計算（取得データは working/ に保存）
  python3 stock_drivers.py --offline  # working/ の保存データだけで再計算

株価はすべてYahoo Financeの分割調整後の円（6857は2023-10-01効力の1対4分割を含めて調整済み）。
日経平均の寄与度は、日経の公表した株価換算係数と、報道された寄与度から逆算した除数の近似値を使う（後述）。
結果は投資助言ではなく、記載日時点の検証用の統計である。
"""
import argparse
import datetime as dt
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
AS_OF = "2026-10-02"  # 直近取引日（東京）
ONE_YEAR_START = "2025-10-03"  # キオクシア版の「約1年」と同じ起点（2025-10-03〜2026-10-02）

SYMBOLS = {
    "6857.T": "アドバンテスト", "^N225": "日経平均", "1306.T": "TOPIX連動ETF",
    "285A.T": "キオクシア", "4062.T": "イビデン", "8035.T": "東京エレクトロン",
    "2330.TW": "TSMC(台湾)", "000660.KS": "SK hynix", "005930.KS": "Samsung電子",
    "NVDA": "NVIDIA", "TER": "Teradyne", "TSM": "TSMC ADR", "AVGO": "Broadcom", "AMD": "AMD",
    "MU": "Micron", "LRCX": "Lam Research", "ASML": "ASML", "^SOX": "SOX指数", "JPY=X": "ドル円",
}
TOKYO = ["6857.T", "^N225", "1306.T", "285A.T", "4062.T", "8035.T"]
ASIA = ["2330.TW", "000660.KS", "005930.KS"]
US = ["NVDA", "TER", "TSM", "AVGO", "AMD", "MU", "LRCX", "ASML", "^SOX"]

# 日経平均の株価換算係数（キャップ調整済み）。出所：日本経済新聞社インデックス・ニュース
#   2026-07-31「『アドバンテスト』に対する指数算出上の取り扱いについて」：10/1から0.9→0.8、係数7.2→6.4
#   2026年4月1日にキャップ調整比率0.9を設定（係数8→7.2）【報道：1/30基準日のウエート12.8%】
COEF = [("2026-10-01", 6.4), ("2026-04-01", 7.2), ("0000-00-00", 8.0)]
# 除数：報道された寄与度から逆算した近似値（独自計算）。
#   9/14：株価−640円、寄与度−154.47円（株探） → 640×7.2÷154.47 = 29.83
#   10/1：株価+3,350円、寄与度 約722円（財経新聞） → 3,350×6.4÷722 = 29.70
DIVISOR = [("2026-09-30", 29.70), ("0000-00-00", 29.83)]
# 報道された寄与度（検証用）
REPORTED_CONTRIB = {"2026-09-10": 260.0, "2026-09-11": -617.0, "2026-09-14": -154.47,
                    "2026-09-18": 436.86, "2026-09-24": 243.77, "2026-10-01": 722.0}

# 決算発表日（会社IRカレンダー。発表は東証の取引終了後。2026-10-28は15:30予定）
EARNINGS = ["2025-04-25", "2025-07-29", "2025-10-28", "2026-01-28", "2026-04-27", "2026-07-29"]
EVENTS = {
    "2025-10-29": "Q2 FY25決算・自社株買い1,500億円の翌日",
    "2025-11-20": "NVIDIA決算（米11/19引け後）の翌朝",
    "2025-11-21": "米半導体の反落",
    "2026-04-02": "CB1,000億円発行の発表翌日",
    "2026-04-28": "FY25決算・FY26予想の翌日",
    "2026-07-28": "米半導体安",
    "2026-07-30": "Q1決算・通期上方修正の翌日",
    "2026-07-31": "米半導体の急反発、引け後に日経がキャップ調整を公表",
    "2026-08-18": "8/14高値後の調整",
    "2026-09-11": "前夜の米半導体安",
    "2026-09-14": "AI開発ペース抑制論・OpenAI上場見送り報道",
    "2026-09-15": "前夜（米9/14）TER−13%・SOX−6%",
    "2026-09-18": "日銀会合（利上げ・反対2人）",
    "2026-09-24": "AI関連の反発",
    "2026-09-30": "日経平均キャップ調整の引けリバランス",
    "2026-10-01": "Micron決算の翌朝",
    "2026-10-02": "1年来高値（日中）",
}


def fname(sym, rng="2y"):
    return os.path.join(WORK, "yahoo-chart-%s-%s.json" % (sym.replace("^", "_").replace("=", "_"), rng))


def fetch(sym, rng="2y", interval="1d"):
    url = ("https://query1.finance.yahoo.com/v8/finance/chart/%s?range=%s&interval=%s&events=div%%2Csplits"
           % (urllib.parse.quote(sym), rng, interval))
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    data["_retrieved"] = dt.datetime.now(dt.timezone.utc).isoformat()
    data["_url"] = url
    with open(fname(sym, rng), "w") as f:
        json.dump(data, f)
    time.sleep(0.4)


def load(sym):
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
        if day > AS_OF and sym not in US and sym != "JPY=X":
            continue
        if sym in US and day > "2026-10-02":
            continue
        rows[day] = {"o": q["open"][i], "h": q["high"][i], "l": q["low"][i], "c": c, "v": q["volume"][i]}
    return dict(sorted(rows.items()))


def rets(rows):
    days = list(rows)
    return {days[i]: rows[days[i]]["c"] / rows[days[i - 1]]["c"] - 1 for i in range(1, len(days))}


def corr(x, y):
    n = len(x)
    if n < 3:
        return float("nan")
    mx, my = sum(x) / n, sum(y) / n
    sx = math.sqrt(sum((a - mx) ** 2 for a in x))
    sy = math.sqrt(sum((b - my) ** 2 for b in y))
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)


def corr_ci(r, n):
    z = math.atanh(r)
    se = 1 / math.sqrt(n - 3)
    return math.tanh(z - 1.96 * se), math.tanh(z + 1.96 * se)


def ols_beta(y, x):
    mx, my = statistics.mean(x), statistics.mean(y)
    b = sum((a - mx) * (c - my) for a, c in zip(x, y)) / sum((a - mx) ** 2 for a in x)
    return b, my - b * mx


def pct(v):
    return "%+.1f%%" % (100 * v)


def lookup(table, day):
    for start, v in table:
        if day >= start:
            return v
    return table[-1][1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    a = ap.parse_args()
    os.makedirs(WORK, exist_ok=True)
    if not a.offline:
        for s in SYMBOLS:
            try:
                fetch(s)
            except Exception as e:  # noqa: BLE001
                print("fetch failed", s, e, file=sys.stderr)
        try:
            fetch("6857.T", "10y", "1mo")  # 分割履歴の確認用
        except Exception as e:  # noqa: BLE001
            print("fetch failed 6857 10y", e, file=sys.stderr)
    data = {s: load(s) for s in SYMBOLS if os.path.exists(fname(s))}
    R = {s: rets(v) for s, v in data.items()}
    A = data["6857.T"]
    adays = list(A)
    out = {}

    # 分割履歴
    sp = os.path.join(WORK, "yahoo-chart-6857.T-10y.json")
    if os.path.exists(sp):
        with open(sp) as f:
            ev = json.load(f)["chart"]["result"][0].get("events", {}).get("splits", {})
        out["splits"] = [(dt.datetime.fromtimestamp(v["date"], dt.timezone.utc).date().isoformat(), v["splitRatio"])
                         for v in ev.values()]
        print("== 0. 6857 分割履歴（Yahoo、直近10年）:", out["splits"])

    # ---- 1. 騰落率・値動きの特徴
    def close_on_or_before(sym, day):
        ds = [d for d in data[sym] if d <= day]
        return data[sym][ds[-1]]["c"]
    anchors = {"2025-10-02": "1年前", "2026-03-31": "3/31", "2026-06-30": "6/30", "2026-07-29": "7/29(決算日)",
               "2026-09-04": "9/4", "2026-09-11": "9/11", "2026-09-15": "9/15", "2026-09-17": "9/17", "2026-09-30": "9/30"}
    perf = {}
    # 1306.TはYahooの日足が2026-03-30〜04-01の分割（1→10とみられる）を調整していないため騰落率から除外
    for s in ["6857.T", "^N225", "285A.T", "4062.T", "8035.T", "2330.TW", "000660.KS",
              "NVDA", "TER", "TSM", "AVGO", "AMD", "MU", "LRCX", "ASML", "^SOX"]:
        if s not in data:
            continue
        last = close_on_or_before(s, AS_OF)
        perf[s] = {lab: last / close_on_or_before(s, d) - 1 for d, lab in anchors.items()}
        perf[s]["last"] = last
    out["performance"] = perf
    print("== 1. 騰落率（各日の終値→直近終値。米国・台湾・韓国は10/2の現地終値）")
    print("%-10s" % "", "  ".join("%11s" % l for l in anchors.values()), "     last")
    for s, p in perf.items():
        print("%-10s" % s, "  ".join("%11s" % pct(p[l]) for l in anchors.values()), "%10.2f" % p["last"])

    common = [d for d in adays[1:] if all(d in R[s] for s in TOKYO if s in R)]
    y1 = [d for d in common if d >= ONE_YEAR_START]
    windows = {"20日": common[-20:], "60日": common[-60:], "120日": common[-120:], "約1年": y1}
    print("\n-- 東京の共通営業日：約1年 %d日（%s〜%s）" % (len(y1), y1[0], y1[-1]))
    out["vol"], out["beta"] = {}, {}
    for s in ["6857.T", "^N225", "8035.T", "285A.T", "NVDA", "TER", "^SOX"]:
        rs = R[s]
        for lab, n in [("60日", 60), ("1年", None)]:
            ks = [d for d in rs if d >= ONE_YEAR_START] if n is None else list(rs)[-n:]
            x = [rs[d] for d in ks]
            out["vol"]["%s %s" % (s, lab)] = dict(
                annVol=statistics.pstdev(x) * math.sqrt(250), meanAbs=statistics.mean(abs(t) for t in x),
                days10=sum(1 for t in x if abs(t) >= 0.10), days5=sum(1 for t in x if abs(t) >= 0.05), days3=sum(1 for t in x if abs(t) >= 0.03), n=len(x))
        v6, v1 = out["vol"][s + " 60日"], out["vol"][s + " 1年"]
        print("%-8s 年率ボラ 60日 %.0f%% / 1年 %.0f%%、平均絶対日次 60日 %.2f%%、|日次|≥5%%の日 60日 %d / 1年 %d、≥3%% 60日 %d、|日次|≥10%%の日 1年 %d" % (
            s, 100 * v6["annVol"], 100 * v1["annVol"], 100 * v6["meanAbs"], v6["days5"], v1["days5"], v6["days3"], v1["days10"]))
    print("-- 6857のβ・相関（対日経平均・TOPIX連動ETF・TEL・キオクシア）。1306.Tの『約1年』は4/2以降に限定")
    for mk in ["^N225", "1306.T", "8035.T", "285A.T"]:
        for lab, ds in windows.items():
            if mk == "1306.T" and ds[0] < "2026-04-02":
                ds = [d for d in ds if d >= "2026-04-02"]  # 未調整の分割をまたがない
            y = [R["6857.T"][d] for d in ds]; x = [R[mk][d] for d in ds]
            b, _ = ols_beta(y, x); r = corr(y, x)
            out["beta"]["%s %s" % (mk, lab)] = dict(beta=b, corr=r, n=len(ds))
        print("%-7s" % mk, "  ".join("%s β%.2f r%.2f" % (lab, out["beta"]["%s %s" % (mk, lab)]["beta"],
                                                         out["beta"]["%s %s" % (mk, lab)]["corr"]) for lab in windows))

    gaps = {d: A[d]["o"] / A[adays[i - 1]]["c"] - 1 for i, d in enumerate(adays) if i > 0}
    g60 = [gaps[d] for d in adays[-60:]]
    out["gaps60"] = dict(ge3=sum(1 for g in g60 if abs(g) >= 0.03), meanAbs=statistics.mean(abs(g) for g in g60))
    print("6857 寄り付きギャップ（直近60日）: |gap|≥3%% %d日、平均絶対 %.2f%%" % (out["gaps60"]["ge3"], 100 * out["gaps60"]["meanAbs"]))
    big = sorted([d for d in y1], key=lambda d: -abs(R["6857.T"][d]))[:15]
    out["bigDays"] = {d: dict(r6857=R["6857.T"][d], n225=R["^N225"][d], gap=gaps[d]) for d in sorted(big)}
    print("6857 約1年の大きな日次（上位15）:")
    for d in sorted(big):
        print("   %s 6857 %s（寄り %s） 日経 %s" % (d, pct(R["6857.T"][d]), pct(gaps[d]), pct(R["^N225"][d])))

    # ---- 2. 日経平均への寄与度
    print("\n== 2. 日経平均への寄与度（株価換算係数×株価変化÷除数、除数は報道値からの逆算・近似）")
    N = data["^N225"]
    contrib = {}
    for i, d in enumerate(adays):
        if i == 0 or d < "2026-04-01" or d not in N:
            continue
        prev = adays[i - 1]
        coef_today = lookup(COEF, d)
        div = lookup(DIVISOR, d)
        # 係数が切り替わる日は、前日終値も新しい係数で評価した寄与度（指数の連続性を保つ扱い）
        contrib[d] = (A[d]["c"] - A[prev]["c"]) * coef_today / div
    print("-- 報道値との照合")
    out["contribCheck"] = {}
    for d, rep in REPORTED_CONTRIB.items():
        est = contrib.get(d)
        out["contribCheck"][d] = (est, rep)
        print("   %s 推計 %+.0f円 / 報道 %+.0f円" % (d, est, rep))
    last = AS_OF
    coef = lookup(COEF, last); div = lookup(DIVISOR, last)
    pts_per_1pct = A[last]["c"] * 0.01 * coef / div
    weight = A[last]["c"] * coef / div / N[last]["c"]
    out["nikkei"] = dict(close6857=A[last]["c"], coef=coef, divisor=div, ptsPer1pct=pts_per_1pct,
                         weight=weight, n225=N[last]["c"])
    print("10/2: 6857終値 %.0f円、係数 %.1f、除数 %.2f → 6857が1%%動くと日経平均は約%.0f円。構成比率（推計）%.1f%%（日経平均 %.0f円）" % (
        A[last]["c"], coef, div, pts_per_1pct, 100 * weight, N[last]["c"]))
    # 係数7.2のままだった場合（参考）
    w72 = A[last]["c"] * 7.2 / div / N[last]["c"]
    out["nikkei"]["weightIfCoef72"] = w72
    print("   参考：係数7.2のままなら構成比率 %.1f%%" % (100 * w72))
    for dd in ("2026-07-31", "2026-09-30"):
        c0 = lookup(COEF, dd); w = A[dd]["c"] * c0 / lookup(DIVISOR, dd) / N[dd]["c"]
        out["nikkei"]["weight_" + dd] = w
        print("   %s時点の構成比率（推計、係数%.1f）%.1f%%" % (dd, c0, 100 * w))
    # 寄与の比率・日経平均から6857を除いた指数
    cd = [d for d in common if d in contrib and d >= "2026-04-02"]
    share = []
    exret, a6 = [], []
    for d in cd:
        prevN = N[[x for x in N if x < d][-1]]["c"]
        dN = N[d]["c"] - prevN
        exret.append((dN - contrib[d]) / (prevN - lookup(COEF, d) * A[[x for x in adays if x < d][-1]]["c"] / lookup(DIVISOR, d)))
        a6.append(R["6857.T"][d])
        if abs(dN) > 0:
            share.append(contrib[d] / dN)
    absc = [abs(contrib[d]) for d in cd]
    absN = [abs(N[d]["c"] - N[[x for x in N if x < d][-1]]["c"]) for d in cd]
    out["contribStats"] = dict(n=len(cd), meanAbsContrib=statistics.mean(absc), meanAbsN=statistics.mean(absN),
                               ratioOfMeans=sum(absc) / sum(absN), medianShare=statistics.median(share))
    print("4/2〜10/2（%d日）：6857の寄与度の平均絶対値 %.0f円、日経平均の日次変化の平均絶対値 %.0f円（比 %.0f%%）、日々の寄与比率の中央値 %.0f%%" % (
        len(cd), statistics.mean(absc), statistics.mean(absN), 100 * sum(absc) / sum(absN), 100 * statistics.median(share)))
    top = sorted(cd, key=lambda d: -abs(contrib[d]))[:8]
    out["contribTop"] = {d: contrib[d] for d in sorted(top)}
    print("   寄与度の大きい日:", ", ".join("%s %+.0f円" % (d, contrib[d]) for d in sorted(top)))
    # 日経平均（6857を除く）に対するβ・相関
    for lab, n in [("60日", 60), ("4/2以降", len(cd))]:
        y = a6[-n:]; x = exret[-n:]
        b, _ = ols_beta(y, x); r = corr(y, x)
        bn, _ = ols_beta(y, [R["^N225"][d] for d in cd[-n:]])
        out.setdefault("betaEx", {})[lab] = dict(beta=b, corr=r, betaN225=bn, n=n)
        print("   6857の日経平均（6857除く）に対するβ %.2f 相関 %.2f（同期間の日経平均そのものに対するβ %.2f）[%s]" % (b, r, bn, lab))

    # ---- 3. 米国前夜 -> 東京の6857
    print("\n== 3. 米国前夜の騰落 -> 東京の6857（寄り付きギャップ・終値・寄り→引け）")
    out["us_overnight"] = {}
    for win_lab, win in [("120日", common[-120:]), ("約1年", y1)]:
        wset = set(win)
        for us in US:
            ur = R.get(us, {})
            ud = sorted(ur)
            xs, gap, cc, oc = [], [], [], []
            for i, d in enumerate(adays[1:], 1):
                if d not in wset:
                    continue
                prev = [u for u in ud if u < d]
                if not prev or prev[-1] < adays[i - 1]:
                    continue
                xs.append(ur[prev[-1]])
                gap.append(gaps[d])
                cc.append(R["6857.T"][d])
                oc.append(A[d]["c"] / A[d]["o"] - 1)
            cg, ccc, coc = corr(xs, gap), corr(xs, cc), corr(xs, oc)
            bg, _ = ols_beta(gap, xs); bc, _ = ols_beta(cc, xs)
            same = sum(1 for a2, b2 in zip(xs, cc) if (a2 > 0) == (b2 > 0)) / len(xs)
            out["us_overnight"]["%s %s" % (us, win_lab)] = dict(n=len(xs), corrGap=cg, corrClose=ccc, corrOpenToClose=coc,
                                                                betaGap=bg, betaClose=bc, sameSign=same)
            print("%-5s %-6s n=%d 寄りギャップ相関 %.2f(β%.2f) 終値相関 %.2f(β%.2f) 寄り→引け相関 %+.2f 同方向 %.0f%%" % (
                win_lab, us, len(xs), cg, bg, ccc, bc, coc, 100 * same))
    # TERが±5%以上動いた夜の翌日
    ur = R["TER"]; ud = sorted(ur)
    bigTER = []
    for i, d in enumerate(adays[1:], 1):
        if d < ONE_YEAR_START:
            continue
        prev = [u for u in ud if u < d]
        if not prev or prev[-1] < adays[i - 1]:
            continue
        if abs(ur[prev[-1]]) >= 0.05:
            bigTER.append((prev[-1], ur[prev[-1]], d, gaps[d], R["6857.T"][d]))
    out["bigTERnights"] = bigTER
    up = [t for t in bigTER if t[1] > 0]; dn = [t for t in bigTER if t[1] < 0]
    print("TERが±5%%以上動いた夜（約1年）：上昇%d回→翌日6857の寄り平均 %s・終値平均 %s／下落%d回→寄り平均 %s・終値平均 %s" % (
        len(up), pct(statistics.mean(t[3] for t in up)) if up else "-", pct(statistics.mean(t[4] for t in up)) if up else "-",
        len(dn), pct(statistics.mean(t[3] for t in dn)) if dn else "-", pct(statistics.mean(t[4] for t in dn)) if dn else "-"))

    # ---- 4. アジア同日
    print("\n== 4. 同じ時間帯のアジア株との同日相関（6857）")
    out["asia_sameday"] = {}
    for s in ASIA:
        for lab, ds0 in [("120日", common[-120:]), ("約1年", y1)]:
            ds = [d for d in ds0 if d in R.get(s, {})]
            r = corr([R["6857.T"][d] for d in ds], [R[s][d] for d in ds])
            out["asia_sameday"]["%s %s" % (s, lab)] = (r, len(ds))
        print("%-10s 120日 %.2f / 約1年 %.2f" % (s, out["asia_sameday"][s + " 120日"][0], out["asia_sameday"][s + " 約1年"][0]))
    ds = [d for d in common[-120:] if d in R.get("JPY=X", {})]
    out["usdjpy_corr120"] = corr([R["6857.T"][d] for d in ds], [R["JPY=X"][d] for d in ds])
    print("ドル円(同日付)相関(120日) %.2f n=%d（日付ずれあり、参考）" % (out["usdjpy_corr120"], len(ds)))

    # ---- 5. 決算反応
    print("\n== 5. 決算発表（引け後）の反応：発表日・翌営業日")
    out["earnings"] = {}
    for e in EARNINGS:
        if e not in A:
            continue
        i = adays.index(e)
        nx = adays[i + 1]
        nx2 = adays[i + 2] if i + 2 < len(adays) else nx
        # 前夜SOX（翌営業日の直前の米国取引日）
        ud = sorted(R["^SOX"])
        us_prev = [u for u in ud if u < nx and u >= e]
        sox = R["^SOX"][us_prev[-1]] if us_prev else float("nan")
        row = dict(day=R["6857.T"][e], nextDay=nx, gap=gaps[nx], close=R["6857.T"][nx],
                   n225=R["^N225"][nx], soxPrevNight=sox, twoDay=A[nx2]["c"] / A[e]["c"] - 1,
                   rel=R["6857.T"][nx] - R["^N225"][nx])
        out["earnings"][e] = row
        print("%s 当日 %s → 翌%s 寄り %s 終値 %s（日経 %s、前夜SOX %s、発表日終値→翌々営業日終値 %s）" % (
            e, pct(row["day"]), nx, pct(row["gap"]), pct(row["close"]), pct(row["n225"]), pct(sox), pct(row["twoDay"])))
    ab = [abs(v["close"]) for v in out["earnings"].values()]
    allabs = statistics.mean(abs(R["6857.T"][d]) for d in y1)
    out["earningsStats"] = dict(meanAbsNextDay=statistics.mean(ab), meanAbsAllDays1y=allabs)
    print("翌営業日の終値の平均絶対値 %.1f%%（約1年の全営業日 %.1f%%）" % (100 * statistics.mean(ab), 100 * allabs))

    # ---- 6. イベント日・テクニカル
    print("\n== 6. 個別イベント日の値動き（6857、日経平均、前夜SOX・NVDA・TER）")
    out["events"] = {}
    for d, lab in EVENTS.items():
        if d not in R["6857.T"]:
            continue
        i = adays.index(d)
        def prev_us(sym):
            ud = sorted(R[sym])
            p = [u for u in ud if u < d and u >= adays[i - 1]]
            return R[sym][p[-1]] if p else float("nan")
        row = dict(label=lab, r=R["6857.T"][d], gap=gaps[d], close=A[d]["c"], high=A[d]["h"], n225=R["^N225"][d],
                   sox=prev_us("^SOX"), nvda=prev_us("NVDA"), ter=prev_us("TER"), vol=A[d]["v"])
        out["events"][d] = row
        print("%s %-28s 6857 %s（寄り %s、終値 %.0f） 日経 %s 前夜SOX %s NVDA %s TER %s 出来高 %.1f百万株" % (
            d, lab, pct(row["r"]), pct(row["gap"]), row["close"], pct(row["n225"]), pct(row["sox"]), pct(row["nvda"]),
            pct(row["ter"]), row["vol"] / 1e6))

    print("\n-- テクニカル")
    closes = [A[d]["c"] for d in adays]
    ma = {n: statistics.mean(closes[-n:]) for n in (5, 25, 75, 200)}
    y1days = [d for d in adays if d >= ONE_YEAR_START]
    hi_d = max(y1days, key=lambda d: A[d]["h"]); lo_d = min(y1days, key=lambda d: A[d]["l"])
    out["technical"] = dict(close=closes[-1], ma=ma, high1y=(hi_d, A[hi_d]["h"]), low1y=(lo_d, A[lo_d]["l"]),
                            dev25=closes[-1] / ma[25] - 1, dev75=closes[-1] / ma[75] - 1, dev200=closes[-1] / ma[200] - 1)
    print("終値 %.0f、移動平均 5日 %.0f / 25日 %.0f / 75日 %.0f / 200日 %.0f（乖離 25日 %s、75日 %s、200日 %s）" % (
        closes[-1], ma[5], ma[25], ma[75], ma[200], pct(out["technical"]["dev25"]), pct(out["technical"]["dev75"]),
        pct(out["technical"]["dev200"])))
    print("約1年の高値 %.0f（%s）、安値 %.0f（%s）" % (A[hi_d]["h"], hi_d, A[lo_d]["l"], lo_d))
    # 終値ベースの高値・最大下落
    cl_hi_d = max(y1days, key=lambda d: A[d]["c"])
    print("約1年の終値高値 %.0f（%s）" % (A[cl_hi_d]["c"], cl_hi_d))
    # 2026年の主な高値・安値（月別）
    print("-- 月別の高値・安値・終値・平均出来高（2026年）")
    out["monthly"] = {}
    for m in ["2026-%02d" % k for k in range(1, 11)]:
        ds = [d for d in adays if d.startswith(m)]
        if not ds:
            continue
        hi = max(A[d]["h"] for d in ds); lo = min(A[d]["l"] for d in ds)
        out["monthly"][m] = dict(high=hi, low=lo, close=A[ds[-1]]["c"], avgVol=statistics.mean(A[d]["v"] for d in ds))
        print("   %s 高値 %.0f 安値 %.0f 月末終値 %.0f 平均出来高 %.1f百万株" % (m, hi, lo, A[ds[-1]]["c"],
                                                                 out["monthly"][m]["avgVol"] / 1e6))
    seg = [d for d in adays if d >= "2026-07-01"]
    piv_h, piv_l = [], []
    for i in range(2, len(seg) - 2):
        d = seg[i]
        if A[d]["h"] == max(A[x]["h"] for x in seg[i - 2:i + 3]):
            piv_h.append((d, A[d]["h"]))
        if A[d]["l"] == min(A[x]["l"] for x in seg[i - 2:i + 3]):
            piv_l.append((d, A[d]["l"]))
    out["pivots"] = {"highs": piv_h, "lows": piv_l}
    print("スイング高値(前後2日, 7月以降):", ", ".join("%s %.0f" % t for t in piv_h))
    print("スイング安値(前後2日, 7月以降):", ", ".join("%s %.0f" % t for t in piv_l))
    vp = {}
    for lab, a0, a1 in [("7月", "2026-07-01", "2026-07-31"), ("8月", "2026-08-01", "2026-08-31"),
                        ("9/1-9/18", "2026-09-01", "2026-09-18"), ("9/24-10/2", "2026-09-24", "2026-10-02")]:
        xs = [A[d]["v"] for d in adays if a0 <= d <= a1]
        vp[lab] = (statistics.mean(xs), len(xs))
    out["volumeByPeriod"] = vp
    print("平均出来高:", ", ".join("%s %.1f百万株(%d日)" % (k, v[0] / 1e6, v[1]) for k, v in vp.items()))

    # ---- 7. 会社予想に対する簡単な感応度（会社開示の数値を使った機械的な計算）
    print("\n== 7. 会社予想ベースの簡単な計算（独自計算）")
    eps_fy26, eps_ttm = 911.64, 515.15  # 会社予想（2026-07-29）基本的EPS、FY25実績（Yahoo TTM、2026年3月期）
    px = A[AS_OF]["c"]
    fx = data.get("JPY=X", {})
    def fx_avg(a0, a1):
        xs = [fx[d]["c"] for d in fx if a0 <= d <= a1]
        return statistics.mean(xs) if xs else float("nan")
    q2 = fx_avg("2026-07-01", "2026-09-30")
    last_fx = fx[[d for d in fx if d <= "2026-10-02"][-1]]["c"]
    sens = 53.0  # 億円／1円（対ドル、通期ベース）。会社の前提は2Q以降1ドル150円
    up_q2 = (q2 - 150) * sens / 4
    up_h2 = (last_fx - 150) * sens / 2
    out["valuation_fx"] = dict(perFY26=px / eps_fy26, perTTM=px / eps_ttm, usdjpyQ2avg=q2, usdjpyLast=last_fx,
                               fxUpsideQ2=up_q2, fxUpsideH2=up_h2, fxUpsideTotal=up_q2 + up_h2,
                               fxUpsidePctOfOI=(up_q2 + up_h2) / 8460)
    print("PER：会社予想EPS %.2f円で %.1f倍、FY25実績EPS %.2f円で %.1f倍（株価 %.0f円）" % (eps_fy26, px / eps_fy26, eps_ttm, px / eps_ttm, px))
    print("ドル円：7〜9月平均 %.2f円（Yahoo日足の単純平均）、10/2 %.2f円。前提150円との差×53億円/円 → 2Q分 約%.0f億円＋下期（10/2の水準が続く場合）約%.0f億円＝約%.0f億円（通期営業利益予想8,460億円の%.1f%%）" % (
        q2, last_fx, up_q2, up_h2, up_q2 + up_h2, 100 * (up_q2 + up_h2) / 8460))

    # キオクシア版の数値との整合確認（同じ窓・同じ方法）
    print("\n-- キオクシア版との整合確認：6857~N225 60日相関 %.2f、β %.2f、6857~285A 60日相関 %.2f" % (
        out["beta"]["^N225 60日"]["corr"], out["beta"]["^N225 60日"]["beta"], out["beta"]["285A.T 60日"]["corr"]))

    with open(os.path.join(WORK, "stock-drivers-results.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=str)


if __name__ == "__main__":
    main()
