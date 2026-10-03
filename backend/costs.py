"""Project-scoped billing snapshots. HTTP requests never query BigQuery.

The Cloud Run Job `asset-cost-sync` runs `python -m backend.costs`; it reads the
billing export (filtered to this project) and saves one JSON object to
gs://<ASSET_STATE_BUCKET>/costs/state.json. The dashboard only reads that object.
"""
import json
import math
import os
import re
import time
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

from .paths import ROOT
from .storage import Conflict, GCSDocument, LocalDocument

STATE_OBJECT = 'costs/state.json'
REFRESH_SECONDS = 3600  # Suppress immediate retries; the scheduler supplies the daily cadence.
MAXIMUM_BYTES_BILLED = '100000000'
TABLE_PATTERN = re.compile(r'^[a-z][a-z0-9-]{4,61}[a-z0-9]\.[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*$')
PROJECT_PATTERN = re.compile(r'^[a-z][a-z0-9-]{4,28}[a-z0-9]$')


def project_id():
    project = os.environ.get('ASSET_PROJECT_ID', '')
    return project if PROJECT_PATTERN.fullmatch(project) else None


def cost_window(now):
    today = now.astimezone(ZoneInfo('Asia/Tokyo'))
    month = today.year * 12 + today.month - 1
    def first(offset):
        year, index = divmod(month + offset, 12)
        return date(year, index + 1, 1).isoformat()
    return {'start': first(-5), 'end': first(1)}


def cost_query(table):
    if not TABLE_PATTERN.fullmatch(table):
        raise ValueError('Invalid billing table')
    return f"""SELECT DATE(usage_start_time, 'Asia/Tokyo') AS date,
 service.id AS service_id, service.description AS service, currency,
 SUM(CAST(cost AS NUMERIC)) AS gross,
 SUM(IFNULL((SELECT SUM(CAST(c.amount AS NUMERIC)) FROM UNNEST(credits) AS c), 0)) AS credits,
 MAX(export_time) AS exported_at
 FROM `{table}`
 WHERE project.id = @project
 AND usage_start_time >= TIMESTAMP(@start, 'Asia/Tokyo')
 AND usage_start_time < TIMESTAMP(@end, 'Asia/Tokyo')
 AND (_PARTITIONTIME >= TIMESTAMP_SUB(TIMESTAMP(@start, 'Asia/Tokyo'), INTERVAL 2 DAY) OR _PARTITIONTIME IS NULL)
 GROUP BY date, service_id, service, currency ORDER BY date, service_id"""


def parse_rows(rows, window, fetched_at, project):
    records = []
    for row in rows:
        day = row['date']
        if date.fromisoformat(day).isoformat() != day or not window['start'] <= day < window['end']:
            raise ValueError('Invalid cost date')
        if not re.fullmatch('[A-Z]{3}', row['currency']) or not row['service_id']:
            raise ValueError('Invalid billing identity')
        amounts = [Decimal(row[key]) for key in ('gross', 'credits')]
        if not all(v.is_finite() and math.isfinite(float(v)) for v in amounts):
            raise ValueError('Invalid cost amount')
        gross, credits = amounts
        exported = str(row['exported_at'])
        try:
            stamp = datetime.fromtimestamp(float(exported), timezone.utc)
        except ValueError:
            stamp = datetime.fromisoformat(exported.replace('Z', '+00:00'))
        if stamp.tzinfo is None:
            raise ValueError('Missing timestamp timezone')
        records.append(dict(date=day, serviceId=row['service_id'], service=row['service'] or row['service_id'],
                            currency=row['currency'], gross=float(gross), credits=float(credits),
                            net=float(gross + credits), exportedAt=stamp.astimezone(timezone.utc).isoformat()))
    currencies = {r['currency'] for r in records}
    if len(currencies) > 1:
        raise ValueError('Mixed billing currencies')
    return dict(version=1, projectId=project, fetchedAt=fetched_at, window=window,
                currency=next(iter(currencies), None), records=records,
                latestExportAt=max((r['exportedAt'] for r in records), default=None),
                latestUsageDate=max((r['date'] for r in records), default=None))


def read_costs(table, location='US', session=None, now=None, project=None):
    now = now or datetime.now(timezone.utc)
    project = project or project_id()
    if not project:
        raise ValueError('ASSET_PROJECT_ID is required')
    window = cost_window(now)
    query = cost_query(table)
    if session is None:
        import google.auth
        from google.auth.transport.requests import AuthorizedSession
        credentials, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
        session = AuthorizedSession(credentials)
    # Jobs run (and are billed) in this project; the export table may live elsewhere.
    base = f'https://bigquery.googleapis.com/bigquery/v2/projects/{project}/queries'
    body = dict(query=query, useLegacySql=False, useQueryCache=True, maximumBytesBilled=MAXIMUM_BYTES_BILLED,
                timeoutMs=10000, maxResults=1000, location=location, parameterMode='NAMED',
                queryParameters=[dict(name=k, parameterType={'type': 'STRING'}, parameterValue={'value': v})
                                 for k, v in dict(project=project, **window).items()])
    response = session.post(base, json=body, timeout=30)
    response.raise_for_status()
    page = response.json()
    job, schema, rows = page.get('jobReference'), page.get('schema'), []
    deadline = time.monotonic() + 90
    while True:
        if page.get('errors'):
            raise ValueError('Billing query failed')
        if page.get('jobComplete'):
            schema = page.get('schema') or schema
            for row in page.get('rows', []):
                fields = schema['fields']
                if len(fields) != len(row['f']):
                    raise ValueError('Invalid billing result')
                rows.append({field['name']: value['v'] for field, value in zip(fields, row['f'])})
            if len(rows) > 20000:
                raise ValueError('Billing result too large')
            if not page.get('pageToken'):
                break
        if time.monotonic() >= deadline:
            raise TimeoutError('Billing query timed out')
        if not page.get('jobComplete'):
            time.sleep(.5)
        if not job or not re.fullmatch(r'[A-Za-z0-9_-]+', job.get('jobId', '')):
            raise ValueError('Missing billing job')
        params = dict(location=job.get('location', location), maxResults=1000, timeoutMs=10000)
        if page.get('pageToken'):
            params['pageToken'] = page['pageToken']
        response = session.get(base + '/' + job['jobId'], params=params, timeout=30)
        response.raise_for_status()
        page = response.json()
    return parse_rows(rows, window, now.isoformat(), project)


def cost_document(bucket=None, writable=False):
    if bucket:
        return GCSDocument(bucket, STATE_OBJECT, writable=writable)
    path = Path(os.environ.get('ASSET_COST_LOCAL_PATH', 'data/private/costs.json'))
    return LocalDocument(path if path.is_absolute() else ROOT / path)


def cost_payload(document):
    state, _ = document.read()
    try:
        cap = float(os.environ.get('ASSET_COST_PROJECT_BUDGET', ''))
    except ValueError:
        cap = None
    if cap is not None and (not math.isfinite(cap) or cap <= 0):
        cap = None
    return dict(project=project_id(),
                budget={'currency': os.environ.get('ASSET_COST_CURRENCY', 'JPY'), 'projectBudget': cap},
                snapshot=state.get('snapshot'),
                syncStatus=state.get('syncStatus', {'status': 'not_configured'}))


def synchronize(document, table, read=read_costs, now=None, location='US'):
    now = now or datetime.now(timezone.utc)
    state, generation = document.read()
    previous = state.get('snapshot')
    if table and state.get('syncStatus', {}).get('status') == 'ok' and previous and previous.get('records'):
        age = (now - datetime.fromisoformat(previous['fetchedAt'])).total_seconds()
        if 0 <= age < REFRESH_SECONDS:
            return 'cached'
    status, snapshot = 'not_configured', previous
    if table:
        try:
            snapshot = read(table, location=location, now=now)
            status = 'ok' if snapshot['records'] else 'pending'
        except Exception as exc:
            status = 'pending' if getattr(getattr(exc, 'response', None), 'status_code', None) == 404 else 'error'
    try:
        # One atomic object keeps the status and snapshot consistent. A newer job wins.
        document.write(dict(snapshot=snapshot, syncStatus=dict(status=status, attemptedAt=now.isoformat())), generation)
    except Conflict:
        return 'superseded'
    return status


def main():
    result = synchronize(cost_document(os.environ['ASSET_STATE_BUCKET'], writable=True),
                         os.environ.get('ASSET_COST_BILLING_TABLE', ''),
                         location=os.environ.get('ASSET_COST_BILLING_LOCATION', 'US'))
    print(json.dumps({'costSync': result}), flush=True)
    if result == 'error':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
