"""
The Docker files (docker-compose.yml, the two Dockerfiles, the Caddyfile and the env example) stay usable:
the right services, nothing but the web server open to the internet, no secret inside an image or a file
in git, and every variable the compose file reads is in the env example the owner fills in.
"""
import re
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[3]
COMPOSE = REPO / 'docker-compose.yml'
ENV_EXAMPLE = REPO / 'deploy' / 'docker.env.example'


@pytest.fixture(scope='module')
def compose():
    return yaml.safe_load(COMPOSE.read_text())


def env_keys(path):
    return {line.split('=', 1)[0].strip() for line in path.read_text().splitlines()
            if line.strip() and not line.lstrip().startswith('#') and '=' in line}


class TestCompose:
    def test_has_every_service(self, compose):
        assert set(compose['services']) == {'db', 'redis', 'migrate', 'web', 'worker', 'beat', 'caddy'}

    def test_only_the_web_server_is_open_to_the_internet(self, compose):
        published = {name for name, service in compose['services'].items() if service.get('ports')}
        assert published == {'caddy'}

    def test_database_changes_run_before_the_app_starts(self, compose):
        assert compose['services']['migrate']['command'][-2:] == ['migrate', '--noinput']
        for name in ('web', 'worker', 'beat'):
            assert compose['services'][name]['depends_on']['migrate']['condition'] == 'service_completed_successfully'

    def test_beat_runs_once_and_the_worker_with_the_same_app(self, compose):
        assert 'replicas' not in compose['services']['beat'].get('deploy', {})
        assert 'beat' in ' '.join(compose['services']['beat']['command'])
        assert 'worker' in ' '.join(compose['services']['worker']['command'])

    def test_data_lives_in_named_volumes(self, compose):
        assert {'pgdata', 'media', 'caddy_data'} <= set(compose['volumes'])
        assert any('pgdata' in str(volume) for volume in compose['services']['db']['volumes'])
        assert any('media' in str(volume) for volume in compose['services']['web']['volumes'])

    def test_secrets_come_from_the_env_file_not_from_the_compose_file(self, compose):
        for name in ('web', 'worker', 'beat', 'migrate'):
            assert '.env' in str(compose['services'][name]['env_file'])
        text = COMPOSE.read_text()
        assert not re.search(r'(PASSWORD|SECRET_KEY)\s*[:=]\s*[^$\s]', text)

    def test_the_health_check_looks_like_a_request_from_the_proxy(self, compose):
        # Without these two the app answers 400 (host not allowed) or 301 (to https) and never looks healthy
        check = ' '.join(compose['services']['web']['healthcheck']['test'])
        assert "'Host': os.environ['DOMAIN']" in check
        assert "'X-Forwarded-Proto': 'https'" in check

    def test_every_service_restarts_by_itself(self, compose):
        for name, service in compose['services'].items():
            if name != 'migrate':
                assert service['restart'] == 'unless-stopped', name

    def test_every_variable_the_compose_file_reads_is_in_the_env_example(self):
        # ${NAME} without a default; `$${NAME}` is the container's own variable and ${NAME:-x} has a default
        used = set(re.findall(r'(?<!\$)\$\{([A-Z_]+)\}', COMPOSE.read_text()))
        assert used, 'the compose file reads no variable'
        assert used <= env_keys(ENV_EXAMPLE), sorted(used - env_keys(ENV_EXAMPLE))


class TestImages:
    def test_backend_runs_gunicorn_as_a_normal_user(self):
        text = (REPO / 'backend' / 'Dockerfile').read_text()
        assert re.search(r'^USER (?!root)\w+', text, flags=re.M)
        assert 'gunicorn' in text
        assert 'config.wsgi:application' in text

    def test_gunicorn_is_a_pinned_requirement(self):
        assert re.search(r'^gunicorn==\d', (REPO / 'backend' / 'requirements.txt').read_text(), flags=re.M)

    @pytest.mark.parametrize('folder', ['backend', 'frontend'])
    def test_secrets_and_data_stay_out_of_the_images(self, folder):
        ignored = (REPO / folder / '.dockerignore').read_text().split()
        assert '.env' in ignored or '.env*' in ignored
        assert 'node_modules' in ignored if folder == 'frontend' else 'media' in ignored

    def test_frontend_image_is_built_for_the_real_address(self):
        text = (REPO / 'frontend' / 'Dockerfile').read_text()
        assert 'ARG VITE_API_BASE_URL' in text
        assert 'caddy' in text

    def test_env_files_are_not_in_git(self):
        ignored = (REPO / '.gitignore').read_text().split()
        assert '.env' in ignored


class TestEnvExample:
    def test_has_no_real_secrets(self):
        text = ENV_EXAMPLE.read_text()
        for line in text.splitlines():
            if re.match(r'(SECRET_KEY|DB_PASSWORD|EMAIL_HOST_PASSWORD)=', line):
                assert 'CHANGE_ME' in line or line.endswith('='), line

    def test_points_the_app_at_the_other_containers(self):
        text = ENV_EXAMPLE.read_text()
        assert 'DB_HOST=db' in text
        assert 'REDIS_HOST=redis' in text
        assert 'CELERY_BROKER_URL=redis://redis:6379/0' in text
