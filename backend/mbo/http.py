"""Read-only loopback HTTP boundary for the offline MBO workspace.

Only frozen, public-facing DTOs from ``core`` are read here.  This module does
not import the dashboard's assets, billing, cloud, or authentication clients.
"""
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from socketserver import TCPServer
from urllib.parse import parse_qsl, urlsplit
import json
import os
import re
import stat
import uuid


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = ROOT / 'data' / 'private' / 'mbo'
API_CSP = "default-src 'none'; frame-ancestors 'none'"
MBO_CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self'; "
    "img-src 'self' data:; font-src 'self'; connect-src 'self'; "
    "object-src 'none'; frame-src 'none'; base-uri 'none'; "
    "form-action 'none'; frame-ancestors 'none'"
)
ASSETS = {
    '/': ('mbo.html', 'text/html; charset=utf-8'),
    '/mbo.html': ('mbo.html', 'text/html; charset=utf-8'),
    '/mbo-app.js': ('mbo-app.js', 'text/javascript; charset=utf-8'),
    '/mbo-cases.js': ('mbo-cases.js', 'text/javascript; charset=utf-8'),
    '/mbo-census.js': ('mbo-census.js', 'text/javascript; charset=utf-8'),
    '/mbo-census-data.js': ('mbo-census-data.js', 'text/javascript; charset=utf-8'),
    '/mbo-case-data.js': ('mbo-case-data.js', 'text/javascript; charset=utf-8'),
    '/mbo.css': ('mbo.css', 'text/css; charset=utf-8'),
    '/tokens.css': ('tokens.css', 'text/css; charset=utf-8'),
    '/favicon.svg': ('favicon.svg', 'image/svg+xml'),
}
IDENTIFIER = re.compile(r'[A-Za-z0-9_-]{1,100}\Z')
MAX_STATIC_BYTES = 4 * 1024 * 1024


# Lazy wrappers keep startup/HTTP tests independent of collection dependencies.
def read_status(data_dir):
    from .core import read_status as implementation
    return implementation(data_dir)


def read_runs(data_dir):
    from .core import read_runs as implementation
    return implementation(data_dir)


def read_snapshot(data_dir, run_id=None):
    from .core import read_snapshot as implementation
    return implementation(data_dir, run_id)


class RequestError(ValueError):
    """A rejected public request, rather than a core data/validation failure."""


def decimal_json(value):
    if isinstance(value, Decimal) and value.is_finite():
        return format(value, 'f')
    raise TypeError('Unsupported JSON value')


class MboHandler(BaseHTTPRequestHandler):
    server_version = 'AssetHubMBO'
    sys_version = ''

    def __getattr__(self, name):
        # BaseHTTPRequestHandler otherwise answers unknown verbs with HTML/501.
        if name.startswith('do_'):
            return self.not_allowed
        raise AttributeError(name)

    def log_message(self, *_):
        # In particular, do not log arbitrary request targets or query strings.
        pass

    def _headers(self, status, mime, length, *, csp=API_CSP, extra=None):
        self.send_response(status)
        if mime:
            self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(length))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', csp)
        self.send_header('X-Request-ID', self.request_id)
        for name, value in (extra or {}).items():
            self.send_header(name, value)
        self.end_headers()

    def _json(self, status, payload, *, head=False, extra=None):
        body = json.dumps(payload, ensure_ascii=False, allow_nan=False,
                          default=decimal_json, separators=(',', ':')).encode('utf-8')
        self._headers(status, 'application/json; charset=utf-8', len(body), extra=extra)
        if not head:
            self.wfile.write(body)

    def _error(self, status, code, message, *, head=False, extra=None):
        self._json(status, {
            'error': {'code': code, 'message': message, 'retryable': status == 503},
            'request_id': self.request_id,
        }, head=head, extra=extra)

    def send_error(self, code, message=None, explain=None):
        # Protocol/parser errors must not echo untrusted targets or HTML errors.
        self.request_id = uuid.uuid4().hex
        self.close_connection = True
        self._error(code, 'invalid_request', 'リクエストを処理できません。',
                    head=getattr(self, 'command', '') == 'HEAD')

    def _authorized(self, *, head=False):
        hosts = self.headers.get_all('Host', [])
        allowed_hosts = {f'127.0.0.1:{self.server.server_port}',
                         f'localhost:{self.server.server_port}'}
        if len(hosts) != 1 or hosts[0].lower() not in allowed_hosts:
            self._error(403, 'forbidden', 'この接続元からは利用できません。', head=head)
            return False
        host = hosts[0].lower()
        origins = self.headers.get_all('Origin', [])
        sites = self.headers.get_all('Sec-Fetch-Site', [])
        if (len(origins) > 1 or (origins and origins[0].lower() != f'http://{host}')
                or len(sites) > 1 or (sites and sites[0] not in {'same-origin', 'none'})):
            self._error(403, 'forbidden', 'この接続元からは利用できません。', head=head)
            return False
        return True

    def _target(self):
        if (len(self.path) > 4096 or not self.path.startswith('/')
                or self.path.startswith('//') or '#' in self.path):
            raise RequestError()
        target = urlsplit(self.path)
        if target.scheme or target.netloc:
            raise RequestError()
        try:
            pairs = parse_qsl(target.query, keep_blank_values=True,
                              errors='strict', max_num_fields=12)
        except (ValueError, UnicodeError):
            raise RequestError() from None
        if len({key for key, _ in pairs}) != len(pairs):
            raise RequestError()
        return target.path, dict(pairs)

    @staticmethod
    def _query(query, allowed):
        if set(query) - set(allowed):
            raise RequestError()

    def _api(self, path, query):
        from ..mbo_dashboard import QueryError, query_response
        try:
            return query_response(
                path, query,
                status_reader=lambda: read_status(self.server.data_dir),
                runs_reader=lambda: read_runs(self.server.data_dir),
                snapshot_reader=lambda run_id: read_snapshot(self.server.data_dir, run_id))
        except QueryError:
            raise RequestError() from None

    def _static(self, path, *, head=False):
        asset = ASSETS.get(path)
        if asset is None:
            raise FileNotFoundError()
        filename, mime = asset
        file = self.server.web_dir / filename
        # Every filename is fixed above; never turn the request into a filesystem path.
        if file.is_symlink():
            raise FileNotFoundError()
        flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)
        descriptor = os.open(file, flags)
        with os.fdopen(descriptor, 'rb') as source:
            info = os.fstat(source.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_STATIC_BYTES:
                raise FileNotFoundError()
            body = source.read(MAX_STATIC_BYTES + 1)
        if len(body) > MAX_STATIC_BYTES:
            raise FileNotFoundError()
        self._headers(200, mime, len(body), csp=MBO_CSP)
        if not head:
            self.wfile.write(body)

    def _serve(self, *, head=False):
        self.request_id = uuid.uuid4().hex
        try:
            if not self._authorized(head=head):
                return
            path, query = self._target()
            if path.startswith('/api/'):
                self._json(200, self._api(path, query), head=head)
            else:
                self._query(query, ())
                self._static(path, head=head)
        except RequestError:
            self._error(400, 'invalid_request', '指定された条件を確認してください。', head=head)
        except FileNotFoundError:
            self._error(404, 'not_found', '対象のデータがありません。', head=head)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            self._error(503, 'unavailable', 'データを読み込めませんでした。', head=head)

    def do_GET(self):
        self._serve()

    def do_HEAD(self):
        self._serve(head=True)

    def not_allowed(self):
        self.request_id = uuid.uuid4().hex
        if self._authorized():
            self._error(405, 'method_not_allowed', '読み取り専用です。',
                        extra={'Allow': 'GET, HEAD'})

    do_POST = do_PUT = do_PATCH = do_DELETE = do_OPTIONS = do_TRACE = do_CONNECT = not_allowed


class MboServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, server_address=('127.0.0.1', 4331), handler_class=MboHandler,
                 *, data_dir=DEFAULT_DATA_DIR, web_dir=ROOT / 'web', bind_and_activate=True):
        if 'K_SERVICE' in os.environ:
            raise RuntimeError('MBO local mode cannot run in Cloud.')
        host, port = server_address
        if host != '127.0.0.1' or isinstance(port, bool) or not isinstance(port, int) or not 0 <= port <= 65535:
            raise ValueError('MBO requires an IPv4 loopback address and valid port.')
        self.data_dir = Path(data_dir)
        self.web_dir = Path(web_dir)
        super().__init__((host, port), handler_class, bind_and_activate=bind_and_activate)

    def server_bind(self):
        # HTTPServer's default getfqdn() is unnecessary: do not consult DNS.
        TCPServer.server_bind(self)
        self.server_name, self.server_port = self.server_address

    def handle_error(self, request, client_address):
        # Do not emit request targets, internal stack traces, or local paths.
        pass


def serve(port=4331, data_dir=DEFAULT_DATA_DIR):
    """Serve local MBO DTOs without initializing storage or external clients."""
    with MboServer(('127.0.0.1', port), data_dir=data_dir) as server:
        print(f'MBO local: http://127.0.0.1:{server.server_port}/', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
