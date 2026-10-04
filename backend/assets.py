"""Weekly asset snapshots recorded by hand. HTTP requests only read a prebuilt state document.

Sources live in data/private/assets/ (git-ignored): accounts.json and snapshots/YYYY-MM-DD.json.
`python3 -m backend.assets build` validates them and writes the local state document that the
local server reads; `push` uploads the same state to gs://<ASSET_STATE_BUCKET>/assets/state.json,
which Cloud Run serves at /api/assets. Balances never enter git, the image or the HTTP write path
(there is none). Aggregation happens in the browser, as it does for costs.
"""
import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from .paths import ROOT
from .storage import Conflict, GCSDocument, LocalDocument

STATE_OBJECT = 'assets/state.json'
DEFAULT_DIR = 'data/private/assets'
CLASSES = ('stock', 'fund', 'crypto', 'cash', 'private', 'bond', 'other')
CLASS_LABELS = {'stock': '個別株', 'fund': '投資信託・ETF', 'crypto': '仮想通貨', 'cash': '現金・預金',
                'private': '未上場株', 'bond': '債券', 'other': 'その他'}
# Values that do not move week to week may be copied from the previous snapshot (template marks them).
CARRY_FORWARD_CLASSES = ('private',)
MARKETS = ('JP', 'US', 'other')
ID_PATTERN = re.compile(r'^[a-z0-9][a-z0-9-]{1,39}$')
SYMBOL_PATTERN = re.compile(r'^[A-Za-z0-9._-]{1,32}$')
ACCOUNT_CURRENCY_PATTERN = re.compile(r'^[A-Z]{3}$')
POSITION_CURRENCY_PATTERN = re.compile(r'^[A-Z0-9]{3,10}$')
DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')
JST = ZoneInfo('Asia/Tokyo')
WEEKDAYS = ('月', '火', '水', '木', '金', '土', '日')
POSITION_KEYS = ('account', 'class', 'market', 'symbol', 'name', 'quantity', 'valueJpy', 'costJpy',
                 'currency', 'nativeAmount', 'carryForward')


def assets_dir():
    path = Path(os.environ.get('ASSET_ASSETS_DIR') or DEFAULT_DIR)
    return path if path.is_absolute() else ROOT / path


def local_state_path():
    configured = os.environ.get('ASSET_ASSETS_LOCAL_PATH')
    if not configured:
        return assets_dir() / 'state.json'
    path = Path(configured)
    return path if path.is_absolute() else ROOT / path


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _text(value):
    return isinstance(value, str) and value.strip() != ''


def _iso_date(value):
    if not isinstance(value, str) or not DATE_PATTERN.fullmatch(value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def validate_accounts(data, filename='accounts.json'):
    """Return {id: account} or raise ValueError naming the offending field."""
    if not isinstance(data, dict):
        raise ValueError(f'{filename}: オブジェクトではありません')
    if 'version' in data and data['version'] != 1:
        raise ValueError(f'{filename}: version は 1 にしてください')
    rows = data.get('accounts')
    if not isinstance(rows, list) or not rows:
        raise ValueError(f'{filename}: accounts に口座を1件以上並べてください')
    accounts = {}
    for index, row in enumerate(rows):
        where = f'{filename}: accounts[{index}]'
        if not isinstance(row, dict):
            raise ValueError(f'{where} がオブジェクトではありません')
        identifier = row.get('id')
        if not isinstance(identifier, str) or not ID_PATTERN.fullmatch(identifier):
            raise ValueError(f'{where}.id は小文字英数字とハイフン（2〜40文字）にしてください')
        if identifier in accounts:
            raise ValueError(f'{where}.id "{identifier}" が重複しています')
        for key in ('institution', 'label'):
            if not _text(row.get(key)):
                raise ValueError(f'{where}.{key}（{identifier}）を入力してください')
        if row.get('defaultClass') not in CLASSES:
            raise ValueError(f'{where}.defaultClass（{identifier}）は {"/".join(CLASSES)} のいずれかにしてください')
        currency = row.get('currency')
        if not isinstance(currency, str) or not ACCOUNT_CURRENCY_PATTERN.fullmatch(currency):
            raise ValueError(f'{where}.currency（{identifier}）は JPY のような3文字の通貨コードにしてください')
        guide = row.get('readGuide')
        if guide is not None and not isinstance(guide, str):
            raise ValueError(f'{where}.readGuide（{identifier}）は文字列にしてください')
        account = dict(id=identifier, institution=row['institution'].strip(), label=row['label'].strip(),
                       defaultClass=row['defaultClass'], currency=currency)
        if guide is not None:
            account['readGuide'] = guide
        accounts[identifier] = account
    return accounts


def _validate_position(row, index, accounts, filename):
    where = f'{filename}: positions[{index}]'
    if not isinstance(row, dict):
        raise ValueError(f'{where} がオブジェクトではありません')
    account = row.get('account')
    if account not in accounts:
        raise ValueError(f'{where}.account "{account}" は accounts.json にありません')
    cls = row.get('class')
    if cls not in CLASSES:
        raise ValueError(f'{where}.class（{account}）は {"/".join(CLASSES)} のいずれかにしてください')
    symbol = row.get('symbol')
    if not isinstance(symbol, str) or not SYMBOL_PATTERN.fullmatch(symbol):
        raise ValueError(f'{where}.symbol（{account}）は英数字・ピリオド・ハイフン（1〜32文字）にしてください')
    label = f'{account}/{symbol}'
    if not _text(row.get('name')):
        raise ValueError(f'{where}.name（{label}）を入力してください')
    position = {'account': account, 'class': cls, 'symbol': symbol, 'name': row['name'].strip()}
    market = row.get('market')
    if market is not None:
        if market not in MARKETS:
            raise ValueError(f'{where}.market（{label}）は {"/".join(MARKETS)} のいずれかにしてください')
        position['market'] = market
    value = row.get('valueJpy')
    if value is None:
        raise ValueError(f'{where}.valueJpy（{label}）が未入力です。画面の円換算評価額を記録してください')
    if not _is_int(value) or value < 0:
        raise ValueError(f'{where}.valueJpy（{label}）は 0 以上の整数（円）にしてください')
    position['valueJpy'] = value
    cost = row.get('costJpy')
    if cost is not None:
        if not _is_int(cost) or cost < 0:
            raise ValueError(f'{where}.costJpy（{label}）は 0 以上の整数（円）にしてください')
        position['costJpy'] = cost
    quantity = row.get('quantity')
    if quantity is not None:
        if not _is_number(quantity) or quantity <= 0:
            raise ValueError(f'{where}.quantity（{label}）は 0 より大きい数にしてください')
        position['quantity'] = quantity
    currency = row.get('currency')
    if currency is not None:
        if not isinstance(currency, str) or not POSITION_CURRENCY_PATTERN.fullmatch(currency):
            raise ValueError(f'{where}.currency（{label}）は USD や BTC のような大文字コードにしてください')
        position['currency'] = currency
    native = row.get('nativeAmount')
    if native is not None:
        if not _is_number(native):
            raise ValueError(f'{where}.nativeAmount（{label}）は数値にしてください')
        position['nativeAmount'] = native
    carry = row.get('carryForward')
    if carry is not None:
        if not isinstance(carry, bool):
            raise ValueError(f'{where}.carryForward（{label}）は true/false にしてください')
        if cls not in CARRY_FORWARD_CLASSES:
            raise ValueError(f'{where}.carryForward（{label}）は {"/".join(CARRY_FORWARD_CLASSES)} クラスでのみ使えます。'
                             '他のクラスは毎週画面から読み取ってください')
        if carry:
            position['carryForward'] = True
    return position


def validate_snapshot(data, accounts, filename_date=None, today=None):
    """Return (snapshot, warnings) or raise ValueError. Unknown keys are dropped."""
    filename = f'snapshots/{filename_date}.json' if filename_date else 'snapshot'
    if not isinstance(data, dict):
        raise ValueError(f'{filename}: オブジェクトではありません')
    if data.get('version') != 1 or isinstance(data.get('version'), bool):
        raise ValueError(f'{filename}: version は 1 にしてください')
    day = _iso_date(data.get('date'))
    if day is None:
        raise ValueError(f'{filename}: date は YYYY-MM-DD 形式にしてください')
    if filename_date is not None and day.isoformat() != filename_date:
        raise ValueError(f'{filename}: date "{day.isoformat()}" がファイル名と一致しません')
    today = today or datetime.now(JST).date()
    if day > today:
        raise ValueError(f'{filename}: date "{day.isoformat()}" は未来の日付です')
    snapshot = dict(version=1, date=day.isoformat())
    recorded = data.get('recordedAt')
    if recorded is not None:
        try:
            if not isinstance(recorded, str):
                raise ValueError
            datetime.fromisoformat(recorded.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError(f'{filename}: recordedAt は ISO 8601 の日時にしてください') from None
        snapshot['recordedAt'] = recorded
    source = data.get('source')
    if source is not None:
        if not isinstance(source, str):
            raise ValueError(f'{filename}: source は文字列にしてください')
        snapshot['source'] = source
    rows = data.get('positions')
    if not isinstance(rows, list) or not rows:
        raise ValueError(f'{filename}: positions に保有を1件以上並べてください')
    positions, seen = [], set()
    for index, row in enumerate(rows):
        position = _validate_position(row, index, accounts, filename)
        key = (position['account'], position['class'], position['symbol'])
        if key in seen:
            raise ValueError(f'{filename}: positions[{index}] {"/".join(key)} が重複しています')
        seen.add(key)
        positions.append(position)
    if sum(p['valueJpy'] for p in positions) <= 0:
        raise ValueError(f'{filename}: 評価額の合計が 0 です')
    snapshot['positions'] = positions
    notes = data.get('notes')
    if notes is None:
        notes = []
    if not isinstance(notes, list) or not all(isinstance(note, str) for note in notes):
        raise ValueError(f'{filename}: notes は文字列の配列にしてください')
    snapshot['notes'] = list(notes)
    warnings = []
    if day.weekday() < 5:
        warnings.append(f'{filename}: {day.isoformat()} は土日ではありません（{WEEKDAYS[day.weekday()]}曜日）')
    return snapshot, warnings


def _compact(position):
    return {key: position[key] for key in POSITION_KEYS if position.get(key) is not None}


def build_state(accounts, snapshots, now=None):
    """Combine validated sources into the document the dashboard reads."""
    now = now or datetime.now(timezone.utc)
    ordered = sorted(snapshots, key=lambda s: s['date'])
    dates = [s['date'] for s in ordered]
    for index in range(1, len(dates)):
        if dates[index] == dates[index - 1]:
            raise ValueError(f'snapshots: 日付 {dates[index]} が重複しています')
    rows = list(accounts.values()) if isinstance(accounts, dict) else list(accounts)
    series = []
    for snapshot in ordered:
        entry = dict(date=snapshot['date'])
        if snapshot.get('recordedAt'):
            entry['recordedAt'] = snapshot['recordedAt']
        entry['positions'] = [_compact(p) for p in snapshot['positions']]
        if snapshot.get('notes'):
            entry['notes'] = list(snapshot['notes'])
        series.append(entry)
    return dict(version=1, builtAt=now.isoformat(), accounts=rows, snapshots=series,
                latestDate=dates[-1] if dates else None)


def template(day, accounts, previous_snapshot=None):
    """Positions to fill in for one weekend. Null values must be read from the screen (validate rejects them)."""
    if _iso_date(day) is None:
        raise ValueError(f'template: date "{day}" は YYYY-MM-DD 形式にしてください')
    positions = []
    if previous_snapshot:
        for previous in previous_snapshot['positions']:
            position = _compact(previous)
            position.pop('carryForward', None)
            if position['class'] in CARRY_FORWARD_CLASSES:
                position['carryForward'] = True
            else:
                position['valueJpy'] = None
                for key in ('quantity', 'nativeAmount'):
                    if key in position:
                        position[key] = None
            positions.append(position)
    else:
        rows = accounts.values() if isinstance(accounts, dict) else accounts
        for account in rows:
            cash = account['defaultClass'] == 'cash'
            positions.append({'account': account['id'], 'class': account['defaultClass'],
                              'symbol': account['currency'] if cash else None,
                              'name': account['label'] if cash else None,
                              'quantity': None, 'valueJpy': None})
    return dict(version=1, date=day, source='screenshot', positions=positions, notes=[])


def asset_document(bucket=None, writable=False, session=None):
    if bucket:
        return GCSDocument(bucket, STATE_OBJECT, writable=writable, session=session)
    return LocalDocument(local_state_path())


def asset_payload(document):
    state, _ = document.read()
    inner = state.get('state')
    return dict(state=inner, status=dict(status='ok' if inner else 'not_configured', pushedAt=state.get('pushedAt')))


def _read_json(path, label):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        raise ValueError(f'{label} がありません（{path}）') from None
    except ValueError as exc:
        raise ValueError(f'{label} のJSONが読めません: {exc}') from None


def load_sources(directory, today=None, skip_dates=()):
    """Read and validate accounts.json and snapshots/*.json. Returns (accounts, snapshots, warnings).

    `skip_dates`: snapshot files to leave out, such as the draft `template` is about to (re)write."""
    directory = Path(directory)
    accounts = validate_accounts(_read_json(directory / 'accounts.json', 'accounts.json'))
    snapshots, warnings = [], []
    folder = directory / 'snapshots'
    for path in sorted(folder.glob('*.json')) if folder.is_dir() else []:
        if path.name.startswith('.') or path.stem in skip_dates:
            continue
        if _iso_date(path.stem) is None:
            raise ValueError(f'snapshots/{path.name}: ファイル名は YYYY-MM-DD.json にしてください')
        snapshot, notes = validate_snapshot(_read_json(path, f'snapshots/{path.name}'), accounts, path.stem, today)
        snapshots.append(snapshot)
        warnings.extend(notes)
    return accounts, snapshots, warnings


def mirror(directory, target, state_path=None):
    """Copy the sources and the built state to another folder (for example under iCloud)."""
    directory, target = Path(directory), Path(target)
    sources = {'accounts.json': directory / 'accounts.json',
               'state.json': Path(state_path) if state_path else directory / 'state.json'}
    for path in sorted((directory / 'snapshots').glob('*.json')):
        sources[f'snapshots/{path.name}'] = path
    copied = []
    for relative, source in sources.items():
        if source.is_file():
            (target / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target / relative)
            copied.append(relative)
    return copied


def push(document, state, now=None):
    """Replace the remote state atomically; one retry if another writer got there first."""
    now = now or datetime.now(timezone.utc)
    pushed = now.isoformat()
    for attempt in range(2):
        _, generation = document.read()
        try:
            document.write(dict(state=state, pushedAt=pushed), generation)
            return pushed
        except Conflict:
            if attempt:
                raise


def gcloud_session(account=None):
    """A requests session carrying the operator's gcloud access token (same as infra/setup_costs.py)."""
    import requests
    command = ['gcloud', 'auth', 'print-access-token']
    if account:
        command.append('--account=' + account)
    token = subprocess.check_output(command, text=True).strip()
    if not token:
        raise ValueError('gcloud のアクセストークンを取得できませんでした')
    session = requests.Session()
    session.headers['Authorization'] = 'Bearer ' + token
    return session


def _push_target(bucket, account):
    """Bucket: --bucket > ASSET_STATE_BUCKET > infra config. Account: --account > infra config."""
    bucket = bucket or os.environ.get('ASSET_STATE_BUCKET') or None
    if bucket and account:
        return bucket, account
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from infra.common import load_config, names
    config = load_config()
    return bucket or names(config)['state_bucket'], account or config.get('account')


def _emit(payload):
    print(json.dumps(payload, ensure_ascii=False), flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(prog='python3 -m backend.assets', description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('validate', help='accounts.json と snapshots/*.json を検証する')
    commands.add_parser('build', help='検証して state.json（と ASSET_ASSETS_MIRROR）を書き出す')
    tmpl = commands.add_parser('template', help='前回分を基に今週のスナップショット雛形を作る')
    tmpl.add_argument('--date', required=True, help='YYYY-MM-DD（記録日）')
    tmpl.add_argument('--force', action='store_true', help='既存のファイルを上書きする')
    pusher = commands.add_parser('push', help='検証・build した state を GCS に書き込む')
    pusher.add_argument('--bucket', help='state バケット（既定: ASSET_STATE_BUCKET か infra/config.json から）')
    pusher.add_argument('--account', help='gcloud のアカウント（既定: infra/config.json の account）')
    args = parser.parse_args(argv)
    directory = assets_dir()
    now = datetime.now(timezone.utc)
    try:
        if args.command == 'template':
            if _iso_date(args.date) is None:
                raise ValueError(f'--date "{args.date}" は YYYY-MM-DD 形式にしてください')
            target = directory / 'snapshots' / f'{args.date}.json'
            if target.exists() and not args.force:
                raise ValueError(f'{target} は既にあります（上書きするには --force）')
            # The draft for this date is unfinished by definition; only earlier snapshots must validate.
            accounts, snapshots, warnings = load_sources(directory, skip_dates={args.date})
            for warning in warnings:
                print(warning, file=sys.stderr, flush=True)
            earlier = [s for s in snapshots if s['date'] < args.date]
            previous = max(earlier, key=lambda s: s['date']) if earlier else None
            draft = template(args.date, accounts, previous)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(draft, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            print(str(target), flush=True)
            _emit({'assetsTemplate': 'ok', 'date': args.date, 'basedOn': previous['date'] if previous else None,
                   'positions': len(draft['positions'])})
            return 0
        accounts, snapshots, warnings = load_sources(directory)
        for warning in warnings:
            print(warning, file=sys.stderr, flush=True)
        state = build_state(accounts, snapshots, now)
        if args.command == 'validate':
            _emit({'assetsValidate': 'ok', 'snapshots': len(snapshots), 'latestDate': state['latestDate'],
                   'warnings': len(warnings)})
            return 0
        if args.command == 'build':
            document = asset_document(None)
            _, generation = document.read()
            document.write(dict(state=state, pushedAt=None), generation)
            result = {'assetsBuild': 'ok', 'latestDate': state['latestDate'], 'snapshots': len(snapshots),
                      'path': str(document.path)}
            target = os.environ.get('ASSET_ASSETS_MIRROR')
            if target:
                result['mirrored'] = len(mirror(directory, Path(target) if Path(target).is_absolute() else ROOT / target,
                                                document.path))
            _emit(result)
            return 0
        bucket, account = _push_target(args.bucket, args.account)
        if not bucket:
            raise ValueError('push 先のバケットが分かりません（--bucket か ASSET_STATE_BUCKET）')
        document = asset_document(bucket, writable=True, session=gcloud_session(account))
        pushed = push(document, state, now)
        _emit({'assetsPush': 'ok', 'bucket': bucket, 'object': STATE_OBJECT, 'latestDate': state['latestDate'],
               'snapshots': len(snapshots), 'pushedAt': pushed})
        return 0
    except ValueError as exc:
        print(str(exc), file=sys.stderr, flush=True)
        return 1
    except Conflict:
        print('push: 同時に別の書き込みがあったため中止しました。再実行してください', file=sys.stderr, flush=True)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
