"""Deploy only the configured project; stage an explicit source allowlist.

    python3 infra/deploy.py bootstrap   # one-time: APIs, service accounts, buckets, registry
    python3 infra/deploy.py deploy      # build, cost job, private Cloud Run service behind IAP
    python3 infra/deploy.py verify      # IAP on, viewers == allowed_emails, no public invoker

Options for deploy: --existing-image (skip the build), --skip-costs (do not run setup_costs).
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from infra.common import ROOT, REPOSITORY, Gcloud, load_config, names, require_config  # noqa: E402
from backend.paths import SHELL_TYPES, extension, research_files  # noqa: E402

BUILD_FILES = ['Dockerfile', 'requirements.txt', '.dockerignore']
SERVICES = ['run.googleapis.com', 'artifactregistry.googleapis.com', 'cloudbuild.googleapis.com',
            'iap.googleapis.com', 'storage.googleapis.com', 'iam.googleapis.com',
            'cloudresourcemanager.googleapis.com']


def stage(root, destination):
    """Copy only what the image may contain; returns the staged relative paths."""
    root, destination = Path(root), Path(destination)
    staged = []
    def copy(relative):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / relative, target)
        staged.append(relative)
    for source in sorted((root / 'backend').glob('*.py')):
        copy(f'backend/{source.name}')
    for source in sorted((root / 'web').iterdir()):
        if source.is_file() and not source.is_symlink() and not source.name.startswith('.') and extension(source.name) in SHELL_TYPES:
            copy(f'web/{source.name}')
    for relative in research_files(root / 'research'):
        copy(f'research/{relative}')
    for name in BUILD_FILES:
        copy(name)
    return staged


def bootstrap(config, gcloud):
    n = names(config)
    gcloud.run('services', 'enable', *SERVICES)
    for account in ['asset-runtime', 'asset-builder', 'asset-scheduler']:
        if not gcloud.succeeds('iam', 'service-accounts', 'describe', f'{account}@{config["project"]}.iam.gserviceaccount.com'):
            gcloud.run('iam', 'service-accounts', 'create', account, '--display-name=' + account)
    for bucket in [n['state_bucket'], n['builds_bucket']]:
        if not gcloud.succeeds('storage', 'buckets', 'describe', 'gs://' + bucket):
            gcloud.run('storage', 'buckets', 'create', 'gs://' + bucket, '--location=' + config['region'],
                       '--uniform-bucket-level-access', '--public-access-prevention')
    # The dashboard only reads costs/state.json; only the cost job writes it (setup_costs.py).
    gcloud.run('storage', 'buckets', 'add-iam-policy-binding', 'gs://' + n['state_bucket'],
               '--member=serviceAccount:' + n['runtime'], '--role=roles/storage.objectViewer')
    gcloud.run('storage', 'buckets', 'add-iam-policy-binding', 'gs://' + n['builds_bucket'],
               '--member=serviceAccount:' + n['builder'], '--role=roles/storage.objectViewer')
    if not gcloud.succeeds('artifacts', 'repositories', 'describe', REPOSITORY, '--location=' + config['region']):
        gcloud.run('artifacts', 'repositories', 'create', REPOSITORY, '--repository-format=docker', '--location=' + config['region'])
    gcloud.run('artifacts', 'repositories', 'add-iam-policy-binding', REPOSITORY, '--location=' + config['region'],
               '--member=serviceAccount:' + n['builder'], '--role=roles/artifactregistry.writer')
    gcloud.run('projects', 'add-iam-policy-binding', config['project'], '--member=serviceAccount:' + n['builder'],
               '--role=roles/logging.logWriter', '--condition=None')
    gcloud.run('beta', 'services', 'identity', 'create', '--service=iap.googleapis.com')


def service_env(config):
    n = names(config)
    control = config['cost_control']
    return {'ASSET_IAP_AUDIENCE': n['audience'], 'ASSET_ALLOWED_EMAILS': ','.join(config['allowed_emails']),
            'ASSET_STATE_BUCKET': n['state_bucket'], 'ASSET_PROJECT_ID': config['project'],
            'ASSET_COST_CURRENCY': control['currency'], 'ASSET_COST_PROJECT_BUDGET': str(control['monthly_project_budget'])}


def deploy_args(config, envfile):
    n = names(config)
    return ['run', 'deploy', config['service'], '--image=' + n['image'], '--region=' + config['region'],
            '--service-account=' + n['runtime'], '--no-allow-unauthenticated', '--iap', '--ingress=all',
            '--cpu=1', '--memory=256Mi', '--min=0', '--max=1', '--max-instances=1', '--concurrency=20',
            '--timeout=60', '--cpu-throttling', '--no-cpu-boost', '--port=8080', '--env-vars-file=' + str(envfile)]


def iap_policy(config):
    return {'bindings': [{'role': 'roles/iap.httpsResourceAccessor',
                          'members': ['user:' + e for e in config['allowed_emails']]}]}


def deploy(config, gcloud, argv):
    n = names(config)
    with tempfile.TemporaryDirectory(prefix='asset-build-') as temp:
        source = Path(temp) / 'source'
        source.mkdir()
        staged = stage(ROOT, source)
        print(f'staged {len(staged)} files', flush=True)
        build = {'steps': [{'name': 'gcr.io/cloud-builders/docker', 'args': ['build', '-t', n['image'], '.']}],
                 'images': [n['image']],
                 'serviceAccount': f'projects/{config["project"]}/serviceAccounts/{n["builder"]}',
                 'options': {'logging': 'CLOUD_LOGGING_ONLY'}}
        buildfile = Path(temp) / 'build.json'
        buildfile.write_text(json.dumps(build))
        if '--existing-image' not in argv:
            gcloud.run('builds', 'submit', str(source), '--config=' + str(buildfile), '--region=' + config['region'],
                       '--gcs-source-staging-dir=gs://' + n['builds_bucket'] + '/source')
        if '--skip-costs' not in argv:
            from infra import setup_costs
            setup_costs.main(['--apply'])
        envfile = Path(temp) / 'env.json'
        envfile.write_text(json.dumps(service_env(config)))
        gcloud.run(*deploy_args(config, envfile))
        gcloud.run('run', 'services', 'add-iam-policy-binding', config['service'], '--region=' + config['region'],
                   '--member=serviceAccount:' + n['iap_agent'], '--role=roles/run.invoker')
        policyfile = Path(temp) / 'iap.json'
        policyfile.write_text(json.dumps(iap_policy(config)))
        gcloud.run('iap', 'web', 'set-iam-policy', str(policyfile), '--resource-type=cloud-run',
                   '--service=' + config['service'], '--region=' + config['region'])


def verify(config, gcloud):
    region = config['region']
    service = gcloud.run('run', 'services', 'describe', config['service'], '--region=' + region, read=True)
    assert service['metadata']['annotations'].get('run.googleapis.com/iap-enabled') == 'true', 'IAP is not enabled'
    policy = gcloud.run('iap', 'web', 'get-iam-policy', '--resource-type=cloud-run', '--service=' + config['service'],
                        '--region=' + region, read=True)
    viewers = {m for b in policy.get('bindings', []) if b['role'] == 'roles/iap.httpsResourceAccessor' for m in b['members']}
    assert viewers == {'user:' + e for e in config['allowed_emails']}, 'IAP viewers differ from allowed_emails'
    invoker = gcloud.run('run', 'services', 'get-iam-policy', config['service'], '--region=' + region, read=True)
    public = [m for b in invoker.get('bindings', []) for m in b['members'] if m in ('allUsers', 'allAuthenticatedUsers')]
    assert not public, 'Service is publicly invokable'
    print(json.dumps({'url': service['status']['url'], 'iap': True, 'viewers': len(config['allowed_emails'])}))


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    command = argv[0] if argv else ''
    if command not in ('bootstrap', 'deploy', 'verify'):
        raise SystemExit('usage: python3 infra/deploy.py bootstrap | deploy [--existing-image] [--skip-costs] | verify')
    config = require_config(load_config())
    gcloud = Gcloud(config)
    if command == 'bootstrap':
        bootstrap(config, gcloud)
    elif command == 'deploy':
        deploy(config, gcloud, argv[1:])
    else:
        verify(config, gcloud)


if __name__ == '__main__':
    main()
