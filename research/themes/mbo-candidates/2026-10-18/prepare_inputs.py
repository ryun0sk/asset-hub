"""Create reviewed CSVs from the saved research input; no network or DB writes."""
from pathlib import Path
import csv
import hashlib
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from backend.mbo.core import HEADERS


def main():
    source = json.loads(Path(__file__).with_name('research-inputs.json').read_text())
    inbox = ROOT / 'data/private/mbo-inbox/2026-10-18'
    inbox.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(inbox, 0o700)
    own = inbox / next(d['file'] for d in source['documents'] if d['source_id'].startswith('valuation-assumptions-'))
    content = source['assumption_document_text'].encode()
    if own.exists() and own.read_bytes() != content:
        raise ValueError('独自仮定の原本は置換せず、新しい版を作成してください')
    own.write_bytes(content)
    os.chmod(own, 0o600)
    for document in source['documents']:
        path = inbox / document['file']
        if not path.is_file() or path.is_symlink():
            raise ValueError('原本が不足: ' + document['file'])
        if hashlib.sha256(path.read_bytes()).hexdigest() != document['sha256']:
            raise ValueError('原本ハッシュ不一致: ' + document['file'])
    for kind, headers in HEADERS.items():
        with (inbox / (kind + '.csv')).open('w', encoding='utf-8', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=headers, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(source[kind])
        os.chmod(inbox / (kind + '.csv'), 0o600)
    print(json.dumps({'status': 'prepared', 'rows': {k: len(source[k]) for k in HEADERS}}, ensure_ascii=False))


if __name__ == '__main__':
    main()
