"""deploy/backup.sh must fail loudly and leave no half-written file when the database or the photos cannot be saved.

It runs under /bin/sh (dash on Ubuntu, which has no `pipefail`), against a fake `docker` that succeeds or fails on demand.
"""
import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
FAKE_DOCKER = """#!/bin/sh
case "$*" in
  *"exec -T db"*)  [ -n "$FAKE_DB_FAIL" ] && { echo "pg_dump: connection refused" >&2; exit 1; }; printf 'PGDMP-fake-dump' ;;
  *"cp web:/app/media -"*) [ -n "$FAKE_CP_FAIL" ] && { echo "no such container" >&2; exit 1; }; printf 'fake-tar-stream' ;;
  *) exit 2 ;;
esac
"""


@pytest.fixture
def server(tmp_path):
    """A copy of the repo layout the script expects (deploy/backup.sh one level below the project root) and a fake docker."""
    (tmp_path / 'deploy').mkdir()
    shutil.copy(REPO / 'deploy' / 'backup.sh', tmp_path / 'deploy' / 'backup.sh')
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    docker = bin_dir / 'docker'
    docker.write_text(FAKE_DOCKER)
    docker.chmod(docker.stat().st_mode | stat.S_IEXEC)
    return tmp_path


def run(server, **env):
    environment = {**os.environ, 'PATH': f'{server / "bin"}:{os.environ["PATH"]}', **env}
    return subprocess.run(['sh', str(server / 'deploy' / 'backup.sh')], capture_output=True, text=True, env=environment)


def backups(server):
    folder = server / 'backups'
    return sorted(path.name for path in folder.iterdir()) if folder.exists() else []


def test_a_good_run_leaves_a_database_dump_and_a_photo_archive(server):
    result = run(server)

    assert result.returncode == 0, result.stderr
    names = backups(server)
    assert len(names) == 2
    assert any(name.startswith('db-') and name.endswith('.dump') for name in names)
    assert any(name.startswith('media-') and name.endswith('.tar.gz') for name in names)
    assert 'Backup done' in result.stdout


def test_the_photo_archive_is_a_real_gzip_file(server):
    run(server)
    archive = next((server / 'backups').glob('media-*.tar.gz'))

    assert subprocess.run(['gzip', '-t', str(archive)]).returncode == 0
    assert subprocess.run(['gzip', '-dc', str(archive)], capture_output=True).stdout == b'fake-tar-stream'


def test_when_copying_the_photos_fails_the_run_fails_and_keeps_nothing(server):
    result = run(server, FAKE_CP_FAIL='1')

    assert result.returncode != 0
    assert 'Backup done' not in result.stdout
    assert backups(server) == []


def test_when_the_database_dump_fails_the_run_fails_and_keeps_nothing(server):
    result = run(server, FAKE_DB_FAIL='1')

    assert result.returncode != 0
    assert 'Backup done' not in result.stdout
    assert backups(server) == []


def test_the_backup_files_can_only_be_read_by_their_owner(server):
    # a database dump holds personal data
    run(server)

    for path in (server / 'backups').iterdir():
        assert stat.S_IMODE(path.stat().st_mode) & 0o077 == 0, path.name


def test_a_failed_run_does_not_delete_the_older_good_backups(server):
    (server / 'backups').mkdir()
    old = server / 'backups' / 'db-20200101-000000.dump'
    old.write_text('old')
    os.utime(old, (1, 1))

    run(server, FAKE_CP_FAIL='1')

    assert old.exists()
