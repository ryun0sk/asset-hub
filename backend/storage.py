"""Single JSON documents with optimistic concurrency (GCS generation match)."""
import json
import os
import threading
from pathlib import Path
from urllib.parse import quote


class Conflict(Exception):
    pass


class LocalDocument:
    """Development only; atomic replacement and a lock shared by every request."""
    def __init__(self, path):
        self.path = Path(path)
        self.lock = threading.RLock()

    def read(self):
        with self.lock:
            if not self.path.exists():
                return {}, 0
            value = json.loads(self.path.read_text())
            return value, value.get('revision', 0)

    def write(self, value, generation):
        with self.lock:
            if self.read()[1] != generation:
                raise Conflict()
            value = dict(value, revision=generation + 1)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temp = self.path.with_suffix('.tmp')
            temp.write_text(json.dumps(value, ensure_ascii=False))
            os.replace(temp, self.path)


class GCSDocument:
    def __init__(self, bucket, name, writable=False):
        import google.auth
        from google.auth.transport.requests import AuthorizedSession
        scope = 'read_write' if writable else 'read_only'
        credentials, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/devstorage.' + scope])
        self.session = AuthorizedSession(credentials)
        self.bucket = bucket
        self.name = name

    def read(self):
        url = f'https://storage.googleapis.com/storage/v1/b/{self.bucket}/o/{quote(self.name, safe="")}'
        response = self.session.get(url, params={'alt': 'media'}, timeout=20)
        if response.status_code == 404:
            return {}, 0
        response.raise_for_status()
        # Fail closed if GCS does not return the generation of these exact bytes.
        return response.json(), int(response.headers['x-goog-generation'])

    def write(self, value, generation):
        response = self.session.post(
            f'https://storage.googleapis.com/upload/storage/v1/b/{self.bucket}/o',
            params={'uploadType': 'media', 'name': self.name, 'ifGenerationMatch': generation},
            data=json.dumps(value, ensure_ascii=False).encode(),
            headers={'Content-Type': 'application/json'}, timeout=20)
        if response.status_code == 412:
            raise Conflict()
        response.raise_for_status()
