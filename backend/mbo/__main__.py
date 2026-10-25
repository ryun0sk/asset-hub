"""python3 -m backend.mbo --help (standard library only, always offline)."""
from datetime import date, timedelta
from pathlib import Path
import argparse
import csv
import json
import sys

from . import core


def write_csv(path, rows, headers):
    with Path(path).open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def templates(directory):
    directory = core.private_dir(directory)
    if list(directory.iterdir()):
        raise ValueError('テンプレート出力先には空のフォルダを指定してください')
    for kind, headers in core.HEADERS.items():
        write_csv(directory / (kind + '.csv'), [], headers)
        (directory / (kind + '.csv')).chmod(0o600)
    core.atomic(directory / 'README.txt', (
        'MBO週次取込。docs/mbo-weekly.md の列定義を参照。\n'
        '金額は百万円ではなく円、比率は0〜1、株数は自己株控除後の希薄化株数。\n'
        'documents.csvのfileは同フォルダ内の原本の相対パス。原本なしはpending。\n'
        'verifiedは人が原本と数値・定義・株式分割基準を照合したときだけ指定。\n'
        '不要なCSVはヘッダーだけのままでよい。scenarios.csvは独自仮定。\n'
        'このシステムはファイルから数値を自動読解しません。\n'
    ).encode('utf-8'))
    return {'status': 'templates_created', 'csv_files': len(core.HEADERS)}


def demo(data_dir):
    """Fictional isolated portfolio and two runs exercise the full offline path."""
    base = Path(data_dir)
    if (base / 'state.sqlite').exists():
        raise ValueError('デモ保存先は使用済みです。既存履歴は保持します。別の--data-dirを指定してください')
    today = core.day(core.now())
    earlier = today - timedelta(days=7)
    period = date(today.year if today.month >= 6 else today.year - 1, 3, 31)
    start = date(period.year - 1, 4, 1)
    published = period + timedelta(days=45)
    bundle = core.private_dir(base / 'demo-input-initial')
    core.atomic(bundle / 'fictional-source.txt', '架空データ。実在企業・株価・MBO情報ではありません。\n'.encode())
    documents = [{'source_id': 'demo-facts', 'file': 'fictional-source.txt', 'title': '架空企業の検証用決算・株主情報',
                  'source_url': '', 'published_at': published.isoformat()},
                 {'source_id': 'demo-price-initial', 'file': 'fictional-source.txt', 'title': '架空の前週株価',
                  'source_url': '', 'published_at': earlier.isoformat()}]
    securities, facts, prices, scenarios = [], [], [], []
    for i, name in enumerate(('架空・青葉製作所', '架空・白波サービス', '架空・山吹物流', '架空・若草機器'), 1):
        code = f'DEMO{i}'
        securities.append({'code': code, 'name': name, 'exchange': 'DEMO', 'security_type': 'common_stock',
                           'as_of': earlier.isoformat(), 'source_id': 'demo-facts', 'included': 'true'})
        values = {'ebit': '1200000000', 'depreciation': '200000000', 'capex': '250000000', 'delta_nwc': '50000000',
                  'excess_cash': '2000000000', 'debt': '1000000000', 'noncontrolling_interest': '0',
                  'shares_diluted': '10000000', 'owner_ratio': '.42' if i != 4 else '.08', 'operating_cfo': '1300000000'}
        for metric, value in values.items():
            facts.append({'code': code, 'exchange': 'DEMO', 'metric': metric, 'value': value,
                          'unit': 'JPY' if metric in core.MONEY else ('shares' if metric == 'shares_diluted' else 'ratio'),
                          'currency': 'JPY' if metric in core.MONEY else '', 'period_start': start.isoformat() if metric in core.FLOW else '',
                          'period_end': period.isoformat(), 'fact_kind': 'actual', 'consolidation': 'consolidated',
                          'share_basis': 'demo-post-split-1', 'public_at': published.isoformat(), 'source_id': 'demo-facts',
                          'locator': f'架空の検証用表/{metric}', 'quality_status': 'verified', 'missing_reason': ''})
        if i != 2:
            prices.append({'code': code, 'exchange': 'DEMO', 'value': str(550 + i * 50), 'currency': 'JPY',
                           'price_at': earlier.isoformat(), 'price_type': 'close', 'adjustment': 'unadjusted',
                           'share_basis': 'demo-post-split-1', 'public_at': earlier.isoformat(), 'source_id': 'demo-price-initial',
                           'locator': '架空の終値', 'quality_status': 'verified'})
        for name, growth, wacc in [('bear', '-.02', '.11'), ('base', '.02', '.09'), ('bull', '.04', '.08')]:
            scenarios.append({'code': code, 'exchange': 'DEMO', 'name': name, 'as_of': earlier.isoformat(),
                              'horizon_years': '5', 'revenue_growth': growth, 'tax_rate': '.3', 'wacc': wacc,
                              'terminal_growth': '0', 'entry_debt_multiple': '3', 'debt_interest': '.04',
                              'debt_amortization': '.1', 'exit_multiple': '6', 'target_irr': '.2', 'fee_rate': '.02',
                              'rollover_ratio': '.1', 'minimum_cash': '100000000', 'note': '検証用の独自仮定。融資条件・買付予想ではない'})
    for kind, rows in [('documents', documents), ('securities', securities), ('facts', facts), ('prices', prices), ('scenarios', scenarios)]:
        write_csv(bundle / (kind + '.csv'), rows, core.HEADERS[kind])
        (bundle / (kind + '.csv')).chmod(0o600)
    core.import_bundle(bundle, base, demo=True)
    # Both demo runs are created now. Do not fabricate a past observation date.
    previous = core.build(today.isoformat(), base)
    update = core.private_dir(base / 'demo-input-update')
    core.atomic(update / 'fictional-update.txt', '架空の価格更新・MBO公表イベント。実在企業ではありません。\n'.encode())
    write_csv(update / 'documents.csv', [{'source_id': 'demo-update', 'file': 'fictional-update.txt',
              'title': '架空の当週価格・取引公表', 'source_url': '', 'published_at': today.isoformat()}], core.HEADERS['documents'])
    for row in prices:
        row.update(value=str(int(row['value']) + 30), price_at=today.isoformat(), public_at=today.isoformat(), source_id='demo-update')
    write_csv(update / 'prices.csv', prices, core.HEADERS['prices'])
    write_csv(update / 'events.csv', [{'code': 'DEMO3', 'exchange': 'DEMO', 'event_type': 'mbo', 'status': 'announced',
              'announced_at': today.isoformat(), 'public_at': today.isoformat(), 'source_id': 'demo-update', 'locator': '架空の取引公表'}], core.HEADERS['events'])
    for path in update.glob('*.csv'):
        path.chmod(0o600)
    core.import_bundle(update, base, demo=True)
    current = core.build(today.isoformat(), base)
    return {'status': 'demo_created', 'fictional': True, 'previous': previous, 'current': current,
            'open': 'python3 -m backend.server --mode mbo-local --mbo-data-dir ' + str(base)}


def main(argv=None):
    parser = argparse.ArgumentParser(description='無料データを持ち込むMBO週次調査（通信なし）')
    parser.add_argument('--data-dir', type=Path, default=core.DEFAULT_DATA_DIR, help='私的データ保存先')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('init', help='空のDBを初期化')
    sub.add_parser('status', help='最後の成功・更新状態')
    sub.add_parser('runs', help='保存した週次履歴')
    audit = sub.add_parser('records', help='入力のレコードIDと履歴を確認（訂正用）')
    audit.add_argument('--kind', choices=list(core.CORRECTABLE), required=True)
    audit.add_argument('--code', required=True)
    temp = sub.add_parser('templates', help='空のCSVテンプレートを作成')
    temp.add_argument('directory', type=Path)
    for name in ('import', 'weekly'):
        child = sub.add_parser(name, help='CSV一括取込' if name == 'import' else 'CSV取込と週次計算・発行を連続実行')
        child.add_argument('directory', type=Path)
        child.add_argument('--dry-run', action='store_true', help='検証のみ（DBへ保存しない）')
        child.add_argument('--encoding', default='utf-8-sig', choices=['utf-8-sig', 'utf-8', 'cp932'])
        if name == 'weekly':
            child.add_argument('--as-of', default=core.day(core.now()).isoformat())
    child = sub.add_parser('build', help='取込済みデータを計算して週次結果を保存')
    child.add_argument('--as-of', default=core.day(core.now()).isoformat())
    sub.add_parser('demo', help='別保存先に架空4社・2回の更新比較を作成。実企業の調査ではない')
    child = sub.add_parser('evidence', help='保存した原本の場所をMac内で確認')
    child.add_argument('action', choices=['locate'])
    child.add_argument('--document-id', required=True)
    child = sub.add_parser('backup', help='DBと原本・履歴のローカルバックアップ')
    child.add_argument('destination', type=Path)
    child = sub.add_parser('export-dashboard', help='Asset Hub閲覧用の週次結果だけを書き出す（アップロードなし）')
    child.add_argument('output', type=Path)
    child.add_argument('--keep-runs', type=int, default=52)
    child.add_argument('--allow-demo', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.command == 'init':
            result = core.init(args.data_dir)
        elif args.command == 'status':
            result = core.read_status(args.data_dir)
        elif args.command == 'runs':
            result = core.read_runs(args.data_dir)
        elif args.command == 'records':
            conn = core.connection(args.data_dir)
            try:
                result = {'kind': args.kind, 'records': [row for row in core.records(conn, args.kind) if row['code'] == args.code]}
            finally:
                conn.close()
        elif args.command == 'templates':
            result = templates(args.directory)
        elif args.command in ('import', 'weekly'):
            result = core.import_bundle(args.directory, args.data_dir, dry_run=args.dry_run, encoding=args.encoding)
            if args.command == 'weekly' and not args.dry_run:
                result = {'import': result, 'run': core.build(args.as_of, args.data_dir)}
        elif args.command == 'build':
            result = core.build(args.as_of, args.data_dir)
        elif args.command == 'demo':
            target = args.data_dir if args.data_dir != core.DEFAULT_DATA_DIR else core.DEFAULT_DATA_DIR.with_name('mbo-demo')
            result = demo(target)
        elif args.command == 'evidence':
            result = {'path': core.locate(args.document_id, args.data_dir)}
        elif args.command == 'backup':
            result = core.backup(args.destination, args.data_dir)
        elif args.command == 'export-dashboard':
            from .publish import export_dashboard
            result = export_dashboard(args.data_dir, args.output, args.keep_runs, args.allow_demo)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    except (ValueError, OSError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
