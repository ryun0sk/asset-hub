"""List every 2- and 3-stock equal-weight combination with the attributes needed to screen it.

Reads working/compare-results.json (from compare.py) and writes screen.csv (every combination)
and screen.md (counts for every loss threshold) next to this file. No ranking: rows are ordered
by size, then by combination key. Run from anywhere:

    python3 research/themes/ai-year-end-comparison/2026-10-03/screen.py
"""
import csv
import importlib.util
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "working" / "compare-results.json"
OUTPUT = HERE / "screen.csv"
SUMMARY = HERE / "screen.md"
# Loss thresholds for the 2σ lower bound (万円); None = no limit.
THRESHOLDS = [(-200, "−200万円まで"), (-300, "−300万円まで"), (-400, "−400万円まで"), (-500, "−500万円まで"), (None, "制限なし")]
CAPITAL = 10_000_000
HORIZON = 60  # Tokyo trading days from 10/5 to 12/30

# Earnings inside the 10/27-10/30 cluster (JST reaction day). Confirmed = company/IR calendar
# in report.md section 3; tentative = external calendars only.
CLUSTER_CONFIRMED = {
    "4063.T": "10/27", "6857.T": "10/28", "6501.T": "10/28", "4062.T": "10/29",
    "8035.T": "10/30", "5802.T": "10/30", "285A.T": "10/30", "SNDK": "10/30",
}
CLUSTER_TENTATIVE = {"000660.KS": "10/27頃", "VRT": "10/21〜28頃"}


def main():
    results = json.loads(RESULTS.read_text(encoding="utf-8"))
    spec = importlib.util.spec_from_file_location("compare", HERE / "compare.py")
    compare = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(compare)  # only defines constants; main() runs under __main__
    names = compare.NAME
    rows = []
    for key, p in results["portfolios"].items():
        syms = key.split("+")
        sigma = p["vol"] * math.sqrt(HORIZON / 250)
        confirmed = [f"{names[s]}({CLUSTER_CONFIRMED[s]})" for s in syms if s in CLUSTER_CONFIRMED]
        tentative = [f"{names[s]}({CLUSTER_TENTATIVE[s]})" for s in syms if s in CLUSTER_TENTATIVE]
        rows.append({
            "銘柄数": p["k"],
            "組み合わせ": "＋".join(names[s] for s in syms),
            "コード": key,
            "地域": p["rtype"],
            "サブテーマの組み合わせ": p["ttype"],
            "年率ボラ（円建て）": round(p["vol"] * 100, 1),
            "平均相関（週次1年）": round(p["meanCorr"], 2),
            "分散比": round(p["ratio"], 2),
            "週次β（対日経）": round(p["wbeta"], 2),
            "1σ下限（万円）": round(CAPITAL * (math.exp(-sigma) - 1) / 10_000),
            "1σ上限（万円）": round(CAPITAL * (math.exp(sigma) - 1) / 10_000),
            "2σ下限（万円）": round(CAPITAL * (math.exp(-2 * sigma) - 1) / 10_000),
            "2σ上限（万円）": round(CAPITAL * (math.exp(2 * sigma) - 1) / 10_000),
            "過去12週 最悪（万円）": round(CAPITAL * p["histMin"] / 10_000),
            "過去12週 中央値（万円）": round(CAPITAL * p["histMed"] / 10_000),
            "10/27〜30の決算（確認済）": len(confirmed),
            "10/27〜30の決算（未確認を含む）": len(confirmed) + len(tentative),
            "該当する決算": " ".join(confirmed + tentative),
        })
    rows.sort(key=lambda r: (r["銘柄数"], r["コード"]))
    with OUTPUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {OUTPUT.name}: {len(rows)} combinations")
    write_summary(rows)
    for k in (2, 3):
        subset = [r for r in rows if r["銘柄数"] == k]
        print(f"-- {k}銘柄: {len(subset)}通り, 2σ下限が−500万円より大きい損失: {sum(r['2σ下限（万円）'] < -500 for r in subset)}通り")
        for n in range(k + 1):
            group = sorted(r["年率ボラ（円建て）"] for r in subset if r["10/27〜30の決算（確認済）"] == n)
            if not group:
                continue
            loss = sorted(r["2σ下限（万円）"] for r in subset if r["10/27〜30の決算（確認済）"] == n)
            hist = sorted(r["過去12週 最悪（万円）"] for r in subset if r["10/27〜30の決算（確認済）"] == n)
            mid = len(group) // 2
            print(f"   決算集中期間の確認済み決算{n}社: {len(group)}通り, ボラ中央値{group[mid]}%, 2σ下限中央値{loss[mid]}万円, 過去12週最悪の中央値{hist[mid]}万円")


def median(values):
    values = sorted(values)
    return values[len(values) // 2] if values else None


def write_summary(rows):
    lines = [
        "# 許容損失の全パターン別 組み合わせ一覧｜2026-10-03",
        "",
        "[比較レポート](report.md)第5節の全組み合わせ（2銘柄231通り・3銘柄1,540通り、1,000万円を均等配分）を、年末時点で許容できる最大損失の水準ごとに絞り込んだ一覧。全件と各列の値は [screen.csv](screen.csv)。",
        "",
        "## この資料の位置づけ（推奨ではない）",
        "",
        "- 条件を満たす組み合わせを機械的に数え、並べたもの。特定の組み合わせ・配分を推奨しない。並び順は銘柄コード順で、順位ではない。",
        "- どの損失水準を選ぶか、決算集中期間（10/27〜10/30）をまたぐかは読者が決める前提で、すべてのパターンを並べた。",
        "- 記載日時点の過去データによる機械的な計算で、将来の値動きを予測するものではない。個人向けの投資助言ではない。",
        "",
        "## 計算の前提【独自計算】",
        "",
        f"- 2σ下限＝1,000万円×(exp(−2σ)−1)。σ＝組み合わせの円建て年率ボラ（1年）×√({HORIZON}/250)。ドリフト0の対数正規による「かなり悪いケース」の目安で、これを超える損失も起こり得る。",
        "- 組み合わせのボラは各銘柄の円建て日次ボラ（1年）と週次相関（1年）から計算（レポート第5-3節と同じ）。手数料・税金・為替コストは含まない。",
        "- 決算集中期間の社数は、10/27〜10/30（日本時間の反応日）に決算がある銘柄の数。確認済み＝信越化学10/27、アドバンテスト・日立10/28、イビデン10/29、東京エレクトロン・住友電工・キオクシア・Sandisk（米国10/29）10/30。未確認＝SK hynix（10/27頃）、Vertiv（10/21〜28頃）。",
        "",
        "## 損失の水準ごとの通り数",
        "",
        "| 2σ下限の許容水準 | 銘柄数 | 通り数 | 決算集中期間の確認済み決算 0社／1社／2社／3社 | 日本のみ／海外のみ／日本＋海外 | 年率ボラ中央値 | 週次β中央値 | 過去12週 最悪の中央値 | 過去12週 中央値の中央値 |",
        "|---|---:|---:|---|---|---:|---:|---:|---:|",
    ]
    for limit, label in THRESHOLDS:
        for k in (2, 3):
            subset = [r for r in rows if r["銘柄数"] == k and (limit is None or r["2σ下限（万円）"] >= limit)]
            if not subset:
                lines.append(f"| {label} | {k} | 0 | — | — | — | — | — | — |")
                continue
            by_earnings = "／".join(str(sum(r["10/27〜30の決算（確認済）"] == n for r in subset)) for n in range(4)) if k == 3 else "／".join(str(sum(r["10/27〜30の決算（確認済）"] == n for r in subset)) for n in range(3)) + "／—"
            regions = "／".join(str(sum(r["地域"] == region for r in subset)) for region in ("日本のみ", "海外のみ", "日本＋海外"))
            lines.append(
                f"| {label} | {k} | {len(subset)} | {by_earnings} | {regions} | {median(r['年率ボラ（円建て）'] for r in subset)}% | "
                f"{median(r['週次β（対日経）'] for r in subset)} | {median(r['過去12週 最悪（万円）'] for r in subset)}万円 | {median(r['過去12週 中央値（万円）'] for r in subset)}万円 |")
    lines += ["", "- 2σ下限の幅（全組み合わせ）："]
    for k in (2, 3):
        subset = sorted((r["2σ下限（万円）"], r["組み合わせ"]) for r in rows if r["銘柄数"] == k)
        lines.append(f"  - {k}銘柄：最も損失が小さいもので{subset[-1][0]}万円（{subset[-1][1]}）、最も大きいもので{subset[0][0]}万円（{subset[0][1]}）。")
    lines += [
        "- 過去12週の値は、過去1年に当初均等で買って12週持った場合の損益（重なりあり）。過去1年はAI関連株の大相場で、中央値は上方に偏っている。将来の期待値として読まない。",
        "",
        "## 決算集中期間の社数ごとの比較（制限なし）",
        "",
        "| 銘柄数 | 確認済み決算の社数 | 通り数 | 年率ボラ中央値 | 2σ下限の中央値 | 過去12週 最悪の中央値 |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for k in (2, 3):
        for n in range(k + 1):
            subset = [r for r in rows if r["銘柄数"] == k and r["10/27〜30の決算（確認済）"] == n]
            if subset:
                lines.append(f"| {k} | {n} | {len(subset)} | {median(r['年率ボラ（円建て）'] for r in subset)}% | {median(r['2σ下限（万円）'] for r in subset)}万円 | {median(r['過去12週 最悪（万円）'] for r in subset)}万円 |")
    lines += [
        "",
        "- 決算集中期間の決算が多い組み合わせほど、ボラと2σの損失は大きい傾向がある。ただし差は中央値で数十万円程度で、銘柄自体の値動きの大きさの差のほうが大きい。決算の1日に±10％前後動いた例（アドバンテスト・イビデン・キオクシア）は、ボラの数値に含まれる以上の一度の変動になり得る（レポート第3節）。",
        "",
        "## −300万円までの組み合わせ（全件）",
        "",
        "2σ下限が−300万円以内に収まる組み合わせはこれで全部（−200万円以内はなし）。コード順で、順位ではない。",
        "",
        "| 銘柄数 | 組み合わせ | 地域 | 年率ボラ | 2σ下限 | 1σの幅 | 週次β | 決算集中期間の決算 |",
        "|---:|---|---|---:|---:|---|---:|---|",
    ]
    for r in rows:
        if r["2σ下限（万円）"] >= -300:
            lines.append(f"| {r['銘柄数']} | {r['組み合わせ']} | {r['地域']} | {r['年率ボラ（円建て）']}% | {r['2σ下限（万円）']}万円 | {r['1σ下限（万円）']}〜+{r['1σ上限（万円）']}万円 | {r['週次β（対日経）']} | {r['該当する決算'] or '—'} |")
    lines += [
        "",
        "- このグループは、値動きの小さい6銘柄（日立・信越化学・TSMC・NVIDIA・Broadcom・ASML）を2社以上含む組み合わせが中心で、東京エレクトロン・ディスコ・Vertiv・アドバンテストはそれらと組む形でのみ入る。損失の幅が小さい代わりに、週次βも低く、AI相場の上昇への連動も小さい（レポート第5-3節）。",
        "- −400万円・−500万円・制限なしの組み合わせは件数が多いため、[screen.csv](screen.csv)の「2σ下限（万円）」列で絞り込んで確認する。",
        "",
        "## 再現方法",
        "",
        "```sh",
        "python3 research/themes/ai-year-end-comparison/2026-10-03/compare.py --offline   # 先に計算結果を作る",
        "python3 research/themes/ai-year-end-comparison/2026-10-03/screen.py            # screen.csv と screen.md を作る",
        "```",
        "",
    ]
    SUMMARY.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {SUMMARY.name}")


if __name__ == "__main__":
    main()
