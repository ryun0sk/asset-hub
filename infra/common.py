"""Shared config checks, resource names and the gcloud runner for infra scripts."""
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CONFIG = ROOT / 'infra/config.json'
PLACEHOLDER = 'TBD'
REPOSITORY = 'asset-hub'
COST_JOB = 'asset-cost-sync'


def load_config(path=CONFIG):
    return json.loads(Path(path).read_text())


def placeholders(value, where='config'):
    """Every path in the config that still holds the TBD placeholder."""
    if isinstance(value, dict):
        return [p for k, v in value.items() for p in placeholders(v, f'{where}.{k}')]
    if isinstance(value, list):
        return [p for i, v in enumerate(value) for p in placeholders(v, f'{where}[{i}]')]
    return [where] if isinstance(value, str) and value.strip().upper() == PLACEHOLDER else []


def config_problems(config):
    missing = placeholders(config)
    problems = [f'{p} が未設定（TBD）です' for p in missing]
    checks = [('project', r'[a-z][a-z0-9-]{4,28}[a-z0-9]', 'project が不正です'),
              ('project_number', r'[0-9]+', 'project_number は数字で指定してください'),
              ('account', r'[^@\s]+@[^@\s]+', 'account（gcloud のログインアカウント）を指定してください'),
              ('region', r'[a-z]+-[a-z]+[0-9]', 'region が不正です')]
    for key, pattern, message in checks:
        if 'config.' + key not in missing and not re.fullmatch(pattern, str(config.get(key, ''))):
            problems.append(message)
    emails = config.get('allowed_emails')
    if not isinstance(emails, list) or not emails or any(not isinstance(e, str) or '@' not in e or ',' in e for e in emails):
        problems.append('allowed_emails に閲覧を許可するメールアドレスを1件以上指定してください')
    if not re.fullmatch(r'[a-z0-9-]+', str(config.get('service', ''))):
        problems.append('service が不正です')
    from backend.costs import TABLE_PATTERN
    table = config.get('cost_reporting', {}).get('billing_table', '')
    if 'config.cost_reporting.billing_table' not in missing and table and not TABLE_PATTERN.fullmatch(table):
        problems.append('cost_reporting.billing_table は "<project>.<dataset>.<table>" か、未設定なら空文字にしてください')
    return problems


def require_config(config):
    """Refuse to touch the cloud while the config still has placeholders or no viewers."""
    problems = config_problems(config)
    if problems:
        raise SystemExit('infra/config.json を確定させてから実行してください:\n- ' + '\n- '.join(problems))
    return config


def names(config):
    project, region = config['project'], config['region']
    return dict(
        runtime=f'asset-runtime@{project}.iam.gserviceaccount.com',
        builder=f'asset-builder@{project}.iam.gserviceaccount.com',
        cost=f'asset-cost-sync@{project}.iam.gserviceaccount.com',
        scheduler=f'asset-scheduler@{project}.iam.gserviceaccount.com',
        state_bucket=project + '-asset-state',
        builds_bucket=project + '-asset-builds',
        image=f'{region}-docker.pkg.dev/{project}/{REPOSITORY}/app:current',
        iap_agent=f'service-{config["project_number"]}@gcp-sa-iap.iam.gserviceaccount.com',
        audience=f'/projects/{config["project_number"]}/locations/{region}/services/{config["service"]}',
    )


class Gcloud:
    """Pins every call to the configured project and account. dry_run prints instead of running."""
    def __init__(self, config, dry_run=False):
        self.config = config
        self.dry_run = dry_run

    def command(self, *args, read=False):
        return ['gcloud', *args, '--project=' + self.config['project'], '--account=' + self.config['account'],
                '--quiet', *(['--format=json'] if read else [])]

    def run(self, *args, read=False):
        command = self.command(*args, read=read)
        if self.dry_run:
            print(shlex.join(command))
            return [] if read else None
        result = subprocess.run(command, check=True, text=True, stdout=subprocess.PIPE if read else None)
        return json.loads(result.stdout) if read else None

    def succeeds(self, *args):
        """Existence probe; in dry-run nothing exists yet."""
        if self.dry_run:
            return False
        return subprocess.run(self.command(*args), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
