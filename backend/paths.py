"""Explicit allowlists for what the dashboard may serve or ship in its image.

The same rules decide what is served over HTTP and what infra/deploy.py stages
for the container build, so a file that is never served is never uploaded.
"""
from pathlib import Path, PurePosixPath
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]

# Shell assets: files directly inside web/ (no subdirectories).
SHELL_TYPES = {
    'html': 'text/html; charset=utf-8',
    'js': 'text/javascript; charset=utf-8',
    'css': 'text/css; charset=utf-8',
    'svg': 'image/svg+xml',
    'png': 'image/png',
    'ico': 'image/x-icon',
    'woff2': 'font/woff2',
}

# Research files. Markdown and module sources are shown as text; the shell renders them.
RESEARCH_TYPES = {
    'html': 'text/html; charset=utf-8',
    'md': 'text/plain; charset=utf-8',
    'pdf': 'application/pdf',
    'json': 'application/json; charset=utf-8',
    'js': 'text/javascript; charset=utf-8',
    'mjs': 'text/plain; charset=utf-8',
    'css': 'text/css; charset=utf-8',
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'svg': 'image/svg+xml',
    'txt': 'text/plain; charset=utf-8',
    'csv': 'text/csv; charset=utf-8',
}

# Local-only working material is never served, even when present on disk.
EXCLUDED_SEGMENTS = {'working', 'qa'}


def extension(name):
    suffix = PurePosixPath(name).suffix
    return suffix[1:].casefold() if suffix else ''


def allowed_segments(parts):
    """Reject hidden files, traversal, working/ and qa/ (case-insensitively; macOS is)."""
    if not parts:
        return False
    for part in parts:
        if not part or part.startswith('.') or part.casefold() in EXCLUDED_SEGMENTS:
            return False
        if '\\' in part or '\x00' in part or ':' in part:
            return False
    return True


def research_relative(relative):
    """Return the MIME type when a research-relative POSIX path may be served, else None."""
    parts = PurePosixPath(relative).parts
    if not allowed_segments(parts) or PurePosixPath(relative).is_absolute():
        return None
    return RESEARCH_TYPES.get(extension(parts[-1]))


def resolve_research(research_dir, url_path):
    """Map `/research/<path>` (still percent-encoded) to (file, mime) or None.

    Checks both the requested path and the resolved path, so symlinks cannot
    escape research/ or reach excluded folders.
    """
    prefix = '/research/'
    if not url_path.startswith(prefix):
        return None
    try:
        relative = unquote(url_path[len(prefix):], errors='strict')
    except UnicodeDecodeError:
        return None
    if not relative or relative.endswith('/') or '//' in relative:
        return None
    mime = research_relative(relative)
    if mime is None:
        return None
    base = Path(research_dir).resolve()
    try:
        target = (base / relative).resolve(strict=True)
        inside = target.relative_to(base)
    except (OSError, ValueError, RuntimeError):
        return None
    if not target.is_file() or research_relative(inside.as_posix()) != mime:
        return None
    return target, mime


def shell_assets(web_dir):
    """Scan web/ (top level only) into {'/<filename>': (path, mime)}."""
    assets = {}
    web = Path(web_dir)
    if not web.is_dir():
        return assets
    for entry in web.iterdir():
        mime = SHELL_TYPES.get(extension(entry.name))
        if mime and not entry.name.startswith('.') and entry.is_file() and not entry.is_symlink():
            assets['/' + entry.name] = (entry, mime)
    index = web / 'index.html'
    if index.is_file():
        assets['/'] = (index, SHELL_TYPES['html'])
    return assets


def research_files(research_dir):
    """Every research file that may be served (used to stage the image build)."""
    base = Path(research_dir)
    for path in sorted(base.rglob('*')):
        if path.is_file() and not path.is_symlink():
            relative = path.relative_to(base).as_posix()
            if research_relative(relative):
                yield relative
