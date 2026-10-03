#!/usr/bin/env python3
"""キオクシア（285A）株価変動要因レポート（2026-10-03）の再現用計算。

標準ライブラリのみ。Yahoo Finance公開チャートAPI（キー不要、分割調整済み日足）から
日足OHLCVを取得して working/yahoo-chart-<symbol>-1y.json に保存し、次を計算する。

  1. 相対パフォーマンス（期間別騰落率）
  2. 日次リターンの相関（期間別・20日ローリング）、日経平均を除いた残差の相関
  3. 「シーソー」検定：逆方向の日の比率、片方が大きく下げた日のもう片方の動き、1日ずれの相関
  4. 米国（MU・SNDK・SOX）の前夜の値動きと翌営業日の東京（285A）の関係
  5. キオクシアの値動きの特徴（ボラティリティ、ギャップ、出来高）
  6. 三角持ち合い判定用の高値・安値の推移、レンジ幅・出来高の推移、トレンドライン水準

使い方:
  python3 stock_drivers.py            # 取得して計算（取得データは working/ に保存）
  python3 stock_drivers.py --offline  # working/ の保存データだけで再計算

株価はすべて分割調整後（285Aは2026-10-01効力の1対3分割後の円）。出来高も分割調整後（分割前の日は×3）。
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

SYMBOLS = {
    "285A.T": "キオクシア", "6857.T": "アドバンテスト", "4062.T": "イビデン",
    "8035.T": "東京エレクトロン", "6146.T": "ディスコ", "6920.T": "レーザーテック",
    "3436.T": "SUMCO", "^N225": "日経平均", "1306.T": "TOPIX連動ETF",
    "JPY=X": "ドル円", "MU": "Micron", "SNDK": "Sandisk", "^SOX": "SOX指数",
    "000660.KS": "SK hynix", "005930.KS": "Samsung電子",
}
TOKYO = ["285A.T", "6857.T", "4062.T", "8035.T", "6146.T", "6920.T", "3436.T", "^N225", "1306.T"]
US = ["MU", "SNDK", "^SOX"]


def fname(sym):
    return os.path.join(WORK, "yahoo-chart-%s-1y.json" % sym.replace("^", "_").replace("=", "_"))


def fetch(sym):
    url = ("https://query1.finance.yahoo.com/v8/finance/chart/%s?range=1y&interval=1d&events=div%%2Csplits"
           % urllib.parse.quote(sym))
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    data["_retrieved"] = dt.datetime.now(dt.timezone.utc).isoformat()
    data["_url"] = url
    with open(fname(sym), "w") as f:
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
    data = {s: load(s) for s in SYMBOLS if os.path.exists(fname(s))}
    R = {s: rets(v) for s, v in data.items()}
    out = {}

    # ---- 1. 相対パフォーマンス
    k = data["285A.T"]
    kdays = list(k)
    def close_on_or_before(sym, day):
        ds = [d for d in data[sym] if d <= day]
        return data[sym][ds[-1]]["c"]
    anchors = {"2026-04-01": "4/1", "2026-06-22": "6/22(285A上場来高値)", "2026-06-30": "6/30",
               "2026-07-29": "7/29(285A安値)", "2026-09-04": "9/4(前回調査)",
               "2026-09-11": "9/11(急落前)", "2026-09-17": "9/17", "2026-09-26": "9/26"}
    perf = {}
    for s in ["285A.T", "6857.T", "4062.T", "8035.T", "6146.T", "6920.T", "3436.T", "^N225", "1306.T",
              "MU", "SNDK", "^SOX", "000660.KS", "005930.KS"]:
        if s not in data:
            continue
        last = close_on_or_before(s, AS_OF if s not in US else "2026-10-02")
        perf[s] = {lab: last / close_on_or_before(s, d) - 1 for d, lab in anchors.items()}
        perf[s]["last"] = last
    out["performance"] = perf
    print("== 1. 騰落率（各日の終値→直近終値。米国は10/2米国終値、Yahoo分割調整済み）")
    print("%-10s" % "", "  ".join("%14s" % l for l in anchors.values()), "     last")
    for s, p in perf.items():
        print("%-10s" % s, "  ".join("%14s" % pct(p[l]) for l in anchors.values()), "%10.2f" % p["last"])

    # ---- 2. 相関
    pairs = [("285A.T", "6857.T"), ("285A.T", "4062.T"), ("285A.T", "8035.T"), ("6857.T", "4062.T"),
             ("6857.T", "8035.T"), ("285A.T", "^N225"), ("6857.T", "^N225"), ("285A.T", "6146.T"),
             ("285A.T", "6920.T"), ("285A.T", "3436.T")]
    common = [d for d in kdays[1:] if all(d in R[s] for s in TOKYO if s in R)]
    windows = {"20日": 20, "60日": 60, "120日": 120, "全期間(約1年)": len(common)}
    out["corr"] = {}
    print("\n== 2. 日次リターン相関（東京同日、直近N営業日、末日%s）" % common[-1])
    for x, y in pairs:
        row = {}
        for lab, n in windows.items():
            ds = common[-n:]
            r = corr([R[x][d] for d in ds], [R[y][d] for d in ds])
            row[lab] = (r, len(ds), corr_ci(r, len(ds)))
        out["corr"]["%s~%s" % (x, y)] = {k2: v[0] for k2, v in row.items()}
        print("%-16s" % ("%s~%s" % (x, y)),
              "  ".join("%s %.2f[%.2f,%.2f]n=%d" % (lab, v[0], v[2][0], v[2][1], v[1]) for lab, v in row.items()))

    # 20日ローリング（直近120日）
    print("\n-- 20日ローリング相関（直近120営業日の範囲）")
    out["rolling"] = {}
    for x, y in [("285A.T", "6857.T"), ("285A.T", "4062.T"), ("6857.T", "4062.T")]:
        vals = []
        for i in range(len(common) - 120, len(common) + 1):
            ds = common[i - 20:i]
            vals.append((ds[-1], corr([R[x][d] for d in ds], [R[y][d] for d in ds])))
        mn = min(vals, key=lambda t: t[1]); mx = max(vals, key=lambda t: t[1])
        neg = sum(1 for _, v in vals if v < 0)
        out["rolling"]["%s~%s" % (x, y)] = {"min": mn, "max": mx, "last": vals[-1], "negWindows": neg, "n": len(vals)}
        print("%-16s 最小 %.2f(%s) 最大 %.2f(%s) 直近 %.2f 負の窓 %d/%d" % (
            "%s~%s" % (x, y), mn[1], mn[0], mx[1], mx[0], vals[-1][1], neg, len(vals)))
        # monthly snapshots
        snaps = [v for v in vals if v[0][8:10] >= "25" or v is vals[-1]]
        last_by_month = {}
        for d, v in vals:
            last_by_month[d[:7]] = (d, v)
        print("   月末時点:", ", ".join("%s %.2f" % (d, v) for d, v in last_by_month.values()))

    # 日経平均を除いた残差相関（共通の相場要因を除いても逆相関になるか）
    print("\n-- 日経平均（市場要因）を回帰で除いた残差の相関")
    out["residual"] = {}
    for mk, n_lab, n in [("^N225", "60日", 60), ("^N225", "120日", 120), ("^N225", "全期間", len(common)),
                         ("1306.T", "TOPIX 60日", 60), ("1306.T", "TOPIX 120日", 120)]:
        ds = common[-n:]
        m = [R[mk][d] for d in ds]
        res = {}
        for s in ["285A.T", "6857.T", "4062.T", "8035.T"]:
            y = [R[s][d] for d in ds]
            b, c0 = ols_beta(y, m)
            res[s] = [yy - (c0 + b * mm) for yy, mm in zip(y, m)]
            out["residual"].setdefault("beta_" + s, {})[n_lab] = b
        rr = {p: corr(res[p.split("~")[0]], res[p.split("~")[1]]) for p in
              ["285A.T~6857.T", "285A.T~4062.T", "6857.T~4062.T", "285A.T~8035.T", "6857.T~8035.T"]}
        out["residual"][n_lab] = rr
        print(n_lab, "β(対%s):" % mk, ", ".join("%s %.2f" % (s, out["residual"]["beta_" + s][n_lab])
                                         for s in ["285A.T", "6857.T", "4062.T", "8035.T"]))
        print("   残差相関:", ", ".join("%s %.2f" % (p, v) for p, v in rr.items()))

    # ---- 3. シーソー検定
    print("\n== 3. シーソー（逆方向）検定")
    out["seesaw"] = {}
    for x, y in [("285A.T", "6857.T"), ("285A.T", "4062.T")]:
        for lab, n in [("60日", 60), ("120日", 120), ("全期間", len(common))]:
            ds = [d for d in common[-n:] if R[x][d] != 0 and R[y][d] != 0]
            opp = sum(1 for d in ds if (R[x][d] > 0) != (R[y][d] > 0))
            px = sum(1 for d in ds if R[x][d] > 0) / len(ds)
            py = sum(1 for d in ds if R[y][d] > 0) / len(ds)
            p0 = px * (1 - py) + (1 - px) * py  # 独立なら期待される逆方向比率
            z = (opp / len(ds) - p0) / math.sqrt(p0 * (1 - p0) / len(ds))
            # yが-2%以下の日のxの動き
            dn = [d for d in common[-n:] if R[y][d] <= -0.02]
            xup = sum(1 for d in dn if R[x][d] > 0)
            mean_x = statistics.mean(R[x][d] for d in dn) if dn else float("nan")
            # 1日ずれ：yの当日 -> xの翌日
            cd = common[-n:]
            lag = corr([R[y][cd[i - 1]] for i in range(1, len(cd))], [R[x][cd[i]] for i in range(1, len(cd))])
            lag2 = corr([R[x][cd[i - 1]] for i in range(1, len(cd))], [R[y][cd[i]] for i in range(1, len(cd))])
            # 相対強弱の反転（スプレッドの自己相関）
            sp = [R[x][d] - R[y][d] for d in cd]
            ac = corr(sp[:-1], sp[1:])
            key = "%s~%s %s" % (x, y, lab)
            out["seesaw"][key] = dict(n=len(ds), oppositeShare=opp / len(ds), expectedIfIndependent=p0, z=z,
                                      yDown2pctDays=len(dn), xUpOnThoseDays=xup, xMeanOnThoseDays=mean_x,
                                      lag_y_to_next_x=lag, lag_x_to_next_y=lag2, spreadAutocorr=ac)
            print("%s: 逆方向 %d/%d=%.0f%%（独立なら%.0f%%、z=%.2f）。%sが-2%%以下の%d日のうち%sが上昇%d日、平均%s。"
                  "1日ずれ相関 %s→翌%s %.2f / %s→翌%s %.2f。スプレッド自己相関 %.2f" % (
                      key, opp, len(ds), 100 * opp / len(ds), 100 * p0, z, y, len(dn), x, xup, pct(mean_x),
                      y, x, lag, x, y, lag2, ac))

    # 週次（重ならない5営業日リターン）の相関：数日〜数週間のローテーションの確認
    print("-- 5営業日リターン（重ならない区間、末日から遡る）の相関")
    out["weekly"] = {}
    for x, y in [("285A.T", "6857.T"), ("285A.T", "4062.T")]:
        for lab, n in [("約6か月", 125), ("約1年", 240)]:
            cd = common[-n:]
            ends = list(range(len(cd) - 1, 4, -5))
            def wr(sym):
                return [data[sym][cd[e]]["c"] / data[sym][cd[e - 5]]["c"] - 1 for e in ends]
            wx, wy = wr(x), wr(y)
            r = corr(wx, wy)
            opp = sum(1 for a2, b2 in zip(wx, wy) if (a2 > 0) != (b2 > 0))
            out["weekly"]["%s~%s %s" % (x, y, lab)] = dict(n=len(ends), corr=r, opposite=opp)
            print("%s~%s %s: 週数 %d 相関 %.2f 逆方向の週 %d" % (x, y, lab, len(ends), r, opp))

    # 9月中旬以降の日次（表用）
    print("\n-- 9/1以降の日次リターン（東京）")
    out["daily"] = {}
    for d in [d for d in common if d >= "2026-09-01"]:
        out["daily"][d] = {s: R[s][d] for s in ["285A.T", "6857.T", "4062.T", "8035.T", "^N225"]}
        print(d, "  ".join("%s %s" % (s, pct(R[s][d])) for s in ["285A.T", "6857.T", "4062.T", "8035.T", "^N225"]))

    # ---- 4. 米国前夜 -> 東京
    print("\n== 4. 米国前夜の騰落 -> 東京の285A（寄り付きギャップ・終値）")
    out["us_overnight"] = {}
    for us in US:
        ur = R.get(us, {})
        ud = sorted(ur)
        xs, gap, cc = [], [], []
        for i, d in enumerate(kdays[1:], 1):
            if d not in common[-120:]:
                continue
            prev = [u for u in ud if u < d]
            if not prev or prev[-1] < kdays[i - 1]:
                continue  # 前営業日以降に米国の取引がない
            xs.append(ur[prev[-1]])
            gap.append(k[d]["o"] / k[kdays[i - 1]]["c"] - 1)
            cc.append(R["285A.T"][d])
        cg, ccc = corr(xs, gap), corr(xs, cc)
        bg, _ = ols_beta(gap, xs)
        bc, _ = ols_beta(cc, xs)
        same = sum(1 for a2, b2 in zip(xs, cc) if (a2 > 0) == (b2 > 0)) / len(xs)
        out["us_overnight"][us] = dict(n=len(xs), corrGap=cg, corrClose=ccc, betaGap=bg, betaClose=bc, sameSign=same)
        print("%-6s n=%d 寄りギャップ相関 %.2f(β%.2f) 終値相関 %.2f(β%.2f) 同方向 %.0f%%" % (
            us, len(xs), cg, bg, ccc, bc, 100 * same))
    # 同じ東京日のSK hynix（同時間帯）
    for s in ["000660.KS", "005930.KS"]:
        ds = [d for d in common[-120:] if d in R.get(s, {})]
        print("%s 同日相関(120日) %.2f n=%d" % (s, corr([R["285A.T"][d] for d in ds], [R[s][d] for d in ds]), len(ds)))
        out.setdefault("korea_sameday", {})[s] = corr([R["285A.T"][d] for d in ds], [R[s][d] for d in ds])
    # ドル円
    ds = [d for d in common[-120:] if d in R.get("JPY=X", {})]
    out["usdjpy_corr120"] = corr([R["285A.T"][d] for d in ds], [R["JPY=X"][d] for d in ds])
    print("ドル円(同日付)相関(120日) %.2f n=%d（ドル円は日付ずれあり、参考）" % (out["usdjpy_corr120"], len(ds)))

    # ---- 5. 値動きの特徴
    print("\n== 5. 値動きの特徴（直近1年／直近60日）")
    out["vol"] = {}
    for s in ["285A.T", "6857.T", "4062.T", "8035.T", "^N225", "MU", "SNDK"]:
        rs = list(R[s].values())
        for lab, n in [("60日", 60), ("1年", len(rs))]:
            x = rs[-n:]
            v = statistics.pstdev(x) * math.sqrt(250)
            big = sum(1 for t in x if abs(t) >= 0.05)
            out["vol"]["%s %s" % (s, lab)] = dict(annVol=v, meanAbs=statistics.mean(abs(t) for t in x), days5=big, n=len(x))
        print("%-8s 年率ボラ 60日 %.0f%% / 1年 %.0f%%、平均絶対日次 60日 %.2f%%、|日次|≥5%%の日 60日 %d / 1年 %d" % (
            s, 100 * out["vol"][s + " 60日"]["annVol"], 100 * out["vol"][s + " 1年"]["annVol"],
            100 * out["vol"][s + " 60日"]["meanAbs"], out["vol"][s + " 60日"]["days5"], out["vol"][s + " 1年"]["days5"]))
    gaps = [(d, k[d]["o"] / k[kdays[i - 1]]["c"] - 1) for i, d in enumerate(kdays) if i > 0]
    g60 = gaps[-60:]
    out["gaps60"] = dict(ge3=sum(1 for _, g in g60 if abs(g) >= 0.03), meanAbs=statistics.mean(abs(g) for _, g in g60))
    print("285A 寄り付きギャップ（直近60日）: |gap|≥3%% %d日、平均絶対 %.2f%%" % (out["gaps60"]["ge3"], 100 * out["gaps60"]["meanAbs"]))
    big_days = sorted([(d, R["285A.T"][d]) for d in kdays[-80:] if d in R["285A.T"]], key=lambda t: -abs(t[1]))[:12]
    out["bigDays"] = big_days
    print("285A 直近80日の大きな日次:", ", ".join("%s %s" % (d, pct(v)) for d, v in sorted(big_days)))

    # ---- 6. 三角持ち合い
    print("\n== 6. 285A 直近の高値・安値（分割後の円）")
    seg = [d for d in kdays if d >= "2026-07-20"]
    piv_h, piv_l = [], []
    for i in range(2, len(seg) - 2):
        d = seg[i]
        if k[d]["h"] == max(k[x]["h"] for x in seg[i - 2:i + 3]):
            piv_h.append((d, k[d]["h"]))
        if k[d]["l"] == min(k[x]["l"] for x in seg[i - 2:i + 3]):
            piv_l.append((d, k[d]["l"]))
    out["pivots"] = {"highs": piv_h, "lows": piv_l}
    print("スイング高値(前後2日):", ", ".join("%s %.0f" % t for t in piv_h))
    print("スイング安値(前後2日):", ", ".join("%s %.0f" % t for t in piv_l))
    # 5営業日ごとのレンジと出来高
    print("-- 5営業日ブロック（高値・安値・幅・平均出来高、出来高は分割調整後の株数）")
    blocks = []
    tail = kdays[-40:]
    for i in range(0, 40, 5):
        b = tail[i:i + 5]
        hi = max(k[d]["h"] for d in b); lo = min(k[d]["l"] for d in b)
        vol = statistics.mean(k[d]["v"] for d in b)
        blocks.append(dict(start=b[0], end=b[-1], high=hi, low=lo, widthPct=hi / lo - 1, avgVol=vol))
        print("%s〜%s 高値 %.0f 安値 %.0f 幅 %.1f%% 平均出来高 %.1f百万株" % (b[0], b[-1], hi, lo, 100 * (hi / lo - 1), vol / 1e6))
    out["blocks"] = blocks
    # 出来高の推移
    for lab, rng in [("7月", "2026-07"), ("8月", "2026-08"), ("9月1-18日", "2026-09-0|2026-09-1"), ]:
        pass
    def avgv(a0, a1):
        xs = [k[d]["v"] for d in kdays if a0 <= d <= a1]
        return statistics.mean(xs), len(xs)
    vp = {"7/1-7/31": avgv("2026-07-01", "2026-07-31"), "8/1-8/31": avgv("2026-08-01", "2026-08-31"),
          "9/1-9/18": avgv("2026-09-01", "2026-09-18"), "9/24-10/2": avgv("2026-09-24", "2026-10-02")}
    out["volumeByPeriod"] = vp
    print("平均出来高:", ", ".join("%s %.1f百万株(%d日)" % (kk, v[0] / 1e6, v[1]) for kk, v in vp.items()))
    # トレンドライン：9/8高値と9/24高値を結ぶ線、9/14安値と9/29安値を結ぶ線を10/5〜10/9へ延長
    idx = {d: i for i, d in enumerate(kdays)}
    def line(d1, v1, d2, v2):
        s = (v2 - v1) / (idx[d2] - idx[d1])
        return s, lambda steps_after_last: v2 + s * (idx[kdays[-1]] - idx[d2] + steps_after_last)
    print("[A] 短期の線（9月の高値・安値どうし）")
    hs, hl = line("2026-09-08", k["2026-09-08"]["h"], "2026-09-24", k["2026-09-24"]["h"])
    ls, ll = line("2026-09-14", k["2026-09-14"]["l"], "2026-09-29", k["2026-09-29"]["l"])
    print("   10/1上値線 %.0f（10/1終値 %.0f）" % (hl(-1), k["2026-10-01"]["c"]))
    proj = {n: (hl(n), ll(n)) for n in range(0, 6)}
    out["trendlines"] = dict(highSlopePerDay=hs, lowSlopePerDay=ls, proj=proj)
    print("上値線(9/8高値→9/24高値) 傾き %.0f円/日、下値線(9/14安値→9/29安値) 傾き %.0f円/日" % (hs, ls))
    for n, (u, l2) in proj.items():
        print("  直近から%d営業日後: 上値線 %.0f / 下値線 %.0f / 幅 %.1f%%" % (n, u, l2, 100 * (u / l2 - 1)))
    apex = None
    for n in range(0, 200):
        if hl(n) <= ll(n):
            apex = n; break
    out["trendlines"]["apexDaysAfterLast"] = apex
    print("  2線の交点: 直近から約%s営業日後" % apex)
    print("  10/2: 高値 %.0f 安値 %.0f 終値 %.0f" % (k[AS_OF]["h"], k[AS_OF]["l"], k[AS_OF]["c"]))
    print("[B] 8月以降の大きな三角形（8/18高値→9/8高値、8/31安値→9/29安値）")
    hs2, hl2 = line("2026-08-18", k["2026-08-18"]["h"], "2026-09-08", k["2026-09-08"]["h"])
    ls2, ll2 = line("2026-08-31", k["2026-08-31"]["l"], "2026-09-29", k["2026-09-29"]["l"])
    proj2 = {n: (hl2(n), ll2(n)) for n in range(0, 11)}
    apex2 = next((n for n in range(0, 400) if hl2(n) <= ll2(n)), None)
    out["trendlinesB"] = dict(highSlopePerDay=hs2, lowSlopePerDay=ls2, proj=proj2, apexDaysAfterLast=apex2)
    print("   上値線 傾き %.0f円/日、下値線 傾き %.0f円/日、交点 直近から約%s営業日後" % (hs2, ls2, apex2))
    for n in (0, 1, 5, 10, 20):
        print("   直近から%d営業日後: 上値線 %.0f / 下値線 %.0f / 幅 %.1f%%" % (n, hl2(n), ll2(n), 100 * (hl2(n) / ll2(n) - 1)))
    ratio = {d: k[d]["c"] / data["6857.T"][d]["c"] for d in ("2026-06-30", "2026-07-29", "2026-09-04", "2026-09-17", "2026-10-02")}
    out["ratio285A_6857"] = ratio
    print("285A/6857 株価比:", ", ".join("%s %.3f" % kv for kv in ratio.items()))
    hi9 = max(k[d]["h"] for d in kdays if d >= "2026-09-01")
    lo9 = min(k[d]["l"] for d in kdays if d >= "2026-09-01")
    out["sepRange"] = (hi9, lo9)
    print("  9/1以降 高値 %.0f 安値 %.0f" % (hi9, lo9))
    # 6857 も同様に
    a6 = data["6857.T"]
    ad = list(a6)
    seg6 = [d for d in ad if d >= "2026-08-15"]
    print("-- 6857 9月以降 高値 %.0f(%s) 安値 %.0f(%s) 終値 %.0f" % (
        max(a6[d]["h"] for d in seg6 if d >= "2026-09-01"),
        max((d for d in seg6 if d >= "2026-09-01"), key=lambda d: a6[d]["h"]),
        min(a6[d]["l"] for d in seg6 if d >= "2026-09-01"),
        min((d for d in seg6 if d >= "2026-09-01"), key=lambda d: a6[d]["l"]), a6[AS_OF]["c"]))
    hi6_all = max(ad, key=lambda d: a6[d]["h"])
    print("   6857 1年高値 %.0f(%s)" % (a6[hi6_all]["h"], hi6_all))

    with open(os.path.join(WORK, "stock-drivers-results.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=str)


if __name__ == "__main__":
    main()
