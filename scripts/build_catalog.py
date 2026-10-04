"""Build research/catalog.json for the Asset Hub dashboard.

Scans research/{themes,companies}/<slug>/<YYYY-MM-DD>/ and lists the documents the
web app can show. Every dated folder is its own entry; the web app treats the newest one of
each slug as current and the older ones as archives. Titles come from the root README table and each folder README;
small overrides below keep labels stable. Run from anywhere:

    python3 scripts/build_catalog.py          # write research/catalog.json
    python3 scripts/build_catalog.py --check  # exit 1 when the file is out of date

The file is rewritten only when its content (other than generatedAt) changes.
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
OUTPUT = RESEARCH / "catalog.json"
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LINK = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")

GROUPS = (("themes", "テーマ", "theme"), ("companies", "企業", "company"))
# Top-level files in display order: file name -> (type, default label).
FILES = {
    "index.html": ("html", "ダッシュボード"),
    "chart-source.html": ("html", "編集元HTML"),
    "report.md": ("md", "レポート"),
    "stock-drivers.md": ("md", "株価の変動要因"),
    "screen.md": ("md", "許容損失別の組み合わせ一覧"),
    "README.md": ("md", "README・資料一覧"),
    "related-links.md": ("md", "関連資料・着想元"),
    "valuation.mjs": ("code", "評価モデル"),
}
# Manual overrides, keyed by slug. Titles fall back to the root README table.
TITLE_OVERRIDES = {}
LABEL_OVERRIDES = {
    "ai-supply-chain": {"report.md": "工程別レポート", "README.md": "調査範囲・出典方針"},
    "photonics": {"index.html": "株価比較チャート", "report.md": "考察レポート"},
    "ai-year-end-comparison": {"report.md": "比較レポート", "README.md": "調査範囲・前提"},
    "ai-business-quality": {"report.md": "評価レポート", "README.md": "調査範囲・前提"},
    "285A-kioxia": {"report.md": "投資判断レポート", "README.md": "資料・引き継ぎ"},
    "523A-seiwa": {"README.md": "決算資料・調査素材"},
    "6857-advantest": {"README.md": "調査の前提・資料"},
    "4062-ibiden": {"README.md": "調査の前提・資料"},
}


def strip_links(text):
    return LINK.sub(lambda m: m.group(1), text).replace("*", "").strip()


def root_titles():
    """Map research folder (repo-relative) to the first column of the root README table."""
    titles = {}
    for line in (ROOT / "README.md").read_text(encoding="utf-8").splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 3 or not line.lstrip().startswith("|"):
            continue
        for _, href in LINK.findall(line):
            parts = Path(href).parts
            if len(parts) >= 4 and parts[0] == "research":
                titles.setdefault("/".join(parts[:4]), strip_links(cells[0]))
                # Target folder too, so every dated version of a target shares one title.
                titles.setdefault("/".join(parts[:3]), strip_links(cells[0]))
    return titles


def readme_title(folder):
    readme = folder / "README.md"
    if not readme.exists():
        return ""
    first = readme.read_text(encoding="utf-8").splitlines()[0]
    return re.sub(r"^#\s*", "", first).split("｜")[0].strip()


def pdf_label(folder, relative):
    """Use the folder README's link text, or the description cell next to a file-name link."""
    readme = folder / "README.md"
    lines = readme.read_text(encoding="utf-8").splitlines() if readme.exists() else []
    for line in lines:
        for text, href in LINK.findall(line):
            if href != relative:
                continue
            if text and text != Path(relative).name:
                return text
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) >= 2:
                return re.split(r"[：:]", strip_links(cells[1]))[0].strip()
    return Path(relative).name


def readme_position(folder, relative):
    readme = folder / "README.md"
    text = readme.read_text(encoding="utf-8") if readme.exists() else ""
    index = text.find(f"]({relative})")
    return index if index >= 0 else len(text)


def build():
    titles = root_titles()
    groups = []
    for directory, label, kind in GROUPS:
        entries = []
        base = RESEARCH / directory
        for slug_dir in sorted(p for p in base.iterdir() if p.is_dir()) if base.exists() else []:
            for date_dir in sorted((p for p in slug_dir.iterdir() if p.is_dir() and DATE.match(p.name)), reverse=True):
                slug, date = slug_dir.name, date_dir.name
                folder = date_dir.relative_to(ROOT).as_posix()
                overrides = LABEL_OVERRIDES.get(slug, {})
                items = []
                for name, (file_type, default) in FILES.items():
                    if (date_dir / name).is_file():
                        items.append({"label": overrides.get(name, default), "path": f"{folder}/{name}", "type": file_type})
                sources = date_dir / "sources"
                pdfs = sorted(sources.rglob("*.pdf")) if sources.is_dir() else []
                pdfs.sort(key=lambda pdf: readme_position(date_dir, pdf.relative_to(date_dir).as_posix()))
                for pdf in pdfs:
                    relative = pdf.relative_to(date_dir).as_posix()
                    items.append({"label": overrides.get(relative, pdf_label(date_dir, relative)), "path": f"{folder}/{relative}", "type": "pdf"})
                if not items:
                    continue
                entry = {
                    "id": f"{slug}-{date}",
                    "title": TITLE_OVERRIDES.get(slug) or titles.get(folder) or titles.get(slug_dir.relative_to(ROOT).as_posix()) or readme_title(date_dir) or slug,
                    "date": date,
                    "kind": kind,
                    "slug": slug,
                    "items": items,
                    "folder": folder,
                }
                code = re.match(r"^([0-9A-Z]{4})-", slug)
                if kind == "company" and code:
                    entry["code"] = code.group(1)
                entries.append(entry)
        order = list(titles)
        # Newest first; on the same date keep the root README order.
        entries.sort(key=lambda e: e["id"])
        entries.sort(key=lambda e: order.index(e["folder"]) if e["folder"] in order else len(order))
        entries.sort(key=lambda e: e["date"], reverse=True)
        for entry in entries:
            del entry["folder"]
        groups.append({"id": directory, "label": label, "entries": entries})
    return {"version": 1, "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"), "groups": groups}


def comparable(catalog):
    return {key: value for key, value in catalog.items() if key != "generatedAt"}


def main(argv):
    catalog = build()
    current = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else None
    unchanged = current is not None and comparable(current) == comparable(catalog)
    if "--check" in argv:
        if not unchanged:
            raise SystemExit("research/catalog.json is out of date; run python3 scripts/build_catalog.py")
        print("research/catalog.json is up to date")
        return
    if unchanged:
        print("research/catalog.json unchanged")
        return
    OUTPUT.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    count = sum(len(e["items"]) for g in catalog["groups"] for e in g["entries"])
    print(f"Wrote research/catalog.json ({count} documents)")


if __name__ == "__main__":
    main(sys.argv[1:])
