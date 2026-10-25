"""Export curated, frozen MBO dashboard JSON locally; no network or upload."""
from pathlib import Path
import json
import os
import stat
import tempfile

from ..mbo_dashboard import MAX_DOCUMENT_BYTES, sanitize_bundle
from . import core


def _destination(output, data_dir):
    path = core.reject_symlinks(output)
    base = core.reject_symlinks(data_dir)
    try:
        relative = path.relative_to(base)
    except ValueError:
        relative = None
    if relative is not None:
        if (not relative.parts or relative.parts[0] in {'raw', 'imports', 'runs', 'published'}
                or relative.parts[0].startswith('state.sqlite')
                or relative.parts[0] in {'last_attempt.json', '.writer.lock'}):
            raise ValueError('原本・DB・既存の実行履歴は出力先に指定できません。')
    if path.exists() and not stat.S_ISREG(path.stat().st_mode):
        raise ValueError('出力先には通常ファイルを指定してください。')
    return path


def _atomic_export(path, content, data_dir):
    # Only newly created directories receive owner-only permissions. Existing
    # unrelated parent directories are never chmodded by an export command.
    missing = []
    parent = path.parent
    while not parent.exists():
        missing.append(parent)
        parent = parent.parent
    for directory in reversed(missing):
        core.reject_symlinks(directory)
        directory.mkdir(mode=0o700, exist_ok=True)
    _destination(path, data_dir)
    descriptor, temporary = tempfile.mkstemp(prefix='.mbo-export-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as handle:
            os.fchmod(handle.fileno(), 0o600)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        _destination(path, data_dir)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def export_dashboard(data_dir, output, keep_runs=52, allow_demo=False):
    """Atomically save a sanitized bundle without changing source storage.

    The current success pointer is pinned before selecting its history, so an
    in-progress publication cannot silently replace the exported latest run.
    ``allow_demo=True`` is required whenever any selected snapshot is a demo.
    """
    if isinstance(keep_runs, bool) or not isinstance(keep_runs, int) or not 1 <= keep_runs <= 1000:
        raise ValueError('keep_runsは1〜1000の整数で指定してください。')
    if not isinstance(allow_demo, bool):
        raise ValueError('allow_demoは真偽値で指定してください。')
    output = _destination(output, data_dir)
    status = core.read_status(data_dir)
    runs = core.read_runs(data_dir)['items']
    latest = status.get('latest_success_run_id')
    if latest is None:
        if runs:
            raise RuntimeError('最新の成功結果が確定していません。入力状態を確認してください。')
        selected = []
    else:
        position = next((index for index, run in enumerate(runs) if run.get('run_id') == latest), None)
        if position is None:
            raise RuntimeError('最新の成功結果と実行履歴が一致しません。')
        selected = runs[position:position + keep_runs]
    snapshots = {run['run_id']: core.read_snapshot(data_dir, run['run_id']) for run in selected}
    bundle = sanitize_bundle({'schema_version': 1, 'runs': selected, 'snapshots': snapshots,
                              'latest_run_id': latest, 'last_attempt': status.get('last_attempt')})
    if not allow_demo and any(item.get('demo') is not False
                              for item in [*bundle['runs'], *bundle['snapshots'].values()]):
        raise ValueError('デモ結果の書き出しには--allow-demoを明示してください。')
    content = json.dumps(bundle, ensure_ascii=False, allow_nan=False, sort_keys=True, indent=2).encode('utf-8')
    if len(content) > MAX_DOCUMENT_BYTES:
        raise ValueError('出力が32MiBを超えました。keep_runsを減らしてください。')
    _atomic_export(output, content, data_dir)
    return {'status': 'exported', 'runs': len(bundle['runs']), 'latest_run_id': latest}
