#!/usr/bin/env python3
"""イビデン（4062）株価変動要因レポート（2026-10-03）の再現用計算。

標準ライブラリのみ。Yahoo Finance公開チャートAPI（キー不要、分割調整済み日足）から
日足OHLCVを取得して working/yahoo-chart-<symbol>-2y.json に保存し、次を計算する。
アドバンテスト版（../../6857-advantest/2026-10-03/stock_drivers.py）・キオクシア版と同じ方法・同じ窓で、
イビデン固有の分析を追加する。

  1. 騰落率（期間別）と値動きの特徴（ボラティリティ、β、大きな日、出来高）
  2. 日経平均への寄与度（株価換算係数×株価変化÷除数）と構成比率
  3. 米国・欧州（NVDA・INTC・AMD・TSM・AVGO・MU・SOX・AT&S）の前夜の値動きと翌営業日の4062
  4. 同じ時間帯の台湾（Unimicron・Nan Ya PCB・Kinsus・TSMC）・韓国との同日相関
  5. 決算発表翌営業日の反応
  6. 株式分割（2025-12-29・2026-09-29の権利落ち）前後の値動き・売買代金
  7. 個別イベント日の値動き、テクニカル（移動平均・高値・安値・節目）
  8. キオクシア・アドバンテスト・東京エレクトロンとの連動（キオクシア版の数値との整合確認を含む）
  9. 会社予想ベースの簡単な計算（PER、CBの潜在株式）

使い方:
  python3 stock_drivers.py            # 取得して計算（取得データは working/ に保存）
  python3 stock_drivers.py --offline  # working/ の保存データだけで再計算

株価はすべてYahoo Financeの分割調整後の円（4062は2026-01-01効力・2026-10-01効力の各1対2分割を調整済み。
2025年12月以前の株価は分割前の4分の1、2026年1〜9月の株価は分割前の2分の1に換算されている）。
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
ONE_YEAR_START = "2025-10-03"  # キオクシア版・アドバンテスト版の「約1年」と同じ起点

SYMBOLS = {
    "4062.T": "イビデン", "^N225": "日経平均", "1306.T": "TOPIX連動ETF",
    "285A.T": "キオクシア", "6857.T": "アドバンテスト", "8035.T": "東京エレクトロン", "2802.T": "味の素",
    "3037.TW": "Unimicron", "8046.TW": "Nan Ya PCB", "3189.TW": "Kinsus", "2330.TW": "TSMC(台湾)",
    "000660.KS": "SK hynix",
    "NVDA": "NVIDIA", "INTC": "Intel", "AMD": "AMD", "TSM": "TSMC ADR", "AVGO": "Broadcom", "MU": "Micron",
    "^SOX": "SOX指数", "ATS.VI": "AT&S(ウィーン)", "JPY=X": "ドル円",
}
TOKYO = ["4062.T", "^N225", "1306.T", "285A.T", "6857.T", "8035.T"]
ASIA = ["3037.TW", "8046.TW", "3189.TW", "2330.TW", "000660.KS"]
# 東京の取引終了後に取引が終わる市場（翌営業日の東京に対応させる）
OVERNIGHT = ["NVDA", "INTC", "AMD", "TSM", "AVGO", "MU", "^SOX", "ATS.VI"]

# 日経平均の株価換算係数：4062はみなし額面50円で係数1.0、2026-01-01の分割で2.0、2026-10-01の分割で4.0
#   【検証】9/24：分割前株価+2,850円、寄与度191.08円（財経新聞・Fisco）→ 2,850×2.0÷29.83 = 191.08
#           10/2：+105円、寄与度+14.16円（Fisco）→ 105×4.0÷29.70 = 14.14
# 分割調整後の株価に対しては、係数4.0を一貫して使えば分割前の「実株価×当時の係数」と同じ値になる。
COEF_ADJ = 4.0
# 除数：報道された寄与度から逆算した近似値（アドバンテスト版と同じ。9/30以前29.83、10/1以降29.70）
DIVISOR = [("2026-09-30", 29.70), ("0000-00-00", 29.83)]
REPORTED_CONTRIB = {"2026-09-24": 191.08, "2026-10-02": 14.16}

# 決算発表日（会社IRカレンダー。発表時刻は2024-10-31 15:20、2026-02-03 15:30、ほかは15:40。
# いずれも東証の取引終了後。次回2026-10-29は15:20予定で、大引け（15:30）前にあたる）
EARNINGS = ["2024-10-31", "2025-02-04", "2025-05-08", "2025-08-01", "2025-10-30",
            "2026-02-03", "2026-05-11", "2026-08-04"]
SPLIT_EX = ["2025-12-29", "2026-09-29"]
EVENTS = {
    "2025-10-31": "Q2決算・通期上方修正・1対2分割・累進配当の発表翌日",
    "2026-01-15": "豊田自動織機TOBへの応募発表（売却益）",
    "2026-02-04": "Q3決算・河間2,200億円の投資発表の翌日",
    "2026-02-25": "売出し（687万株）発表の翌日",
    "2026-02-27": "大野2,800億円の投資発表の翌日",
    "2026-03-05": "売出価格の決定（7,632円、分割調整後3,816円）",
    "2026-05-12": "FY25決算・FY26予想の翌日",
    "2026-08-05": "Q1決算・通期大幅上方修正・1対2分割発表の翌日",
    "2026-07-28": "米半導体安",
    "2026-07-30": "アドバンテスト決算の翌日",
    "2026-07-31": "米半導体の急反発",
    "2026-09-11": "前夜の米半導体安",
    "2026-09-14": "AI開発ペース抑制論・OpenAI上場見送り報道",
    "2026-09-15": "前夜（米9/14）SOX−6%",
    "2026-09-18": "日銀会合（利上げ・反対2人）",
    "2026-09-24": "NVIDIA CEOとの会談の報道",
    "2026-09-25": "急騰の翌日",
    "2026-09-29": "1対2分割の権利落ち",
    "2026-09-30": "日経平均キャップ調整（6857）の引けリバランス",
    "2026-10-01": "分割の効力発生・Micron決算の翌朝",
    "2026-10-02": "直近",
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
        if day > AS_OF:
            continue
        rows[day] = {"o": q["open"][i], "h": q["high"][i], "l": q["low"][i], "c": c, "v": q["volume"][i] or 0}
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


def ols_beta(y, x):
    mx, my = statistics.mean(x), statistics.mean(y)
    b = sum((a - mx) * (c - my) for a, c in zip(x, y)) / sum((a - mx) ** 2 for a in x)
    return b, my - b * mx


def pct(v):
    return "%+.1f%%" % (100 * v) if v == v else "  n/a"


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
            fetch("4062.T", "10y", "1mo")  # 分割履歴の確認用
        except Exception as e:  # noqa: BLE001
            print("fetch failed 4062 10y", e, file=sys.stderr)
    data = {s: load(s) for s in SYMBOLS if os.path.exists(fname(s))}
    R = {s: rets(v) for s, v in data.items()}
    I = data["4062.T"]
    idays = list(I)
    out = {}

    sp = os.path.join(WORK, "yahoo-chart-4062.T-10y.json")
    if os.path.exists(sp):
        with open(sp) as f:
            ev = json.load(f)["chart"]["result"][0].get("events", {}).get("splits", {})
        out["splits"] = sorted((dt.datetime.fromtimestamp(v["date"], dt.timezone.utc).date().isoformat(), v["splitRatio"])
                               for v in ev.values())
        print("== 0. 4062 分割履歴（Yahoo、直近10年。日付は権利落ち日）:", out["splits"])

    def close_on_or_before(sym, day):
        ds = [d for d in data[sym] if d <= day]
        return data[sym][ds[-1]]["c"]

    # ---- 1. 騰落率
    anchors = {"2025-10-02": "1年前", "2025-12-30": "年初来", "2026-03-31": "3/31", "2026-06-30": "6/30",
               "2026-08-04": "8/4(決算日)", "2026-09-04": "9/4", "2026-09-15": "9/15", "2026-09-17": "9/17",
               "2026-09-24": "9/24"}
    perf = {}
    for s in ["4062.T", "^N225", "285A.T", "6857.T", "8035.T", "2802.T", "3037.TW", "8046.TW", "3189.TW",
              "2330.TW", "ATS.VI", "NVDA", "INTC", "AMD", "TSM", "AVGO", "^SOX"]:
        if s not in data:
            continue
        last = close_on_or_before(s, AS_OF)
        perf[s] = {lab: last / close_on_or_before(s, d) - 1 for d, lab in anchors.items()}
        perf[s]["last"] = last
    out["performance"] = perf
    print("== 1. 騰落率（各日の終値→直近終値。海外は10/2の現地終値。年初来は2025-12-30終値から）")
    print("%-10s" % "", "  ".join("%11s" % l for l in anchors.values()), "     last")
    for s, p in perf.items():
        print("%-10s" % s, "  ".join("%11s" % pct(p[l]) for l in anchors.values()), "%10.2f" % p["last"])

    common = [d for d in idays[1:] if all(d in R[s] for s in TOKYO if s in R)]
    y1 = [d for d in common if d >= ONE_YEAR_START]
    windows = {"20日": common[-20:], "60日": common[-60:], "120日": common[-120:], "約1年": y1}
    print("\n-- 東京の共通営業日：約1年 %d日（%s〜%s）" % (len(y1), y1[0], y1[-1]))
    out["vol"], out["beta"] = {}, {}
    for s in ["4062.T", "^N225", "6857.T", "8035.T", "285A.T", "3037.TW", "NVDA", "INTC", "^SOX"]:
        rs = R[s]
        for lab, n in [("60日", 60), ("1年", None)]:
            ks = [d for d in rs if d >= ONE_YEAR_START] if n is None else list(rs)[-n:]
            x = [rs[d] for d in ks]
            out["vol"]["%s %s" % (s, lab)] = dict(
                annVol=statistics.pstdev(x) * math.sqrt(250), meanAbs=statistics.mean(abs(t) for t in x),
                days10=sum(1 for t in x if abs(t) >= 0.10), days5=sum(1 for t in x if abs(t) >= 0.05),
                days3=sum(1 for t in x if abs(t) >= 0.03), n=len(x))
        v6, v1 = out["vol"][s + " 60日"], out["vol"][s + " 1年"]
        print("%-8s 年率ボラ 60日 %.0f%% / 1年 %.0f%%、平均絶対日次 60日 %.2f%%、|日次|≥5%%の日 60日 %d / 1年 %d、≥3%% 60日 %d、≥10%% 1年 %d" % (
            s, 100 * v6["annVol"], 100 * v1["annVol"], 100 * v6["meanAbs"], v6["days5"], v1["days5"], v6["days3"], v1["days10"]))
    print("-- 4062のβ・相関。1306.Tは4/2以降に限定（Yahooの日足が2026年3月末の分割を未調整）")
    for mk in ["^N225", "1306.T", "6857.T", "285A.T", "8035.T"]:
        for lab, ds in windows.items():
            if mk == "1306.T":
                ds = [d for d in ds if d >= "2026-04-02"]
            y = [R["4062.T"][d] for d in ds]; x = [R[mk][d] for d in ds]
            b, _ = ols_beta(y, x); r = corr(y, x)
            out["beta"]["%s %s" % (mk, lab)] = dict(beta=b, corr=r, n=len(ds))
        print("%-7s" % mk, "  ".join("%s β%.2f r%.2f" % (lab, out["beta"]["%s %s" % (mk, lab)]["beta"],
                                                         out["beta"]["%s %s" % (mk, lab)]["corr"]) for lab in windows))

    gaps = {d: I[d]["o"] / I[idays[i - 1]]["c"] - 1 for i, d in enumerate(idays) if i > 0}
    g60 = [gaps[d] for d in idays[-60:]]
    out["gaps60"] = dict(ge3=sum(1 for g in g60 if abs(g) >= 0.03), meanAbs=statistics.mean(abs(g) for g in g60))
    print("4062 寄り付きギャップ（直近60日）: |gap|≥3%% %d日、平均絶対 %.2f%%" % (out["gaps60"]["ge3"], 100 * out["gaps60"]["meanAbs"]))
    big = sorted(y1, key=lambda d: -abs(R["4062.T"][d]))[:18]
    out["bigDays"] = {d: dict(r=R["4062.T"][d], n225=R["^N225"][d], gap=gaps[d], r6857=R["6857.T"][d]) for d in sorted(big)}
    print("4062 約1年の大きな日次（上位18）:")
    def prev_night(sym, d):
        i = idays.index(d)
        p = [u for u in sorted(R[sym]) if idays[i - 1] <= u < d]
        return R[sym][p[-1]] if p else float("nan")
    for d in sorted(big):
        out["bigDays"][d].update(intc=prev_night("INTC", d), nvda=prev_night("NVDA", d), sox=prev_night("^SOX", d))
        print("   %s 4062 %s（寄り %s） 日経 %s 6857 %s 前夜INTC %s NVDA %s SOX %s 出来高 %.1f百万株" % (
            d, pct(R["4062.T"][d]), pct(gaps[d]), pct(R["^N225"][d]), pct(R["6857.T"][d]), pct(prev_night("INTC", d)),
            pct(prev_night("NVDA", d)), pct(prev_night("^SOX", d)), I[d]["v"] / 1e6))

    # ---- 2. 日経平均への寄与度
    print("\n== 2. 日経平均への寄与度（調整後株価の変化×係数4.0÷除数。除数は報道値からの逆算・近似）")
    N = data["^N225"]
    contrib = {}
    for i, d in enumerate(idays):
        if i == 0 or d < "2026-04-01" or d not in N:
            continue
        contrib[d] = (I[d]["c"] - I[idays[i - 1]]["c"]) * COEF_ADJ / lookup(DIVISOR, d)
    out["contribCheck"] = {}
    for d, rep in REPORTED_CONTRIB.items():
        out["contribCheck"][d] = (contrib.get(d), rep)
        print("   %s 推計 %+.2f円 / 報道 %+.2f円" % (d, contrib.get(d), rep))
    div = lookup(DIVISOR, AS_OF)
    pts1 = I[AS_OF]["c"] * 0.01 * COEF_ADJ / div
    weight = I[AS_OF]["c"] * COEF_ADJ / div / N[AS_OF]["c"]
    out["nikkei"] = dict(close=I[AS_OF]["c"], coefAdj=COEF_ADJ, divisor=div, ptsPer1pct=pts1, weight=weight, n225=N[AS_OF]["c"])
    print("10/2: 4062終値 %.0f円、係数 %.1f、除数 %.2f → 4062が1%%動くと日経平均は約%.1f円。構成比率（推計）%.2f%%（日経平均 %.0f円）" % (
        I[AS_OF]["c"], COEF_ADJ, div, pts1, 100 * weight, N[AS_OF]["c"]))
    for dd in ("2025-12-30", "2026-03-31", "2026-06-30", "2026-08-04"):
        w = close_on_or_before("4062.T", dd) * COEF_ADJ / lookup(DIVISOR, dd) / close_on_or_before("^N225", dd)
        out["nikkei"]["weight_" + dd] = w
        print("   %s時点の構成比率（推計）%.2f%%" % (dd, 100 * w))
    cd = [d for d in common if d in contrib and d >= "2026-04-02"]
    absc = [abs(contrib[d]) for d in cd]
    absN = [abs(N[d]["c"] - N[[x for x in N if x < d][-1]]["c"]) for d in cd]
    out["contribStats"] = dict(n=len(cd), meanAbsContrib=statistics.mean(absc), meanAbsN=statistics.mean(absN),
                               ratioOfMeans=sum(absc) / sum(absN))
    print("4/2〜10/2（%d日）：4062の寄与度の平均絶対値 %.0f円、日経平均の日次変化の平均絶対値 %.0f円（比 %.1f%%）" % (
        len(cd), statistics.mean(absc), statistics.mean(absN), 100 * sum(absc) / sum(absN)))
    top = sorted(cd, key=lambda d: -abs(contrib[d]))[:8]
    out["contribTop"] = {d: contrib[d] for d in sorted(top)}
    print("   寄与度の大きい日:", ", ".join("%s %+.0f円" % (d, contrib[d]) for d in sorted(top)))

    # ---- 3. 米国・欧州の前夜 -> 東京の4062
    print("\n== 3. 米国・欧州の前夜の騰落 -> 東京の4062（寄り付きギャップ・終値・寄り→引け）")
    out["overnight"] = {}

    def overnight_pairs(sym, wset, target="4062.T"):
        ur = R.get(sym, {})
        ud = sorted(ur)
        T = data[target]; td = list(T)
        tg = {d: T[d]["o"] / T[td[i - 1]]["c"] - 1 for i, d in enumerate(td) if i > 0}
        xs, gap, cc, oc, days = [], [], [], [], []
        for i, d in enumerate(td[1:], 1):
            if d not in wset:
                continue
            prev = [u for u in ud if u < d]
            if not prev or prev[-1] < td[i - 1]:
                continue
            xs.append(ur[prev[-1]]); gap.append(tg[d]); cc.append(R[target][d]); oc.append(T[d]["c"] / T[d]["o"] - 1)
            days.append((prev[-1], d))
        return xs, gap, cc, oc, days

    for win_lab, win in [("120日", common[-120:]), ("約1年", y1)]:
        wset = set(win)
        for us in OVERNIGHT:
            if us not in R:
                continue
            xs, gap, cc, oc, _ = overnight_pairs(us, wset)
            cg, ccc, coc = corr(xs, gap), corr(xs, cc), corr(xs, oc)
            bg, _ = ols_beta(gap, xs); bc, _ = ols_beta(cc, xs)
            out["overnight"]["%s %s" % (us, win_lab)] = dict(n=len(xs), corrGap=cg, corrClose=ccc, corrOpenToClose=coc,
                                                             betaGap=bg, betaClose=bc)
            print("%-5s %-7s n=%d 寄りギャップ相関 %.2f(β%.2f) 終値相関 %.2f(β%.2f) 寄り→引け相関 %+.2f" % (
                win_lab, us, len(xs), cg, bg, ccc, bc, coc))
    # 比較用：6857の前夜NVDA・SOX（同じ方法、アドバンテスト版の値と一致するはず）
    for us in ["NVDA", "^SOX"]:
        xs, gap, cc, oc, _ = overnight_pairs(us, set(common[-120:]), "6857.T")
        out["overnight"]["6857 vs %s 120日" % us] = dict(corrGap=corr(xs, gap), n=len(xs))
        print("  参考 6857 vs %s 120日 寄りギャップ相関 %.2f" % (us, corr(xs, gap)))
    # NVDAが±5%以上動いた夜の翌日（約1年）
    xs, gap, cc, oc, days = overnight_pairs("NVDA", set(y1))
    bigN = [(dd[0], x, dd[1], g, c) for x, g, c, dd in zip(xs, gap, cc, days) if abs(x) >= 0.05]
    out["bigNVDAnights"] = bigN
    up = [t for t in bigN if t[1] > 0]; dn = [t for t in bigN if t[1] < 0]
    print("NVDAが±5%%以上動いた夜（約1年）：上昇%d回→翌日4062の寄り平均 %s・終値平均 %s／下落%d回→寄り平均 %s・終値平均 %s" % (
        len(up), pct(statistics.mean(t[3] for t in up)) if up else "-", pct(statistics.mean(t[4] for t in up)) if up else "-",
        len(dn), pct(statistics.mean(t[3] for t in dn)) if dn else "-", pct(statistics.mean(t[4] for t in dn)) if dn else "-"))
    xs, gap, cc, oc, days = overnight_pairs("^SOX", set(y1))
    bigS = [(dd[0], x, dd[1], g, c) for x, g, c, dd in zip(xs, gap, cc, days) if abs(x) >= 0.04]
    up = [t for t in bigS if t[1] > 0]; dn = [t for t in bigS if t[1] < 0]
    out["bigSOXnights"] = dict(up=len(up), down=len(dn),
                               upGap=statistics.mean(t[3] for t in up) if up else None, upClose=statistics.mean(t[4] for t in up) if up else None,
                               dnGap=statistics.mean(t[3] for t in dn) if dn else None, dnClose=statistics.mean(t[4] for t in dn) if dn else None)
    print("SOXが±4%%以上動いた夜（約1年）：上昇%d回→寄り平均 %s・終値平均 %s／下落%d回→寄り平均 %s・終値平均 %s" % (
        len(up), pct(out["bigSOXnights"]["upGap"] or float("nan")), pct(out["bigSOXnights"]["upClose"] or float("nan")),
        len(dn), pct(out["bigSOXnights"]["dnGap"] or float("nan")), pct(out["bigSOXnights"]["dnClose"] or float("nan"))))

    # ---- 4. 台湾・韓国の同日
    print("\n== 4. 同じ時間帯の台湾・韓国株との同日相関（4062）。台湾の取引は日本時間10:00〜14:30")
    out["asia_sameday"] = {}
    for s in ASIA:
        if s not in R:
            continue
        for lab, ds0 in [("60日", common[-60:]), ("120日", common[-120:]), ("約1年", y1)]:
            ds = [d for d in ds0 if d in R[s]]
            r = corr([R["4062.T"][d] for d in ds], [R[s][d] for d in ds])
            b, _ = ols_beta([R["4062.T"][d] for d in ds], [R[s][d] for d in ds])
            out["asia_sameday"]["%s %s" % (s, lab)] = dict(corr=r, beta=b, n=len(ds))
        print("%-10s 60日 %.2f / 120日 %.2f / 約1年 %.2f（120日β %.2f）" % (
            s, out["asia_sameday"][s + " 60日"]["corr"], out["asia_sameday"][s + " 120日"]["corr"],
            out["asia_sameday"][s + " 約1年"]["corr"], out["asia_sameday"][s + " 120日"]["beta"]))
    # 台湾基板3社の等ウエート平均
    tw3 = ["3037.TW", "8046.TW", "3189.TW"]
    for lab, ds0 in [("60日", common[-60:]), ("120日", common[-120:]), ("約1年", y1)]:
        ds = [d for d in ds0 if all(d in R[s] for s in tw3)]
        avg = [statistics.mean(R[s][d] for s in tw3) for d in ds]
        out["asia_sameday"]["TW3 %s" % lab] = dict(corr=corr([R["4062.T"][d] for d in ds], avg), n=len(ds))
    print("台湾基板3社平均 60日 %.2f / 120日 %.2f / 約1年 %.2f" % tuple(out["asia_sameday"]["TW3 %s" % l]["corr"] for l in ["60日", "120日", "約1年"]))
    # 台湾基板の日足とイビデンの日足のローリング20日相関（Unimicron）
    ds = [d for d in common if d in R["3037.TW"]]
    roll = [(ds[i], corr([R["4062.T"][d] for d in ds[i - 19:i + 1]], [R["3037.TW"][d] for d in ds[i - 19:i + 1]]))
            for i in range(19, len(ds)) if ds[i] >= "2026-04-01"]
    out["rollUnimicron"] = dict(min=min(roll, key=lambda t: t[1]), max=max(roll, key=lambda t: t[1]), last=roll[-1],
                               neg=sum(1 for t in roll if t[1] < 0), n=len(roll))
    print("Unimicronとの20日ローリング相関（4月以降 %d窓）：最小 %s %.2f、最大 %s %.2f、直近 %.2f、負の窓 %d" % (
        len(roll), roll and out["rollUnimicron"]["min"][0], out["rollUnimicron"]["min"][1], out["rollUnimicron"]["max"][0],
        out["rollUnimicron"]["max"][1], out["rollUnimicron"]["last"][1], out["rollUnimicron"]["neg"]))
    ds = [d for d in common[-120:] if d in R.get("JPY=X", {})]
    out["usdjpy_corr120"] = corr([R["4062.T"][d] for d in ds], [R["JPY=X"][d] for d in ds])
    print("ドル円(同日付)相関(120日) %.2f n=%d（日付ずれあり、参考）" % (out["usdjpy_corr120"], len(ds)))

    # ---- 5. 決算反応
    print("\n== 5. 決算発表（引け後）の反応：発表日・翌営業日")
    out["earnings"] = {}
    for e in EARNINGS:
        if e not in I:
            continue
        i = idays.index(e)
        nx = idays[i + 1]
        nx2 = idays[i + 2] if i + 2 < len(idays) else nx
        ud = sorted(R["^SOX"])
        us_prev = [u for u in ud if e <= u < nx]
        sox = R["^SOX"][us_prev[-1]] if us_prev else float("nan")
        row = dict(day=R["4062.T"][e], nextDay=nx, gap=gaps[nx], close=R["4062.T"][nx], n225=R["^N225"][nx],
                   soxPrevNight=sox, twoDay=I[nx2]["c"] / I[e]["c"] - 1, volNext=I[nx]["v"])
        out["earnings"][e] = row
        print("%s 当日 %s → 翌%s 寄り %s 終値 %s（日経 %s、前夜SOX %s、発表日終値→翌々営業日終値 %s、出来高 %.1f百万株）" % (
            e, pct(row["day"]), nx, pct(row["gap"]), pct(row["close"]), pct(row["n225"]), pct(sox), pct(row["twoDay"]),
            row["volNext"] / 1e6))
    ab = [abs(v["close"]) for v in out["earnings"].values()]
    allabs = statistics.mean(abs(R["4062.T"][d]) for d in y1)
    ab_y1 = [abs(v["close"]) for k, v in out["earnings"].items() if v["nextDay"] >= ONE_YEAR_START]
    out["earningsStats"] = dict(meanAbsNextDay=statistics.mean(ab), meanAbsNextDay1y=statistics.mean(ab_y1),
                                n=len(ab), n1y=len(ab_y1), meanAbsAllDays1y=allabs,
                                up=sum(1 for v in out["earnings"].values() if v["close"] > 0))
    print("翌営業日の終値の平均絶対値 %.1f%%（%d回）、うち約1年 %.1f%%（%d回）、約1年の全営業日 %.1f%%。上昇 %d回" % (
        100 * statistics.mean(ab), len(ab), 100 * statistics.mean(ab_y1), len(ab_y1), 100 * allabs, out["earningsStats"]["up"]))

    # ---- 6. 株式分割の前後
    print("\n== 6. 株式分割（権利落ち日）の前後（調整後株価・調整後出来高。売買代金＝調整後終値×調整後出来高）")
    out["splits_effect"] = {}
    for ex in SPLIT_EX:
        i = idays.index(ex)
        pre = idays[i - 10:i]; post = idays[i:i + 10]
        r_ex = R["4062.T"][ex]
        cum_pre5 = I[idays[i - 1]]["c"] / I[idays[i - 6]]["c"] - 1
        post_n = min(5, len(idays) - 1 - i)
        cum_post = I[idays[i + post_n]]["c"] / I[idays[i - 1]]["c"] - 1 if post_n > 0 else float("nan")
        n_pre = I[idays[i - 1]]["c"] / I[idays[i - 6]]["c"] - 1
        n225_pre = close_on_or_before("^N225", idays[i - 1]) / close_on_or_before("^N225", idays[i - 6]) - 1
        n225_post = close_on_or_before("^N225", idays[i + post_n]) / close_on_or_before("^N225", idays[i - 1]) - 1 if post_n > 0 else float("nan")
        vpre = statistics.mean(I[d]["v"] for d in pre); vpost = statistics.mean(I[d]["v"] for d in post)
        tpre = statistics.mean(I[d]["v"] * I[d]["c"] for d in pre); tpost = statistics.mean(I[d]["v"] * I[d]["c"] for d in post)
        out["splits_effect"][ex] = dict(exDay=r_ex, exGap=gaps[ex], pre5=cum_pre5, n225pre5=n225_pre, postN=post_n,
                                        post=cum_post, n225post=n225_post, volPre10=vpre, volPost=vpost, nPost=len(post),
                                        turnoverPre10=tpre, turnoverPost=tpost, n225exDay=R["^N225"].get(ex))
        print("%s 権利落ち日 %s（寄り %s、日経 %s）。前5日 %s（日経 %s）、権利落ち前日→%d営業日後 %s（日経 %s）。平均出来高 前10日 %.1f→後%d日 %.1f百万株、売買代金 %.0f→%.0f億円" % (
            ex, pct(r_ex), pct(gaps[ex]), pct(R["^N225"].get(ex, float("nan"))), pct(cum_pre5), pct(n225_pre), post_n,
            pct(cum_post), pct(n225_post), vpre / 1e6, len(post), vpost / 1e6, tpre / 1e8, tpost / 1e8))
    # 9/29の権利落ち日：同日に分割したキオクシア・東京エレクトロン
    for s in ["285A.T", "8035.T", "6857.T", "^N225"]:
        print("   参考 9/29 %s %s、9/29〜10/2累計 %s" % (s, pct(R[s]["2026-09-29"]),
                                               pct(data[s]["2026-10-02"]["c"] / data[s]["2026-09-28"]["c"] - 1)))
        out["splits_effect"]["peer " + s] = dict(exDay=R[s]["2026-09-29"], cum=data[s]["2026-10-02"]["c"] / data[s]["2026-09-28"]["c"] - 1)

    # ---- 7. イベント日・テクニカル
    print("\n== 7. 個別イベント日の値動き（4062、日経平均、前夜SOX・NVDA・INTC、同日Unimicron）")
    out["events"] = {}
    for d, lab in EVENTS.items():
        if d not in R["4062.T"]:
            continue
        i = idays.index(d)

        def prev_us(sym):
            ud = sorted(R[sym])
            p = [u for u in ud if idays[i - 1] <= u < d]
            return R[sym][p[-1]] if p else float("nan")
        row = dict(label=lab, r=R["4062.T"][d], gap=gaps[d], close=I[d]["c"], high=I[d]["h"], low=I[d]["l"],
                   n225=R["^N225"][d], sox=prev_us("^SOX"), nvda=prev_us("NVDA"), intc=prev_us("INTC"),
                   umc=R["3037.TW"].get(d, float("nan")), r6857=R["6857.T"][d], vol=I[d]["v"],
                   contrib=contrib.get(d))
        out["events"][d] = row
        print("%s %-26s 4062 %s（寄り %s、終値 %.1f） 日経 %s 6857 %s 前夜SOX %s NVDA %s INTC %s Unimicron %s 出来高 %.1f百万株" % (
            d, lab, pct(row["r"]), pct(row["gap"]), row["close"], pct(row["n225"]), pct(row["r6857"]), pct(row["sox"]),
            pct(row["nvda"]), pct(row["intc"]), pct(row["umc"]), row["vol"] / 1e6))

    print("\n-- テクニカル")
    closes = [I[d]["c"] for d in idays]
    ma = {n: statistics.mean(closes[-n:]) for n in (5, 25, 75, 200)}
    y1days = [d for d in idays if d >= ONE_YEAR_START]
    hi_d = max(y1days, key=lambda d: I[d]["h"]); lo_d = min(y1days, key=lambda d: I[d]["l"])
    cl_hi_d = max(y1days, key=lambda d: I[d]["c"])
    out["technical"] = dict(close=closes[-1], ma=ma, high1y=(hi_d, I[hi_d]["h"]), low1y=(lo_d, I[lo_d]["l"]),
                            closeHigh1y=(cl_hi_d, I[cl_hi_d]["c"]), fromCloseHigh=closes[-1] / I[cl_hi_d]["c"] - 1,
                            fromHigh=closes[-1] / I[hi_d]["h"] - 1,
                            dev25=closes[-1] / ma[25] - 1, dev75=closes[-1] / ma[75] - 1, dev200=closes[-1] / ma[200] - 1,
                            up1yFromLow=closes[-1] / I[lo_d]["l"] - 1)
    t = out["technical"]
    print("終値 %.0f、移動平均 5日 %.0f / 25日 %.0f / 75日 %.0f / 200日 %.0f（乖離 25日 %s、75日 %s、200日 %s）" % (
        closes[-1], ma[5], ma[25], ma[75], ma[200], pct(t["dev25"]), pct(t["dev75"]), pct(t["dev200"])))
    print("約1年の高値 %.0f（%s、直近終値はその %s）、終値高値 %.0f（%s、%s）、安値 %.0f（%s）" % (
        I[hi_d]["h"], hi_d, pct(t["fromHigh"]), I[cl_hi_d]["c"], cl_hi_d, pct(t["fromCloseHigh"]), I[lo_d]["l"], lo_d))
    print("-- 月別の高値・安値・終値・平均出来高・売買代金（2026年、調整後）")
    out["monthly"] = {}
    for m in ["2025-10", "2025-11", "2025-12"] + ["2026-%02d" % k for k in range(1, 11)]:
        ds = [d for d in idays if d.startswith(m)]
        if not ds:
            continue
        hi = max(I[d]["h"] for d in ds); lo = min(I[d]["l"] for d in ds)
        out["monthly"][m] = dict(high=hi, low=lo, close=I[ds[-1]]["c"], avgVol=statistics.mean(I[d]["v"] for d in ds),
                                 avgTurnover=statistics.mean(I[d]["v"] * I[d]["c"] for d in ds))
        print("   %s 高値 %.0f 安値 %.0f 月末終値 %.0f 平均出来高 %.1f百万株 売買代金 %.0f億円" % (
            m, hi, lo, I[ds[-1]]["c"], out["monthly"][m]["avgVol"] / 1e6, out["monthly"][m]["avgTurnover"] / 1e8))
    seg = [d for d in idays if d >= "2026-07-01"]
    piv_h, piv_l = [], []
    for i in range(2, len(seg) - 2):
        d = seg[i]
        if I[d]["h"] == max(I[x]["h"] for x in seg[i - 2:i + 3]):
            piv_h.append((d, I[d]["h"]))
        if I[d]["l"] == min(I[x]["l"] for x in seg[i - 2:i + 3]):
            piv_l.append((d, I[d]["l"]))
    out["pivots"] = {"highs": piv_h, "lows": piv_l}
    print("スイング高値(前後2日, 7月以降):", ", ".join("%s %.0f" % t for t in piv_h))
    print("スイング安値(前後2日, 7月以降):", ", ".join("%s %.0f" % t for t in piv_l))
    vp = {}
    for lab, a0, a1 in [("7月", "2026-07-01", "2026-07-31"), ("8月", "2026-08-01", "2026-08-31"),
                        ("9/1-9/18", "2026-09-01", "2026-09-18"), ("9/24-10/2", "2026-09-24", "2026-10-02")]:
        xs = [I[d]["v"] for d in idays if a0 <= d <= a1]
        vp[lab] = (statistics.mean(xs), len(xs))
    out["volumeByPeriod"] = vp
    print("平均出来高:", ", ".join("%s %.1f百万株(%d日)" % (k, v[0] / 1e6, v[1]) for k, v in vp.items()))

    # ---- 8. キオクシア・アドバンテスト・TELとの連動
    print("\n== 8. キオクシア・アドバンテスト・TELとの連動（キオクシア版と同じ窓）")
    out["peers"] = {}
    for s in ["285A.T", "6857.T", "8035.T", "^N225"]:
        row = {lab: corr([R["4062.T"][d] for d in ds], [R[s][d] for d in ds]) for lab, ds in windows.items()}
        out["peers"][s] = row
        print("4062~%-7s" % s, "  ".join("%s %.2f" % (k, v) for k, v in row.items()))
    for p1, p2 in [("285A.T", "6857.T")]:
        print("確認 %s~%s 60日 %.2f" % (p1, p2, corr([R[p1][d] for d in common[-60:]], [R[p2][d] for d in common[-60:]])))
    # 20日ローリング（直近121窓）
    roll = []
    for i in range(len(common) - 121, len(common)):
        ds = common[i - 19:i + 1]
        roll.append((common[i], corr([R["4062.T"][d] for d in ds], [R["6857.T"][d] for d in ds]),
                     corr([R["4062.T"][d] for d in ds], [R["285A.T"][d] for d in ds])))
    out["roll20"] = dict(adv_min=min(roll, key=lambda t: t[1])[:2], adv_last=roll[-1][1], adv_neg=sum(1 for t in roll if t[1] < 0),
                         kx_min=(min(roll, key=lambda t: t[2])[0], min(roll, key=lambda t: t[2])[2]), kx_last=roll[-1][2])
    print("20日ローリング：対6857 最小 %s %.2f・直近 %.2f・負 %d窓／対285A 最小 %s %.2f・直近 %.2f" % (
        out["roll20"]["adv_min"][0], out["roll20"]["adv_min"][1], out["roll20"]["adv_last"], out["roll20"]["adv_neg"],
        out["roll20"]["kx_min"][0], out["roll20"]["kx_min"][1], out["roll20"]["kx_last"]))
    # 残差相関（TOPIX連動ETFで回帰、60日、4/2以降）
    ds = [d for d in common[-60:] if d >= "2026-04-02"]
    mk = [R["1306.T"][d] for d in ds]

    def resid(sym):
        y = [R[sym][d] for d in ds]
        b, c = ols_beta(y, mk)
        return [yy - (b * x + c) for yy, x in zip(y, mk)]
    out["residCorr60"] = {s: corr(resid("4062.T"), resid(s)) for s in ["285A.T", "6857.T", "8035.T", "3037.TW"] if all(d in R[s] for d in ds)}
    # 3037.TWは台湾の休日で欠ける日があるため個別に計算
    ds2 = [d for d in ds if d in R["3037.TW"]]
    mk2 = [R["1306.T"][d] for d in ds2]
    y1r = [R["4062.T"][d] for d in ds2]; y2r = [R["3037.TW"][d] for d in ds2]
    b1, c1 = ols_beta(y1r, mk2); b2, c2 = ols_beta(y2r, mk2)
    out["residCorr60"]["3037.TW"] = corr([a - (b1 * x + c1) for a, x in zip(y1r, mk2)], [a - (b2 * x + c2) for a, x in zip(y2r, mk2)])
    print("残差相関（1306で回帰、60日）:", ", ".join("%s %.2f" % kv for kv in out["residCorr60"].items()))
    # シーソー頻度（逆方向の日）と、6857が−2%以下の日の4062
    out["seesaw"] = {}
    for s in ["6857.T", "285A.T"]:
        for lab, ds in [("60日", common[-60:]), ("約1年", y1)]:
            pairs = [(R["4062.T"][d], R[s][d]) for d in ds if R["4062.T"][d] != 0 and R[s][d] != 0]
            opp = sum(1 for x, y in pairs if (x > 0) != (y > 0))
            n = len(pairs)
            # キオクシア版と同じ：独立なら期待される逆方向比率 p0 を各銘柄の上昇日比率から計算
            px_ = sum(1 for x, _ in pairs if x > 0) / n; py_ = sum(1 for _, y in pairs if y > 0) / n
            p0 = px_ * (1 - py_) + (1 - px_) * py_
            z = (opp / n - p0) / math.sqrt(p0 * (1 - p0) / n)
            out["seesaw"]["%s %s" % (s, lab)] = dict(opp=opp, n=n, share=opp / n, p0=p0, z=z)
            print("逆方向の日 4062~%s %s：%d/%d（%.0f%%、z %.1f）" % (s, lab, opp, n, 100 * opp / n, z))
    for lab, ds in [("60日", common[-60:]), ("約1年", y1)]:
        dd = [d for d in ds if R["6857.T"][d] <= -0.02]
        out["seesaw"]["adv_down %s" % lab] = dict(n=len(dd), up=sum(1 for d in dd if R["4062.T"][d] > 0),
                                                  mean=statistics.mean(R["4062.T"][d] for d in dd))
        print("6857が−2%%以下の日（%s %d日）：4062が上昇 %d日、平均 %s" % (lab, len(dd), out["seesaw"]["adv_down %s" % lab]["up"],
                                                             pct(out["seesaw"]["adv_down %s" % lab]["mean"])))
    # 1日ずれ（前日の6857・285A → 当日の4062）
    out["lag"] = {}
    for s in ["6857.T", "285A.T", "3037.TW"]:
        for lab, ds in [("60日", common[-60:]), ("120日", common[-120:]), ("約1年", y1)]:
            prs = []
            for d in ds:
                i = idays.index(d)
                pv = idays[i - 1]
                if pv in R[s]:
                    prs.append((R[s][pv], R["4062.T"][d]))
            out["lag"]["%s %s" % (s, lab)] = (corr([p[0] for p in prs], [p[1] for p in prs]), len(prs))
        print("前日の%s → 当日の4062：60日 %.2f、120日 %.2f、約1年 %.2f" % (
            s, out["lag"][s + " 60日"][0], out["lag"][s + " 120日"][0], out["lag"][s + " 約1年"][0]))
    # 5営業日（重ならない区間）の相関
    for s in ["6857.T", "285A.T"]:
        for lab, n in [("約6か月", 125), ("約1年", 240)]:
            # キオクシア版と同じ：末日から遡って重ならない5営業日区間
            cd = common[-n:]
            ends = list(range(len(cd) - 1, 4, -5))
            blocks = ends
            xs = [I[cd[e]]["c"] / I[cd[e - 5]]["c"] - 1 for e in ends]
            ys = [data[s][cd[e]]["c"] / data[s][cd[e - 5]]["c"] - 1 for e in ends]
            out.setdefault("weekly", {})["%s %s" % (s, lab)] = dict(corr=corr(xs, ys), n=len(blocks),
                                                                     opp=sum(1 for x, y in zip(xs, ys) if (x > 0) != (y > 0)))
            print("5営業日 4062~%s %s：相関 %.2f（%d区間中、逆方向 %d）" % (s, lab, out["weekly"]["%s %s" % (s, lab)]["corr"],
                                                                len(blocks), out["weekly"]["%s %s" % (s, lab)]["opp"]))
    # 決算日の連動：6857・285A・8035の決算翌日の4062と、4062決算翌日の他社
    peer_e = {"6857.T": ["2025-10-28", "2026-01-28", "2026-04-27", "2026-07-29"]}
    out["peerEarnings"] = {}
    for s, es in peer_e.items():
        for e in es:
            if e not in I:
                continue
            nx = idays[idays.index(e) + 1]
            out["peerEarnings"]["%s %s" % (s, e)] = dict(next=nx, r4062=R["4062.T"][nx], rpeer=R[s][nx])
            print("%s決算 %s の翌営業日 %s：%s %s、4062 %s" % (s, e, nx, s, pct(R[s][nx]), pct(R["4062.T"][nx])))
    for e in EARNINGS:
        if e not in I or e < "2025-10-01":
            continue
        nx = idays[idays.index(e) + 1]
        row = {s: R[s].get(nx) for s in ["6857.T", "285A.T", "8035.T"]}
        um = [d for d in sorted(R["3037.TW"]) if d >= nx]
        row["3037.TW"] = R["3037.TW"].get(um[0]) if um else None
        out["peerEarnings"]["4062 %s" % e] = dict(next=nx, r4062=R["4062.T"][nx], **{k: v for k, v in row.items()})
        print("4062決算 %s の翌営業日 %s：4062 %s、6857 %s、285A %s、8035 %s、Unimicron(同日以降最初) %s" % (
            e, nx, pct(R["4062.T"][nx]), pct(row["6857.T"] if row["6857.T"] is not None else float("nan")),
            pct(row["285A.T"] if row["285A.T"] is not None else float("nan")), pct(row["8035.T"]),
            pct(row["3037.TW"] if row["3037.TW"] is not None else float("nan"))))

    # ---- 9. 会社予想ベースの簡単な計算
    print("\n== 9. 会社予想ベースの簡単な計算（独自計算）")
    px = I[AS_OF]["c"]
    eps_fy26 = 149.68   # 会社予想（2026-08-04）。2026-10-01の分割後基準
    eps_fy25 = 228.16 / 2  # 2026年3月期実績（2026-01分割後基準228.16円）を10月分割後基準へ
    eps_fy25_ex = (63713 - (49144 - 15804) * (1 - 0.3062)) / 63713 * eps_fy25  # 特別損益を除いた参考値（実効税率30.62%と仮定）
    cb_book = 64248 - 7300  # 6/30の転換社債残高（百万円、帳簿価額）−7月の転換額面
    cb_px = 2243.1
    shares_out = 563888038
    pot = cb_book * 1e6 / cb_px
    out["valuation"] = dict(price=px, perFY26=px / eps_fy26, epsFY25=eps_fy25, perFY25=px / eps_fy25,
                            epsFY25exSpecial=eps_fy25_ex, perFY25exSpecial=px / eps_fy25_ex,
                            cbRemainingApprox=cb_book, cbConvPrice=cb_px, cbPotentialShares=pot,
                            cbDilution=pot / shares_out, cbMoneyness=px / cb_px,
                            offerPriceAdj=7632 / 2, fromOfferPrice=px / (7632 / 2) - 1,
                            mcapOku=px * shares_out / 1e8)
    v = out["valuation"]
    print("株価 %.0f円：会社予想EPS 149.68円でPER %.1f倍、FY25実績EPS %.2f円で %.1f倍（特別損益を除く参考EPS %.1f円で %.1f倍）" % (
        px, v["perFY26"], eps_fy25, v["perFY25"], eps_fy25_ex, v["perFY25exSpecial"]))
    print("時価総額（分割後発行済563,888,038株×終値、自己株含む）約%.0f億円" % v["mcapOku"])
    print("CB：6/30残高64,248百万円−7月転換7,300百万円＝約%.0f百万円（概算）÷転換価額2,243.1円＝約%.1f百万株（発行済の%.1f%%）。株価は転換価額の%.1f倍" % (
        cb_book, pot / 1e6, 100 * v["cbDilution"], v["cbMoneyness"]))
    print("2026年3月の売出価格7,632円（分割調整後3,816円）からの上昇率 %s" % pct(v["fromOfferPrice"]))
    # 会社予想の分解（百万円。2026-08-04の会社予想と1Q実績の差し引き）
    q1 = dict(sales=123219, op=26880, e_sales=77522, e_op=21375)
    h1 = dict(sales=253500, op=54500)
    fy = dict(sales=550000, op=127000, e_sales=375000, e_op=110000)
    q2_op = h1["op"] - q1["op"]; h2_op = fy["op"] - h1["op"]
    out["guidanceSplit"] = dict(q2Sales=h1["sales"] - q1["sales"], q2Op=q2_op, q2OpQoQ=q2_op / q1["op"] - 1,
                                h2Sales=fy["sales"] - h1["sales"], h2Op=h2_op, h2OpPerQ=h2_op / 2,
                                h2PerQvsQ1=h2_op / 2 / q1["op"] - 1,
                                eRest3QSales=(fy["e_sales"] - q1["e_sales"]) / 3, eRest3QOp=(fy["e_op"] - q1["e_op"]) / 3)
    g = out["guidanceSplit"]
    print("会社予想の分解：2Q 売上 %.0f億円・営業利益 %.0f億円（1Q比 %s）、下期 売上 %.0f億円・営業利益 %.0f億円（四半期平均 %.0f億円、1Q比 %s）" % (
        g["q2Sales"] / 100, g["q2Op"] / 100, pct(g["q2OpQoQ"]), g["h2Sales"] / 100, g["h2Op"] / 100, g["h2OpPerQ"] / 100, pct(g["h2PerQvsQ1"])))
    print("電子：2〜4Qの四半期平均 売上 %.0f億円・営業利益 %.0f億円（1Qは775億円・214億円）" % (g["eRest3QSales"] / 100, g["eRest3QOp"] / 100))
    # 7/1の高値から7/29の安値までの下落、6/22の終値高値から7/29の終値
    hi = I["2026-07-01"]["h"]; lo = I["2026-07-29"]["l"]
    out["drawdownJul"] = dict(high=hi, low=lo, dd=lo / hi - 1, closeHigh=I["2026-06-22"]["c"], closeLow=I["2026-07-29"]["c"],
                              ddClose=I["2026-07-29"]["c"] / I["2026-06-22"]["c"] - 1, rebound=I[AS_OF]["c"] / lo - 1)
    print("7/1の日中高値 %.0f→7/29の日中安値 %.0f：%s（終値ベース 6/22 %.0f→7/29 %.0f：%s）。7/29安値から10/2終値まで %s" % (
        hi, lo, pct(lo / hi - 1), I["2026-06-22"]["c"], I["2026-07-29"]["c"], pct(out["drawdownJul"]["ddClose"]), pct(out["drawdownJul"]["rebound"])))

    print("\n-- キオクシア版との整合確認：4062~285A 60日 %.2f／約1年 %.2f、4062~6857 60日 %.2f／約1年 %.2f、4062 1年ボラ %.0f%%" % (
        out["peers"]["285A.T"]["60日"], out["peers"]["285A.T"]["約1年"], out["peers"]["6857.T"]["60日"],
        out["peers"]["6857.T"]["約1年"], 100 * out["vol"]["4062.T 1年"]["annVol"]))

    with open(os.path.join(WORK, "stock-drivers-results.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=str)


if __name__ == "__main__":
    main()
