"""Check design-token usage and CSP-safe markup in web/ without Node. See docs/design-system.md."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOUNDATION = "tokens.css"
# Shell and cost CSS ported from the reference dashboard. They keep its literal sizes, so only
# undefined token references, token definitions and chart overrides are enforced there.
LEGACY_CSS = {"styles.css", "costs.css"}
# JavaScript that emits chart markup must leave every visual decision to charts.css.
CHART_JS = {"charts.js", "cost-view.js", "asset-view.js"}
REFERENCE = re.compile(r"var\(\s*(--[\w-]+)")
DECLARATION = re.compile(r"(?:^|[;{])\s*([\w-]+)\s*:\s*([^;}]+)")
LENGTH = re.compile(r"[\d.]+(?:px|rem|em)\b")
JS_LITERALS = re.compile(r"#[0-9a-fA-F]{3,8}\b|\bfont-size\b|\b(?:fill|stroke|stroke-width|font-size)=[\"'][^\"'$]")
CHART_ONLY = re.compile(r"\.ui-chart")
# The shell is served with `style-src 'self'; script-src 'self'`: no inline styles or scripts.
INLINE_STYLE = re.compile(r"<style\b|\sstyle\s*=\s*[\"'{]", re.I)
INLINE_SCRIPT = re.compile(r"<script\b(?![^>]*\bsrc=)[^>]*>", re.I)
INLINE_HANDLER = re.compile(r"<[^>]+\son[a-z]+\s*=", re.I)


def strip_comments(text):
    return re.sub(r"/\*.*?\*/", "", text, flags=re.S)


def check(web=None):
    web = Path(web) if web else ROOT / "web"
    errors = []
    sources = {path.relative_to(web).as_posix(): strip_comments(path.read_text(encoding="utf-8")) for path in web.rglob("*.css")}
    if FOUNDATION not in sources:
        return [f"Missing foundation: {FOUNDATION}"]
    definitions = dict(re.findall(r"(--[\w-]+)\s*:\s*([^;}]+)", sources[FOUNDATION]))

    for name, source in sources.items():
        for reference in REFERENCE.findall(source):
            if reference not in definitions:
                errors.append(f"{name}: undefined token {reference}")
        if name == FOUNDATION:
            continue
        if re.search(r"(?:^|[;{\s])--[\w-]+\s*:", source):
            errors.append(f"{name}: define custom properties in tokens.css")
        if name in LEGACY_CSS:
            if CHART_ONLY.search(source):
                errors.append(f"{name}: chart classes belong to charts.css")
            continue
        for prop, value in DECLARATION.findall(source):
            value = value.strip()
            if prop in {"font-size", "font-weight", "font-family", "line-height", "font"}:
                if value in {"inherit", "normal"}:
                    continue
                if "var(" not in value or LENGTH.search(value) or re.fullmatch(r"[\d.]+", value):
                    errors.append(f"{name}: use tokens for {prop}: {value}")
            if re.fullmatch(r"border(?:-(?:top|bottom|left|right))?(?:-width)?|outline(?:-width|-offset)?|stroke-width", prop):
                if LENGTH.search(value) or (prop == "stroke-width" and re.fullmatch(r"[\d.]+", value) and value != "0"):
                    errors.append(f"{name}: use tokens for {prop}: {value}")
            if prop in {"z-index", "opacity"} and "var(" not in value and value not in {"0", "1", "auto", "inherit"}:
                errors.append(f"{name}: use tokens for {prop}: {value}")
            if re.fullmatch(r"(?:padding|margin)(?:-[\w-]+)?|(?:row-|column-)?gap", prop) and LENGTH.search(value):
                errors.append(f"{name}: use tokens for {prop}: {value}")
            if re.search(r"#[0-9a-fA-F]{3,8}\b|\b(?:rgba?|hsla?)\(", value):
                errors.append(f"{name}: use a colour token for {prop}: {value}")

    # HTML and JS: CSP-safe markup, and chart markup that bypasses charts.css.
    for path in (*web.rglob("*.html"), *web.rglob("*.js")):
        name, source = path.relative_to(web).as_posix(), path.read_text(encoding="utf-8")
        if INLINE_STYLE.search(source):
            errors.append(f"{name}: inline style is blocked by the CSP; use a class in a stylesheet")
        if path.suffix == ".html" and INLINE_SCRIPT.search(source):
            errors.append(f"{name}: inline <script> is blocked by the CSP; load a file with src")
        if INLINE_HANDLER.search(source):
            errors.append(f"{name}: inline event handler attributes are blocked by the CSP")
        if name in CHART_JS:
            for literal in JS_LITERALS.findall(source):
                errors.append(f"{name}: chart markup must use charts.css, found {literal!r}")

    visited = set()

    def visit(token, active):
        if token in active:
            errors.append("Cyclic token: " + " -> ".join((*active, token)))
            return
        if token in visited:
            return
        for reference in REFERENCE.findall(definitions.get(token, "")):
            visit(reference, (*active, token))
        visited.add(token)

    for token in definitions:
        visit(token, ())
    return sorted(set(errors))


if __name__ == "__main__":
    errors = check()
    if errors:
        raise SystemExit("\n".join(errors))
    print("Design tokens: references, cycles, CSP-safe markup, chart markup and new-file literals OK")
