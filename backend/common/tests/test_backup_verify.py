"""deploy/verify_backup.sh sırtqı nusqa haqıyqatında tiklenetuǵının dálillaydı: restic repository di tekseredi, eń jańa nusqa
waqtınsha papkaǵa tiklenedi, súwret arxivi jaramlı gzip fayl hám PostgreSQL dump tı oqıy aladı.

Jalǵan `restic` (ol eki fayldı "tikleydi") hám jalǵan `docker` (pg_restore --list ornında) ǵa qarsı isleydi.
"""
import gzip
import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
FAKE_RESTIC = """#!/bin/sh
echo "restic $*" >> "$FAKE_LOG"
[ -n "$FAKE_CHECK_FAIL" ] && [ "$1" = check ] && { echo "restic: repository is damaged" >&2; exit 1; }
if [ "$1" = restore ]; then
  while [ "$#" -gt 0 ]; do [ "$1" = --target ] && target="$2"; shift; done
  mkdir -p "$target/backups"
  [ -z "$FAKE_NOTHING" ] && printf 'PGDMP-fake-dump' > "$target/backups/db-20261112-030000.dump"
  [ -z "$FAKE_NOTHING" ] && cp "$FAKE_MEDIA" "$target/backups/media-20261112-030000.tar.gz"
fi
exit 0
"""
FAKE_DOCKER = """#!/bin/sh
echo "docker $*" >> "$FAKE_LOG"
cat > /dev/null
[ -n "$FAKE_PGR_FAIL" ] && { echo "pg_restore: not a valid archive" >&2; exit 1; }
exit 0
"""
OFFSITE = 'RESTIC_REPOSITORY=s3:s3.eu-west-1.amazonaws.com/tickbron-backups-test\nRESTIC_PASSWORD=very-secret-repository-password\n'


def executable(path, text):
    path.write_text(text)
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


@pytest.fixture
def server(tmp_path):
    (tmp_path / 'deploy').mkdir()
    shutil.copy(REPO / 'deploy' / 'verify_backup.sh', tmp_path / 'deploy' / 'verify_backup.sh')
    (tmp_path / 'bin').mkdir()
    executable(tmp_path / 'bin' / 'restic', FAKE_RESTIC)
    executable(tmp_path / 'bin' / 'docker', FAKE_DOCKER)
    good = tmp_path / 'media.tar.gz'
    good.write_bytes(gzip.compress(b'fake-tar-stream'))
    (tmp_path / 'deploy' / 'offsite.env').write_text(OFFSITE)
    (tmp_path / 'deploy' / 'offsite.env').chmod(0o600)
    return tmp_path


def run(server, **env):
    environment = {**os.environ, 'PATH': f'{server / "bin"}:{os.environ["PATH"]}', 'FAKE_LOG': str(server / 'log.txt'),
                   'FAKE_MEDIA': str(server / 'media.tar.gz'), **env}
    return subprocess.run(['sh', str(server / 'deploy' / 'verify_backup.sh')], capture_output=True, text=True, env=environment)


def test_a_good_copy_is_checked_restored_and_read(server):
    result = run(server)

    assert result.returncode == 0, result.stderr
    log = (server / 'log.txt').read_text()
    assert log.index('restic check') < log.index('restic restore latest --tag tickbron')
    assert 'docker compose exec -T db pg_restore --list' in log
    assert 'Offsite backup verified' in result.stdout


def test_without_the_offsite_file_it_says_so(server):
    (server / 'deploy' / 'offsite.env').unlink()

    result = run(server)

    assert result.returncode != 0
    assert 'offsite.env' in result.stderr


def test_a_damaged_repository_fails(server):
    result = run(server, FAKE_CHECK_FAIL='1')

    assert result.returncode != 0
    assert 'verified' not in result.stdout


def test_an_empty_restore_fails(server):
    result = run(server, FAKE_NOTHING='1')

    assert result.returncode != 0
    assert 'verified' not in result.stdout


def test_a_photo_archive_that_is_not_gzip_fails(server):
    (server / 'media.tar.gz').write_bytes(b'not a gzip file')

    result = run(server)

    assert result.returncode != 0
    assert 'verified' not in result.stdout


def test_a_dump_that_postgres_cannot_read_fails(server):
    result = run(server, FAKE_PGR_FAIL='1')

    assert result.returncode != 0
    assert 'verified' not in result.stdout


def test_the_temporary_restore_folder_is_removed_and_no_secret_is_printed(server):
    scratch = server / 'scratch'
    scratch.mkdir()

    result = run(server, TMPDIR=str(scratch))

    assert result.returncode == 0, result.stderr
    assert 'very-secret-repository-password' not in result.stdout + result.stderr
    assert list(scratch.iterdir()) == []


def test_a_settings_file_that_others_can_read_is_refused_and_never_run(server):
    # offsite.env shell retinde isletiledi: basqa paydalanıwshı jaza alsa, ol serverde komanda isletedi
    env = server / 'deploy' / 'offsite.env'
    env.write_text(OFFSITE + 'touch "$PWD/pwned"' + chr(10))
    env.chmod(0o666)

    result = run(server)

    assert result.returncode != 0
    assert 'chmod 600' in result.stderr
    assert not (server / 'pwned').exists()
    assert not (server / 'log.txt').exists()


def test_a_good_run_reminds_that_the_env_file_is_not_in_the_backup(server):
    # .env (SECRET_KEY, TWO_FACTOR_KEY) nusqada joq: onsız dump tiklense de 2FA kilt'leri oqılmaydı
    result = run(server)

    assert result.returncode == 0, result.stderr
    assert '.env' in result.stdout
    assert 'TWO_FACTOR_KEY' in result.stdout
