#!/usr/bin/env python3
"""光半導体・光インターコネクト関連株チャートの取得・生成スクリプト（標準ライブラリのみ）。

使い方（リポジトリのルートで実行）:
    python3 research/themes/photonics/2026-10-03/build_chart.py            # 取得して生成
    python3 research/themes/photonics/2026-10-03/build_chart.py --offline  # working/ の保存済みJSONから再生成

- 価格: Yahoo Finance 公開チャートAPI (query1.finance.yahoo.com/v8/finance/chart)、キー不要。
- 系列: 各市場の現地通貨・配当調整後終値 (adjclose)。株式分割はYahoo側で遡及調整済み。
- 指数: 2026年最初の取引日 = 100。日次を5取引日ごとに間引き、最終取引日を必ず含める。
- 表示枠（HTMLヘッダ・スタイル・iframeラッパー）は前回版 ../2026-09-05/index.html を流用する。
出力: chart-source.html, index.html, prices-summary.csv（同フォルダ）, working/raw/*.json（Git対象外）
"""
import csv
import datetime as dt
import html
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREV_INDEX = HERE.parent / "2026-09-05" / "index.html"
RAW_DIR = HERE / "working" / "raw"
START = dt.date(2026, 1, 1)
END_EXCLUSIVE = dt.date(2026, 10, 3)  # 2026-10-02（金）の終値までを対象
PREV_END = "2026-09-04"  # 前回チャートの最終日

# (symbol, 表示名, パネル, 通貨) 前回15銘柄 + 今回追加5銘柄
SERIES = [
    ("AVGO", "Broadcom", "platform", "USD"),
    ("NVDA", "NVIDIA", "platform", "USD"),
    ("MRVL", "Marvell", "platform", "USD"),
    ("GFS", "GlobalFoundries", "platform", "USD"),
    ("CSCO", "Cisco", "platform", "USD"),
    ("COHR", "Coherent", "components", "USD"),
    ("LITE", "Lumentum", "components", "USD"),
    ("MTSI", "MACOM", "components", "USD"),
    ("POET", "POET Technologies", "components", "USD"),
    ("6503.T", "三菱電機", "japan", "JPY"),
    ("5802.T", "住友電工", "japan", "JPY"),
    ("5801.T", "古河電工", "japan", "JPY"),
    ("9432.T", "NTT", "japan", "JPY"),
    ("6965.T", "浜松ホトニクス", "japan", "JPY"),
    ("6777.T", "santec", "japan", "JPY"),
    ("5803.T", "フジクラ", "added", "JPY"),
    ("FN", "Fabrinet", "added", "USD"),
    ("AAOI", "Applied Optoelectronics", "added", "USD"),
    ("300308.SZ", "InnoLight（中際旭創）", "added", "CNY"),
    ("300502.SZ", "Eoptolink（新易盛）", "added", "CNY"),
]
GROUPS = [
    ("platform", "AIプラットフォーム／シリコンフォトニクス"),
    ("components", "光半導体・光部品の直接プレイヤー"),
    ("japan", "日本企業"),
    ("added", "今回追加：光ファイバ・トランシーバ（フジクラ・Fabrinet・AAOI・中国2社）"),
]


def ts(d):
    return int(dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone.utc).timestamp())


def fetch(symbol):
    url = ("https://query1.finance.yahoo.com/v8/finance/chart/%s?period1=%d&period2=%d"
           "&interval=1d&events=div,splits" % (symbol, ts(START), ts(END_EXCLUSIVE + dt.timedelta(days=1))))
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def daily(doc):
    r = doc["chart"]["result"][0]
    off = r["meta"].get("gmtoffset", 0)
    adj = r["indicators"]["adjclose"][0]["adjclose"]
    out = []
    for t, p in zip(r["timestamp"], adj):
        if p is None:
            continue
        d = dt.datetime.fromtimestamp(t + off, dt.timezone.utc).date()
        if START <= d < END_EXCLUSIVE:
            out.append((d.isoformat(), float(p)))
    # 同日重複（取引中の暫定値）を除く
    seen = {}
    for d, p in out:
        seen[d] = p
    return sorted(seen.items()), r["meta"].get("currency"), r.get("events", {}).get("splits", {})


def thin(rows, step=5):
    idx = list(range(0, len(rows), step))
    if idx[-1] != len(rows) - 1:
        idx.append(len(rows) - 1)
    return [rows[i] for i in idx]


def nearest_on_or_before(rows, day):
    cand = [p for d, p in rows if d <= day]
    return cand[-1] if cand else None


def main():
    offline = "--offline" in sys.argv
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw, summary = [], []
    for sym, name, group, cur in SERIES:
        path = RAW_DIR / (sym.replace(".", "_") + ".json")
        if not offline:
            try:
                path.write_text(json.dumps(fetch(sym)))
            except Exception as e:  # 取得失敗は表示から外し、要約に記録
                print("取得失敗", sym, e, file=sys.stderr)
            time.sleep(0.5)
        if not path.exists():
            summary.append([sym, name, cur, "", "", "", "", "", "", "取得失敗"])
            continue
        rows, api_cur, splits = daily(json.loads(path.read_text()))
        if api_cur and api_cur != cur:
            print("通貨不一致", sym, api_cur, cur, file=sys.stderr)
        first, last = rows[0], rows[-1]
        prev = nearest_on_or_before(rows, PREV_END)
        split_note = ";".join("%s %s" % (dt.datetime.fromtimestamp(int(k), dt.timezone.utc).date(), v.get("splitRatio"))
                              for k, v in splits.items())
        summary.append([sym, name, cur, first[0], "%.4f" % first[1], "%.4f" % prev, last[0], "%.4f" % last[1],
                        "%.1f" % ((last[1] / first[1] - 1) * 100), "%.1f" % ((last[1] / prev - 1) * 100),
                        split_note])
        raw.append({"symbol": sym, "name": name, "group": group, "currency": cur,
                    "values": [{"date": d, "price": round(p, 4)} for d, p in thin(rows)]})

    with open(HERE / "prices-summary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["symbol", "name", "currency", "first_date", "first_adjclose", "adjclose_2026-09-04",
                    "last_date", "last_adjclose", "ytd_pct", "since_2026-09-04_pct", "splits_in_period"])
        w.writerows(summary)

    last_date = max(s["values"][-1]["date"] for s in raw)
    y, m, d = last_date.split("-")
    label = "%d年%d月%d日" % (int(y), int(m), int(d))
    frag = (HERE.parent / "2026-09-05" / "chart-source.html").read_text()
    lag = [s["name"] + "は" + s["values"][-1]["date"][5:].replace("-", "/") for s in raw if s["values"][-1]["date"] != last_date]
    note = "（休場により%sまで）" % "、".join(lag) if lag else ""
    frag = frag.replace("2026年9月4日まで", label + "まで" + note)
    frag = re.sub(r"const raw=\[.*?\];\n", lambda _: "const raw=" + json.dumps(raw, ensure_ascii=False, separators=(",", ":")) + ";\n", frag, count=1, flags=re.S)
    groups_js = "const groups=[\n" + ",\n".join('    {key:"%s",title:"%s"}' % g for g in GROUPS) + "\n  ];"
    frag = re.sub(r"const groups=\[.*?\];", lambda _: groups_js, frag, count=1, flags=re.S)
    frag = frag.replace('c==="JPY"?"¥"+d3.format(",.0f")(v):"$"+d3.format(",.2f")(v)',
                        'c==="JPY"?"¥"+d3.format(",.0f")(v):(c==="CNY"?"CN¥"+d3.format(",.2f")(v):"$"+d3.format(",.2f")(v))')
    frag = frag.replace("出所：Yahoo Finance Chart API（日次データを約週次に間引いて表示）",
                        "出所：Yahoo Finance Chart API（%s取得、日次データを5取引日ごとに間引いて表示）" % dt.date.today().isoformat())
    (HERE / "chart-source.html").write_text(frag)

    outer = PREV_INDEX.read_text()
    m_ = re.search(r'srcdoc="(.*?)"></iframe>', outer, re.S)
    inner = html.unescape(m_.group(1))
    a = inner.find('<div id="photonic-stocks-2026"')
    b = inner.find("</script>", inner.find("groups.forEach(buildPanel);")) + len("</script>")
    new_inner = inner[:a] + frag.rstrip("\n") + inner[b:]
    new_outer = outer[:m_.start(1)] + html.escape(new_inner, quote=True) + outer[m_.end(1):]
    new_outer = new_outer.replace("Photonic Stocks 2026", "Photonic Stocks 2026 (to %s)" % last_date)
    (HERE / "index.html").write_text(new_outer)
    print("最終取引日", last_date, "系列数", len(raw))


if __name__ == "__main__":
    main()
