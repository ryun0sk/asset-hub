"""Read-only private dashboard server.

Cloud (K_SERVICE set): every request must carry a valid IAP assertion for an
allowed email. Local: binds 127.0.0.1 and accepts only Host localhost/127.0.0.1.
Only GET/HEAD are accepted; nothing is writable over HTTP.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
import argparse
import json
import os
import shutil
import threading
import time
from pathlib import Path

from .paths import ROOT, resolve_research, shell_assets

SHELL_CSP = ("default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-src 'self'; "
             "connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
# Research HTML is self-contained (inline scripts/styles, chart libraries from CDNs) and
# is iframed by the shell, so it may only be framed by this origin.
RESEARCH_HTML_CSP = ("default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; "
                     "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: blob:; "
                     "font-src 'self' data:; connect-src 'self'; frame-src 'self'; object-src 'none'; "
                     "base-uri 'none'; form-action 'none'; frame-ancestors 'self'")
# PDFs keep the browser viewer working (a CSP sandbox breaks it).
RESEARCH_PDF_CSP = "frame-ancestors 'self'"
# Any other research file (SVG, JSON, text...) is inert even when opened directly.
RESEARCH_FILE_CSP = "default-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:; frame-ancestors 'self'; sandbox"
API_CSP = "default-src 'none'; frame-ancestors 'none'"
LOCAL_HOSTS = ('127.0.0.1', 'localhost')
IAP_HEADER = 'X-Goog-IAP-JWT-Assertion'
# Static files change only with a new image: browsers keep a private copy and revalidate by ETag.
STATIC_CACHE = 'private, no-cache'
COST_CACHE_SECONDS = 60


def etag(file):
    stat = file.stat()
    return f'"{stat.st_size:x}-{stat.st_mtime_ns:x}"'


class Handler(BaseHTTPRequestHandler):
    server_version = 'AssetHub'
    sys_version = ''

    def send_headers(self, status, mime, csp, length, cache='no-store', extra=None):
        self.send_response(status)
        if mime:
            self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(length))
        self.send_header('Cache-Control', cache)
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', csp)
        for name, value in (extra or {}).items():
            self.send_header(name, value)
        self.end_headers()

    def send_bytes(self, status, content, mime, csp, head=False, extra=None):
        self.send_headers(status, mime, csp, len(content), extra=extra)
        if not head:
            self.wfile.write(content)

    def send_file(self, file, mime, csp, head):
        """Stream a static file (research pages reach ~17MB) and answer revalidations with 304."""
        tag = etag(file)
        if tag in [value.strip() for value in self.headers.get('If-None-Match', '').split(',')]:
            self.send_headers(304, None, csp, 0, STATIC_CACHE, {'ETag': tag})
            return
        self.send_headers(200, mime, csp, file.stat().st_size, STATIC_CACHE, {'ETag': tag})
        if not head:
            with file.open('rb') as source:
                shutil.copyfileobj(source, self.wfile, 1 << 20)

    def json_response(self, status, payload, head=False, extra=None):
        content = json.dumps(payload, ensure_ascii=False).encode()
        self.send_bytes(status, content, 'application/json; charset=utf-8', API_CSP, head, extra)

    def error(self, status, message, head=False, extra=None):
        if urlsplit(self.path).path.startswith('/api/'):
            self.json_response(status, {'error': message}, head, extra)
        else:
            self.send_bytes(status, message.encode(), 'text/plain; charset=utf-8', API_CSP, head, extra)

    def authorized(self, head=False):
        """IAP in cloud, loopback Host locally. Sends the rejection itself."""
        if self.server.cloud:
            try:
                self.server.verify(self.headers.get(IAP_HEADER, ''), self.server.audience, self.server.allowed)
            except PermissionError:
                self.error(403, 'Forbidden', head)
                return False
            return True
        host = self.headers.get('Host', '')
        host = host if host.startswith('[') else host.rsplit(':', 1)[0]
        if host not in LOCAL_HOSTS:
            self.error(403, 'Forbidden', head)
            return False
        return True

    def serve(self, head):
        if not self.authorized(head):
            return
        path = urlsplit(self.path).path
        if path == '/api/catalog':
            self.serve_catalog(head)
        elif path == '/api/costs':
            try:
                payload = self.server.costs()
            except Exception:
                self.json_response(503, {'error': '費用データを読み込めませんでした。'}, head)
                return
            self.json_response(200, payload, head)
        elif path.startswith('/research/'):
            self.serve_research(path, head)
        else:
            asset = self.server.shell().get(path)
            if not asset:
                self.error(404, 'Not found', head)
                return
            file, mime = asset
            self.send_file(file, mime, SHELL_CSP, head)

    def serve_catalog(self, head):
        catalog = self.server.research_dir / 'catalog.json'
        try:
            payload = json.loads(catalog.read_text(encoding='utf-8'))
        except FileNotFoundError:
            self.json_response(404, {'error': 'カタログがありません。'}, head)
            return
        except (OSError, ValueError):
            self.json_response(503, {'error': 'カタログを読み込めませんでした。'}, head)
            return
        self.json_response(200, payload, head)

    def serve_research(self, path, head):
        found = resolve_research(self.server.research_dir, path)
        if not found:
            self.error(404, 'Not found', head)
            return
        file, mime = found
        if mime.startswith('text/html'):
            csp = RESEARCH_HTML_CSP
        elif mime == 'application/pdf':
            csp = RESEARCH_PDF_CSP
        else:
            csp = RESEARCH_FILE_CSP
        self.send_file(file, mime, csp, head)

    def do_GET(self):
        self.serve(head=False)

    def do_HEAD(self):
        self.serve(head=True)

    def not_allowed(self):
        if self.authorized():
            self.error(405, 'Method not allowed', extra={'Allow': 'GET, HEAD'})

    do_POST = do_PUT = do_PATCH = do_DELETE = do_OPTIONS = not_allowed

    def log_message(self, *_):
        pass


class DashboardServer(ThreadingHTTPServer):
    daemon_threads = True

    def configure(self, cloud, web_dir=ROOT / 'web', research_dir=ROOT / 'research'):
        self.cloud = cloud
        self.web_dir = Path(web_dir)
        self.research_dir = Path(research_dir)
        # The image is immutable in cloud; locally rescan so new web/ files appear without restart.
        self._assets = shell_assets(self.web_dir) if cloud else None
        self._cost_lock = threading.Lock()
        self._cost_cache = (0.0, None)
        return self

    def shell(self):
        return self._assets if self._assets is not None else shell_assets(self.web_dir)

    def costs(self):
        """The snapshot changes once a day; reuse a GCS read for a minute across requests."""
        from .costs import cost_payload
        with self._cost_lock:
            loaded, payload = self._cost_cache
            if payload is None or time.monotonic() - loaded >= COST_CACHE_SECONDS:
                payload = cost_payload(self.cost_document)
                self._cost_cache = (time.monotonic(), payload)
            return payload


def cloud_settings(environ):
    """Fail closed: cloud mode needs an explicit audience, viewers and state bucket."""
    audience = environ.get('ASSET_IAP_AUDIENCE', '')
    allowed = frozenset(filter(None, environ.get('ASSET_ALLOWED_EMAILS', '').casefold().split(',')))
    bucket = environ.get('ASSET_STATE_BUCKET', '')
    if not audience or not allowed or any('@' not in email for email in allowed):
        raise SystemExit('Explicit IAP audience and viewers are required')
    if not bucket:
        raise SystemExit('ASSET_STATE_BUCKET is required')
    return audience, allowed, bucket


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=int(os.environ.get('PORT', '4330')))
    args = parser.parse_args()
    cloud = bool(os.environ.get('K_SERVICE'))
    from .costs import cost_document
    if cloud:
        audience, allowed, bucket = cloud_settings(os.environ)
        from .cloud import verify_iap
        document = cost_document(bucket)
    else:
        document = cost_document(None)
    server = DashboardServer(('0.0.0.0' if cloud else '127.0.0.1', args.port), Handler).configure(cloud)
    server.cost_document = document
    if cloud:
        server.audience, server.allowed, server.verify = audience, allowed, verify_iap
    print(f'Asset Hub listening on port {args.port}; IAP={cloud}', flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main()
