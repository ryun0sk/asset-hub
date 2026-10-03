"""Provision the daily billing read (Cloud Run Job + Cloud Scheduler).

    python3 infra/setup_costs.py            # default: dry-run, prints the plan and gcloud commands
    python3 infra/setup_costs.py --apply    # provisions; refuses while config has TBD values

The dashboard identity never receives BigQuery or billing-account access. Only
the job identity `asset-cost-sync` reads the export dataset, and it can write
only gs://<state bucket>/costs/state.json.
"""
import json
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from infra.common import COST_JOB, PLACEHOLDER, Gcloud, config_problems, load_config, names, require_config  # noqa: E402

DEFAULT_SCHEDULE = '0 1 * * *'
DEFAULT_TIME_ZONE = 'Asia/Tokyo'


def verify_source(session, base, table_id, project, location, allow_pending=False):
    response = session.get(base + '/tables/' + table_id, timeout=30)
    if response.status_code != 404 or not allow_pending:
        response.raise_for_status()
        return
    # Initial export can take hours. Accept only the standard table of this
    # project's live billing account, in a dataset writable by Google's exporter.
    response = session.get('https://cloudbilling.googleapis.com/v1/projects/' + project + '/billingInfo', timeout=30)
    response.raise_for_status()
    billing = response.json()
    account = billing.get('billingAccountName', '').removeprefix('billingAccounts/')
    if not billing.get('billingEnabled') or not account or table_id != 'gcp_billing_export_v1_' + account.replace('-', '_'):
        raise ValueError('Pending export does not match the live billing account')
    response = session.get(base, timeout=30)
    response.raise_for_status()
    dataset = response.json()
    exporter = {'role': 'OWNER', 'userByEmail': 'billing-export-bigquery@system.gserviceaccount.com'}
    if dataset.get('location') != location or exporter not in dataset.get('access', []):
        raise ValueError('Pending export dataset is not ready')
    print('Verified initial billing export; first data is pending.')


def budget_command(config):
    """Budget alerts are created by hand once (re-running would duplicate them)."""
    control = config['cost_control']
    account = control.get('billing_account') or '<BILLING_ACCOUNT_ID>'
    command = ['gcloud', 'billing', 'budgets', 'create', '--billing-account=' + account,
               '--display-name=' + config['service'] + ' monthly',
               f'--budget-amount={control["monthly_project_budget"]}{control["currency"]}',
               '--filter-projects=projects/' + config['project'], '--calendar-period=month']
    command += [f'--threshold-rule=percent={t}' for t in control.get('thresholds', [])]
    return command


def disable_reporting(run, project, region, job, image):
    schedules = run('scheduler', 'jobs', 'list', '--location=' + region, read=True)
    if any(j['name'].endswith('/' + job) and j.get('state') != 'PAUSED' for j in schedules):
        run('scheduler', 'jobs', 'pause', job, '--location=' + region)
    jobs = run('run', 'jobs', 'list', '--region=' + region, read=True)
    if any(j['metadata']['name'] == job for j in jobs):
        # Clear the source so manual execution cannot continue old billing reads.
        run('run', 'jobs', 'update', job, '--region=' + region, '--image=' + image,
            '--remove-env-vars=ASSET_COST_BILLING_TABLE')
        run('run', 'jobs', 'execute', job, '--region=' + region, '--wait')


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    apply = '--apply' in argv
    if apply and '--dry-run' in argv:
        raise SystemExit('--apply と --dry-run は同時に指定できません')
    config = load_config()
    if apply:
        require_config(config)
    else:
        for problem in config_problems(config):
            print('# 注意: ' + problem)
    cost = config.get('cost_reporting', {})
    table = cost.get('billing_table', '')
    location = cost.get('location', 'US')
    schedule = cost.get('schedule', DEFAULT_SCHEDULE)
    time_zone = cost.get('time_zone', DEFAULT_TIME_ZONE)
    project, region = config['project'], config['region']
    n = names(config)
    gcloud = Gcloud(config, dry_run=not apply)
    run = gcloud.run

    if not table:
        print('# Cost export is not configured; pause existing reads and show setup pending.')
        disable_reporting(run, project, region, COST_JOB, n['image'])
        return
    if table != PLACEHOLDER:
        from backend.costs import cost_query
        cost_query(table)
        dataset_project, dataset, table_id = table.split('.')
    else:
        dataset_project, dataset, table_id = '<billing-project>', '<dataset>', '<table>'
    print('# ' + json.dumps({'project': project, 'table': table, 'schedule': schedule, 'timeZone': time_zone,
                             'reader': n['cost'], 'maximumBytesBilled': 100000000, 'apply': apply}))

    base = f'https://bigquery.googleapis.com/bigquery/v2/projects/{dataset_project}/datasets/{dataset}'
    session = None
    if apply:
        # Verify the source before granting access, including explicitly enabled initial exports.
        import requests
        token = subprocess.check_output(['gcloud', 'auth', 'print-access-token', '--account=' + config['account']], text=True).strip()
        session = requests.Session()
        session.headers['Authorization'] = 'Bearer ' + token
        verify_source(session, base, table_id, project, location, allow_pending=cost.get('allow_pending_export') is True)
    else:
        print(f'# verify table {table} exists (REST GET {base}/tables/{table_id})')

    run('services', 'enable', 'bigquery.googleapis.com', 'cloudscheduler.googleapis.com', 'run.googleapis.com')
    if not gcloud.succeeds('iam', 'service-accounts', 'describe', n['cost']):
        run('iam', 'service-accounts', 'create', 'asset-cost-sync', '--display-name=Asset Hub daily cost reader')
    run('projects', 'add-iam-policy-binding', project, '--member=serviceAccount:' + n['cost'],
        '--role=roles/bigquery.jobUser', '--condition=None')
    grant = {'role': 'READER', 'userByEmail': n['cost']}
    if apply:
        response = session.get(base, timeout=30)
        response.raise_for_status()
        metadata = response.json()
        access = metadata.get('access', [])
        if grant not in access:
            response = session.patch(base, json={'access': access + [grant]},
                                     headers={'If-Match': metadata['etag']}, timeout=30)
            response.raise_for_status()
    else:
        print(f'# grant dataset READER to {n["cost"]} (REST PATCH {base} access += {json.dumps(grant)})')
    bucket = n['state_bucket']
    run('storage', 'buckets', 'add-iam-policy-binding', 'gs://' + bucket,
        '--member=serviceAccount:' + n['cost'], '--role=roles/storage.objectAdmin',
        "--condition=title=asset-cost-snapshot,expression=resource.name == 'projects/_/buckets/" + bucket + "/objects/costs/state.json'")
    with tempfile.TemporaryDirectory() as directory:
        env = Path(directory) / 'env.json'
        env.write_text(json.dumps({'ASSET_STATE_BUCKET': bucket, 'ASSET_PROJECT_ID': project,
                                   'ASSET_COST_BILLING_TABLE': table, 'ASSET_COST_BILLING_LOCATION': location}))
        run('run', 'jobs', 'deploy', COST_JOB, '--region=' + region, '--image=' + n['image'],
            '--service-account=' + n['cost'], '--command=python', '--args=-m,backend.costs',
            '--tasks=1', '--parallelism=1', '--max-retries=1', '--task-timeout=300s',
            '--cpu=1', '--memory=512Mi', '--env-vars-file=' + str(env))
    run('run', 'jobs', 'add-iam-policy-binding', COST_JOB, '--region=' + region,
        '--member=serviceAccount:' + n['scheduler'], '--role=roles/run.invoker')
    jobs = run('scheduler', 'jobs', 'list', '--location=' + region, read=True)
    existing = any(j['name'].endswith('/' + COST_JOB) for j in jobs)
    run('scheduler', 'jobs', 'update' if existing else 'create', 'http', COST_JOB,
        '--location=' + region, '--schedule=' + schedule, '--time-zone=' + time_zone,
        '--uri=' + f'https://run.googleapis.com/v2/projects/{project}/locations/{region}/jobs/{COST_JOB}:run',
        '--http-method=POST', '--oauth-service-account-email=' + n['scheduler'],
        '--oauth-token-scope=https://www.googleapis.com/auth/cloud-platform',
        ('--update-headers=' if existing else '--headers=') + 'Content-Type=application/json',
        '--message-body={}', '--attempt-deadline=180s', '--max-retry-attempts=1')
    if any(j['name'].endswith('/' + COST_JOB) and j.get('state') == 'PAUSED' for j in jobs):
        run('scheduler', 'jobs', 'resume', COST_JOB, '--location=' + region)
    run('run', 'jobs', 'execute', COST_JOB, '--region=' + region, '--wait')
    print('# 予算アラートは初回のみ手動で作成します（再実行すると重複します）:')
    print('# ' + shlex.join(budget_command(config)))


if __name__ == '__main__':
    main()
